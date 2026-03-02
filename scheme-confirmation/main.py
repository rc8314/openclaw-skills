#!/usr/bin/env python3
"""
Scheme Confirmation Skill - 方案确认与追踪

功能：
1. 自动识别对话中的方案/建议
2. 管理方案的生命周期（提出→确认→执行→完成）
3. 提醒用户确认和执行方案
4. 追踪方案执行状态
"""

import json
import os
import time
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict, field
from pathlib import Path
from enum import Enum


class SchemeStatus(Enum):
    """方案状态枚举"""
    PROPOSED = "proposed"       # 已提出，待确认
    CONFIRMED = "confirmed"     # 已确认，待执行
    IN_PROGRESS = "in_progress" # 执行中
    COMPLETED = "completed"     # 已完成
    CANCELLED = "cancelled"     # 已取消
    EXPIRED = "expired"         # 已过期


@dataclass
class Scheme:
    """方案数据结构"""
    id: str
    title: str
    description: str
    status: str
    created_at: float
    updated_at: float
    session_key: str
    proposed_by: str  # 'ai' 或 'user'
    
    # 确认相关
    confirmation_requested_at: Optional[float] = None
    confirmed_at: Optional[float] = None
    confirmed_by: Optional[str] = None  # 确认者标识
    
    # 执行相关
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    # 提醒相关
    last_reminded_at: Optional[float] = None
    reminder_count: int = 0
    
    # 元数据
    tags: List[str] = field(default_factory=list)
    priority: str = "normal"  # low, normal, high, urgent
    due_date: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Scheme':
        return cls(**data)
    
    def is_expired(self, timeout: int = 3600) -> bool:
        """检查是否过期（基于确认超时）"""
        if self.status == SchemeStatus.PROPOSED.value:
            if self.confirmation_requested_at:
                return time.time() - self.confirmation_requested_at > timeout
        return False
    
    def should_remind(self, interval: int = 7200) -> bool:
        """检查是否应该提醒"""
        if self.status not in [SchemeStatus.PROPOSED.value, SchemeStatus.CONFIRMED.value]:
            return False
        
        if not self.last_reminded_at:
            return True
        
        return time.time() - self.last_reminded_at >= interval
    
    def get_status_display(self) -> str:
        """获取状态显示文本"""
        status_map = {
            SchemeStatus.PROPOSED.value: "⏳ 待确认",
            SchemeStatus.CONFIRMED.value: "✅ 已确认",
            SchemeStatus.IN_PROGRESS.value: "🔄 执行中",
            SchemeStatus.COMPLETED.value: "✨ 已完成",
            SchemeStatus.CANCELLED.value: "❌ 已取消",
            SchemeStatus.EXPIRED.value: "⌛ 已过期",
        }
        return status_map.get(self.status, self.status)


class SchemeStore:
    """方案存储管理器"""
    
    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir is None:
            storage_dir = os.path.expanduser("~/.openclaw/skills/scheme-confirmation")
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.schemes_file = self.storage_dir / "schemes.json"
        self._schemes: Dict[str, Scheme] = {}
        self._load()
    
    def _load(self):
        """加载方案数据"""
        if self.schemes_file.exists():
            try:
                with open(self.schemes_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for scheme_id, scheme_data in data.items():
                        self._schemes[scheme_id] = Scheme.from_dict(scheme_data)
            except Exception as e:
                print(f"[SchemeStore] 加载失败: {e}")
                self._schemes = {}
    
    def _save(self):
        """保存方案数据"""
        try:
            data = {k: v.to_dict() for k, v in self._schemes.items()}
            with open(self.schemes_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[SchemeStore] 保存失败: {e}")
    
    def add(self, scheme: Scheme) -> bool:
        """添加方案"""
        self._schemes[scheme.id] = scheme
        self._save()
        return True
    
    def get(self, scheme_id: str) -> Optional[Scheme]:
        """获取方案"""
        return self._schemes.get(scheme_id)
    
    def get_by_status(self, status: str) -> List[Scheme]:
        """按状态获取方案"""
        return [s for s in self._schemes.values() if s.status == status]
    
    def get_active(self) -> List[Scheme]:
        """获取活跃方案（非完成/取消）"""
        active_statuses = [
            SchemeStatus.PROPOSED.value,
            SchemeStatus.CONFIRMED.value,
            SchemeStatus.IN_PROGRESS.value
        ]
        return [s for s in self._schemes.values() if s.status in active_statuses]
    
    def update(self, scheme_id: str, **kwargs) -> bool:
        """更新方案"""
        if scheme_id not in self._schemes:
            return False
        
        scheme = self._schemes[scheme_id]
        for key, value in kwargs.items():
            if hasattr(scheme, key):
                setattr(scheme, key, value)
        
        scheme.updated_at = time.time()
        self._save()
        return True
    
    def update_status(self, scheme_id: str, new_status: str) -> bool:
        """更新方案状态"""
        if scheme_id not in self._schemes:
            return False
        
        scheme = self._schemes[scheme_id]
        old_status = scheme.status
        scheme.status = new_status
        scheme.updated_at = time.time()
        
        # 更新时间戳
        now = time.time()
        if new_status == SchemeStatus.CONFIRMED.value and old_status == SchemeStatus.PROPOSED.value:
            scheme.confirmed_at = now
        elif new_status == SchemeStatus.IN_PROGRESS.value:
            scheme.started_at = now
        elif new_status == SchemeStatus.COMPLETED.value:
            scheme.completed_at = now
        
        self._save()
        return True
    
    def delete(self, scheme_id: str) -> bool:
        """删除方案"""
        if scheme_id in self._schemes:
            del self._schemes[scheme_id]
            self._save()
            return True
        return False
    
    def get_pending_confirmation(self) -> List[Scheme]:
        """获取待确认方案"""
        return self.get_by_status(SchemeStatus.PROPOSED.value)
    
    def get_pending_execution(self) -> List[Scheme]:
        """获取待执行方案"""
        return self.get_by_status(SchemeStatus.CONFIRMED.value)
    
    def cleanup_expired(self, timeout: int = 3600) -> int:
        """清理过期方案"""
        expired = []
        for scheme_id, scheme in self._schemes.items():
            if scheme.is_expired(timeout):
                scheme.status = SchemeStatus.EXPIRED.value
                expired.append(scheme_id)
        
        if expired:
            self._save()
        return len(expired)


class SchemeDetector:
    """方案检测器 - 从对话中识别方案"""
    
    # 方案关键词模式
    SCHEME_PATTERNS = [
        r'(?:建议|方案|计划|提议).{0,20}(?:：|:)',
        r'(?:可以|应该|需要).{0,10}(?:尝试|考虑|采用|实施)',
        r'(?:第一步|首先|然后|接着|最后).{0,30}',
        r'(?:方案|计划).{0,5}(?:A|B|C|一|二|三)',
        r'(?:分|拆).{0,5}(?:几步|几个阶段|几个步骤)',
    ]
    
    # 方案类型关键词
    SCHEME_TYPES = {
        'implementation': ['实施', '执行', '落地', '推进', '开展'],
        'decision': ['决定', '选择', '确定', '采纳'],
        'plan': ['计划', '安排', '规划', '时间表'],
        'solution': ['方案', '解决办法', '对策', '措施'],
    }
    
    def __init__(self):
        self.patterns = [re.compile(p, re.IGNORECASE) for p in self.SCHEME_PATTERNS]
    
    def detect(self, message: str) -> Optional[Dict[str, Any]]:
        """
        检测消息中是否包含方案
        
        Returns:
            方案信息字典或 None
        """
        # 检查是否匹配方案模式
        is_scheme = False
        for pattern in self.patterns:
            if pattern.search(message):
                is_scheme = True
                break
        
        # 检查是否包含方案类型关键词
        scheme_type = None
        message_lower = message.lower()
        for stype, keywords in self.SCHEME_TYPES.items():
            if any(kw in message_lower for kw in keywords):
                scheme_type = stype
                is_scheme = True
                break
        
        if not is_scheme:
            return None
        
        # 提取标题
        title = self._extract_title(message)
        
        # 提取描述
        description = self._extract_description(message)
        
        return {
            'title': title,
            'description': description,
            'type': scheme_type or 'general',
            'confidence': 'high' if scheme_type else 'medium'
        }
    
    def _extract_title(self, message: str) -> str:
        """提取方案标题"""
        lines = message.split('\n')
        
        # 优先找包含"方案"、"建议"的行
        for line in lines[:3]:  # 只看前3行
            line = line.strip()
            if any(kw in line for kw in ['方案', '建议', '计划']):
                # 清理标点
                title = re.sub(r'[：:\-–—]', '', line).strip()
                if len(title) > 5:
                    return title[:50]
        
        #  fallback: 取第一行
        first_line = lines[0].strip()
        if len(first_line) > 10:
            return first_line[:50]
        
        return "未命名方案"
    
    def _extract_description(self, message: str) -> str:
        """提取方案描述"""
        # 取前200字符作为描述
        desc = message.replace('\n', ' ')[:200]
        if len(message) > 200:
            desc += "..."
        return desc


class SchemeConfirmation:
    """方案确认主类"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.store = SchemeStore()
        self.detector = SchemeDetector()
        
        self.confirmation_timeout = self.config.get('confirmation_timeout', 3600)
        self.reminder_interval = self.config.get('reminder_interval', 7200)
        self.auto_detect = self.config.get('auto_detect', True)
        self.max_active_schemes = self.config.get('max_active_schemes', 20)
    
    def on_message(self, session_key: str, message: str, sender: str = "user") -> Optional[str]:
        """
        处理消息，检测方案或处理确认
        
        Args:
            session_key: 会话标识
            message: 消息内容
            sender: 发送者 ('user' 或 'ai')
        
        Returns:
            响应消息或 None
        """
        # 1. 检查是否是确认/拒绝指令
        confirmation_result = self._handle_confirmation(message)
        if confirmation_result:
            return confirmation_result
        
        # 2. 检查是否是状态查询
        if self._is_status_query(message):
            return self._get_status_summary()
        
        # 3. 如果是AI消息且包含方案，自动创建
        if sender == "ai" and self.auto_detect:
            scheme_info = self.detector.detect(message)
            if scheme_info:
                return self._create_scheme(session_key, scheme_info, proposed_by="ai")
        
        return None
    
    def _handle_confirmation(self, message: str) -> Optional[str]:
        """处理确认/拒绝指令"""
        message_lower = message.lower().strip()
        
        # 确认关键词
        confirm_keywords = ['确认', '同意', '采纳', '可以', '好的', '没问题', 'yes', 'ok']
        # 拒绝关键词
        reject_keywords = ['拒绝', '不同意', '取消', '不用', '算了', 'no', '否']
        # 执行关键词
        execute_keywords = ['开始执行', '立即执行', '开始', '启动']
        # 完成关键词
        complete_keywords = ['已完成', '搞定了', '做完', '完成']
        
        # 尝试提取方案ID
        scheme_id = self._extract_scheme_id(message)
        
        # 处理确认
        if any(kw in message_lower for kw in confirm_keywords):
            if scheme_id:
                return self._confirm_scheme(scheme_id)
            else:
                # 确认最近的待确认方案
                pending = self.store.get_pending_confirmation()
                if pending:
                    pending.sort(key=lambda s: s.created_at, reverse=True)
                    return self._confirm_scheme(pending[0].id)
        
        # 处理拒绝
        if any(kw in message_lower for kw in reject_keywords):
            if scheme_id:
                return self._cancel_scheme(scheme_id)
            else:
                pending = self.store.get_pending_confirmation()
                if pending:
                    pending.sort(key=lambda s: s.created_at, reverse=True)
                    return self._cancel_scheme(pending[0].id)
        
        # 处理执行
        if any(kw in message_lower for kw in execute_keywords):
            if scheme_id:
                return self._start_execution(scheme_id)
            else:
                confirmed = self.store.get_pending_execution()
                if confirmed:
                    confirmed.sort(key=lambda s: s.confirmed_at or 0, reverse=True)
                    return self._start_execution(confirmed[0].id)
        
        # 处理完成
        if any(kw in message_lower for kw in complete_keywords):
            if scheme_id:
                return self._complete_scheme(scheme_id)
        
        return None
    
    def _extract_scheme_id(self, message: str) -> Optional[str]:
        """从消息中提取方案ID"""
        # 匹配 #SCHEME-xxx 或 方案ID: xxx 格式
        patterns = [
            r'#(SCHEME-[a-zA-Z0-9]+)',
            r'方案[编号ID]*[：:\s]+([a-zA-Z0-9\-]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _is_status_query(self, message: str) -> bool:
        """检查是否是状态查询"""
        query_keywords = ['方案状态', '查看方案', '有哪些方案', '待办方案', 'scheme status']
        message_lower = message.lower()
        return any(kw in message_lower for kw in query_keywords)
    
    def _create_scheme(self, session_key: str, scheme_info: Dict, proposed_by: str = "ai") -> str:
        """创建新方案"""
        scheme_id = f"SCHEME-{int(time.time())}"
        
        scheme = Scheme(
            id=scheme_id,
            title=scheme_info['title'],
            description=scheme_info['description'],
            status=SchemeStatus.PROPOSED.value,
            created_at=time.time(),
            updated_at=time.time(),
            session_key=session_key,
            proposed_by=proposed_by,
            confirmation_requested_at=time.time()
        )
        
        # 清理旧方案
        self._cleanup_old_schemes()
        
        self.store.add(scheme)
        
        return self._format_proposal(scheme)
    
    def _format_proposal(self, scheme: Scheme) -> str:
        """格式化方案提议"""
        msg = f"📋 方案提议 #{scheme.id}\n"
        msg += f"━━━━━━━━━━━━━━\n"
        msg += f"📝 {scheme.title}\n\n"
        msg += f"{scheme.description}\n\n"
        msg += f"━━━━━━━━━━━━━━\n"
        msg += f"请回复「确认」采纳此方案，或「取消」放弃。"
        return msg
    
    def _confirm_scheme(self, scheme_id: str) -> str:
        """确认方案"""
        scheme = self.store.get(scheme_id)
        if not scheme:
            return f"❌ 未找到方案 #{scheme_id}"
        
        if scheme.status != SchemeStatus.PROPOSED.value:
            return f"⚠️ 方案 #{scheme_id} 状态为「{scheme.get_status_display()}」，无需确认"
        
        self.store.update_status(scheme_id, SchemeStatus.CONFIRMED.value)
        
        return f"✅ 方案 #{scheme_id}「{scheme.title}」已确认！\n回复「开始执行」启动方案。"
    
    def _cancel_scheme(self, scheme_id: str) -> str:
        """取消方案"""
        scheme = self.store.get(scheme_id)
        if not scheme:
            return f"❌ 未找到方案 #{scheme_id}"
        
        self.store.update_status(scheme_id, SchemeStatus.CANCELLED.value)
        
        return f"❌ 方案 #{scheme_id}「{scheme.title}」已取消。"
    
    def _start_execution(self, scheme_id: str) -> str:
        """开始执行方案"""
        scheme = self.store.get(scheme_id)
        if not scheme:
            return f"❌ 未找到方案 #{scheme_id}"
        
        if scheme.status not in [SchemeStatus.PROPOSED.value, SchemeStatus.CONFIRMED.value]:
            return f"⚠️ 方案 #{scheme_id} 当前状态为「{scheme.get_status_display()}」"
        
        self.store.update_status(scheme_id, SchemeStatus.IN_PROGRESS.value)
        
        return f"🚀 方案 #{scheme_id}「{scheme.title}」开始执行！\n完成后请回复「已完成」。"
    
    def _complete_scheme(self, scheme_id: str) -> str:
        """完成方案"""
        scheme = self.store.get(scheme_id)
        if not scheme:
            return f"❌ 未找到方案 #{scheme_id}"
        
        self.store.update_status(scheme_id, SchemeStatus.COMPLETED.value)
        
        return f"✨ 方案 #{scheme_id}「{scheme.title}」已完成！做得好！"
    
    def _get_status_summary(self) -> str:
        """获取状态摘要"""
        active = self.store.get_active()
        
        if not active:
            return "📭 当前没有活跃的方案。"
        
        msg = f"📊 方案状态总览（共{len(active)}个活跃）\n"
        msg += "━━━━━━━━━━━━━━\n"
        
        by_status = {}
        for scheme in active:
            status = scheme.status
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(scheme)
        
        for status in [SchemeStatus.PROPOSED.value, SchemeStatus.CONFIRMED.value, SchemeStatus.IN_PROGRESS.value]:
            if status in by_status:
                schemes = by_status[status]
                status_display = Scheme(id="", title="", description="", status=status, 
                                       created_at=0, updated_at=0, session_key="", proposed_by="").get_status_display()
                msg += f"\n{status_display} ({len(schemes)}):\n"
                for s in schemes[:3]:  # 最多显示3个
                    msg += f"  • #{s.id} {s.title[:30]}\n"
                if len(schemes) > 3:
                    msg += f"  ... 还有 {len(schemes) - 3} 个\n"
        
        return msg
    
    def _cleanup_old_schemes(self):
        """清理旧方案"""
        active = self.store.get_active()
        if len(active) > self.max_active_schemes:
            # 按创建时间排序，删除最旧的
            sorted_schemes = sorted(active, key=lambda s: s.created_at)
            to_delete = sorted_schemes[:len(active) - self.max_active_schemes]
            for scheme in to_delete:
                self.store.delete(scheme.id)
    
    def check_reminders(self) -> List[str]:
        """
        检查需要提醒的方案
        
        Returns:
            提醒消息列表
        """
        reminders = []
        active = self.store.get_active()
        
        for scheme in active:
            if scheme.should_remind(self.reminder_interval):
                if scheme.status == SchemeStatus.PROPOSED.value:
                    msg = f"⏰ 提醒：方案 #{scheme.id}「{scheme.title}」等待你的确认\n"
                    msg += f"回复「确认」采纳，或「取消」放弃"
                elif scheme.status == SchemeStatus.CONFIRMED.value:
                    msg = f"⏰ 提醒：方案 #{scheme.id}「{scheme.title}」已确认，等待执行\n"
                    msg += f"回复「开始执行」启动"
                else:
                    continue
                
                # 更新提醒时间
                self.store.update(
                    scheme.id,
                    last_reminded_at=time.time(),
                    reminder_count=scheme.reminder_count + 1
                )
                
                reminders.append(msg)
        
        return reminders
    
    def create_manual_scheme(self, session_key: str, title: str, description: str = "") -> str:
        """手动创建方案"""
        scheme_info = {
            'title': title,
            'description': description or title,
            'type': 'manual',
            'confidence': 'high'
        }
        return self._create_scheme(session_key, scheme_info, proposed_by="user")


# 便捷函数
def create_skill(config: Optional[Dict] = None) -> SchemeConfirmation:
    """创建 Skill 实例"""
    return SchemeConfirmation(config)


def on_message(session_key: str, message: str, sender: str = "user", config: Optional[Dict] = None) -> Optional[str]:
    """处理消息的便捷函数"""
    skill = create_skill(config)
    return skill.on_message(session_key, message, sender)
