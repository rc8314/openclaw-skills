#!/usr/bin/env python3
"""
Cross-Session Memory Skill - 跨会话记忆管理

功能：
1. 检测并提取会话中的关键话题
2. 持久化存储话题记忆
3. 在新会话中恢复上下文
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class TopicMemory:
    """话题记忆结构"""
    id: str
    title: str
    summary: str
    key_points: List[str]
    pending_items: List[str]
    created_at: float
    updated_at: float
    session_key: str
    ttl: int = 86400  # 默认24小时
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() - self.updated_at > self.ttl
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TopicMemory':
        return cls(**data)


class MemoryStore:
    """记忆存储管理器"""
    
    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir is None:
            storage_dir = os.path.expanduser("~/.openclaw/skills/cross-session-memory")
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.memories_file = self.storage_dir / "memories.json"
        self._memories: Dict[str, TopicMemory] = {}
        self._load()
    
    def _load(self):
        """从文件加载记忆"""
        if self.memories_file.exists():
            try:
                with open(self.memories_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for topic_id, topic_data in data.items():
                        self._memories[topic_id] = TopicMemory.from_dict(topic_data)
            except Exception as e:
                print(f"[MemoryStore] 加载记忆失败: {e}")
                self._memories = {}
    
    def _save(self):
        """保存记忆到文件"""
        try:
            data = {k: v.to_dict() for k, v in self._memories.items()}
            with open(self.memories_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[MemoryStore] 保存记忆失败: {e}")
    
    def add(self, memory: TopicMemory) -> bool:
        """添加新记忆"""
        self._memories[memory.id] = memory
        self._save()
        return True
    
    def get(self, topic_id: str) -> Optional[TopicMemory]:
        """获取特定记忆"""
        return self._memories.get(topic_id)
    
    def get_active(self, max_age: int = 86400) -> List[TopicMemory]:
        """获取所有活跃记忆（未过期）"""
        now = time.time()
        return [
            m for m in self._memories.values()
            if now - m.updated_at <= max_age
        ]
    
    def update(self, topic_id: str, **kwargs) -> bool:
        """更新记忆"""
        if topic_id not in self._memories:
            return False
        memory = self._memories[topic_id]
        for key, value in kwargs.items():
            if hasattr(memory, key):
                setattr(memory, key, value)
        memory.updated_at = time.time()
        self._save()
        return True
    
    def delete(self, topic_id: str) -> bool:
        """删除记忆"""
        if topic_id in self._memories:
            del self._memories[topic_id]
            self._save()
            return True
        return False
    
    def cleanup_expired(self) -> int:
        """清理过期记忆，返回清理数量"""
        expired = [k for k, v in self._memories.items() if v.is_expired()]
        for topic_id in expired:
            del self._memories[topic_id]
        if expired:
            self._save()
        return len(expired)
    
    def get_recent(self, limit: int = 5) -> List[TopicMemory]:
        """获取最近更新的记忆"""
        sorted_memories = sorted(
            self._memories.values(),
            key=lambda m: m.updated_at,
            reverse=True
        )
        return sorted_memories[:limit]


class TopicExtractor:
    """话题提取器 - 从对话中提取关键信息"""
    
    # 关键词模式，用于识别话题类型
    TOPIC_PATTERNS = {
        'task': ['任务', '待办', 'todo', '需要', '计划', '安排'],
        'question': ['问题', '疑问', '怎么', '如何', '为什么', '吗？', '呢？'],
        'decision': ['决定', '选择', '方案', '建议', '推荐', '对比'],
        'info': ['信息', '资料', '数据', '报告', '文档', '链接'],
    }
    
    def __init__(self):
        self.store = MemoryStore()
    
    def extract_topic(self, session_key: str, messages: List[Dict]) -> Optional[TopicMemory]:
        """
        从消息列表中提取话题
        
        Args:
            session_key: 会话标识
            messages: 消息列表，每项包含 role 和 content
        
        Returns:
            TopicMemory 对象或 None
        """
        if not messages:
            return None
        
        # 提取最后几条消息分析
        recent_msgs = messages[-5:] if len(messages) > 5 else messages
        
        # 生成话题标题（取第一条用户消息的前20字）
        title = self._generate_title(recent_msgs)
        
        # 生成摘要
        summary = self._generate_summary(recent_msgs)
        
        # 提取关键点
        key_points = self._extract_key_points(recent_msgs)
        
        # 提取待办事项
        pending_items = self._extract_pending(recent_msgs)
        
        # 识别话题类型
        topic_type = self._detect_topic_type(summary)
        
        topic_id = f"{session_key}_{int(time.time())}"
        
        return TopicMemory(
            id=topic_id,
            title=title,
            summary=summary,
            key_points=key_points,
            pending_items=pending_items,
            created_at=time.time(),
            updated_at=time.time(),
            session_key=session_key
        )
    
    def _generate_title(self, messages: List[Dict]) -> str:
        """生成话题标题"""
        for msg in messages:
            if msg.get('role') == 'user':
                content = msg.get('content', '')
                # 取前30个字符，去除换行
                title = content.replace('\n', ' ')[:30]
                if len(content) > 30:
                    title += '...'
                return title
        return "未命名话题"
    
    def _generate_summary(self, messages: List[Dict]) -> str:
        """生成话题摘要"""
        # 简单实现：合并所有用户消息的前100字
        user_contents = []
        for msg in messages:
            if msg.get('role') == 'user':
                user_contents.append(msg.get('content', ''))
        
        combined = ' | '.join(user_contents)
        summary = combined[:100]
        if len(combined) > 100:
            summary += '...'
        return summary
    
    def _extract_key_points(self, messages: List[Dict]) -> List[str]:
        """提取关键点"""
        key_points = []
        
        for msg in messages:
            content = msg.get('content', '')
            # 简单的启发式规则
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                # 检测列表项
                if line.startswith('- ') or line.startswith('* ') or line.startswith('• '):
                    key_points.append(line[2:])
                # 检测数字列表
                elif len(line) > 3 and line[0].isdigit() and line[1:3] in ['. ', '、']:
                    key_points.append(line[3:])
        
        return key_points[:5]  # 最多5个关键点
    
    def _extract_pending(self, messages: List[Dict]) -> List[str]:
        """提取待办/待确认事项"""
        pending = []
        pending_keywords = ['待办', 'todo', '需要', '计划', '确认', '决定', '选择']
        
        for msg in messages:
            content = msg.get('content', '')
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                # 检测包含待办关键词的行
                if any(kw in line for kw in pending_keywords):
                    if len(line) > 5:  # 过滤太短的行
                        pending.append(line)
        
        return list(set(pending))[:3]  # 去重，最多3个
    
    def _detect_topic_type(self, summary: str) -> str:
        """检测话题类型"""
        summary_lower = summary.lower()
        scores = {}
        
        for topic_type, keywords in self.TOPIC_PATTERNS.items():
            score = sum(1 for kw in keywords if kw in summary_lower)
            scores[topic_type] = score
        
        if scores:
            return max(scores, key=scores.get)
        return 'general'


class CrossSessionMemory:
    """跨会话记忆主类"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.store = MemoryStore()
        self.extractor = TopicExtractor()
        self.memory_ttl = self.config.get('memory_ttl', 86400)
        self.max_topics = self.config.get('max_topics', 10)
        self.auto_resume = self.config.get('auto_resume', True)
    
    def on_session_start(self, session_key: str, user_message: str = "") -> Optional[str]:
        """
        会话开始时检查是否有可恢复的话题
        
        Returns:
            恢复提示消息或 None
        """
        if not self.auto_resume:
            return None
        
        # 获取活跃记忆
        active_memories = self.store.get_active(self.memory_ttl)
        
        if not active_memories:
            return None
        
        # 按更新时间排序
        active_memories.sort(key=lambda m: m.updated_at, reverse=True)
        
        # 检查用户新消息是否与已有话题相关
        if user_message:
            related = self._find_related_topic(user_message, active_memories)
            if related:
                return self._generate_resume_prompt(related, is_related=True)
        
        # 返回最近的话题
        most_recent = active_memories[0]
        time_diff = time.time() - most_recent.updated_at
        
        # 如果时间间隔太短（<5分钟），不提示
        if time_diff < 300:
            return None
        
        return self._generate_resume_prompt(most_recent)
    
    def _find_related_topic(self, message: str, memories: List[TopicMemory]) -> Optional[TopicMemory]:
        """查找与消息相关的话题"""
        message_lower = message.lower()
        
        for memory in memories:
            # 简单的关键词匹配
            title_words = set(memory.title.lower().split())
            message_words = set(message_lower.split())
            
            # 计算重叠词
            overlap = title_words & message_words
            if len(overlap) >= 2:  # 至少2个词重叠
                return memory
            
            # 检查关键点
            for point in memory.key_points:
                if any(word in message_lower for word in point.lower().split()[:3]):
                    return memory
        
        return None
    
    def _generate_resume_prompt(self, memory: TopicMemory, is_related: bool = False) -> str:
        """生成恢复提示"""
        time_str = self._format_time_ago(time.time() - memory.updated_at)
        
        if is_related:
            prompt = f"💡 看起来你在继续之前的话题「{memory.title}」\n"
        else:
            prompt = f"💭 {time_str}前我们讨论过：「{memory.title}」\n"
        
        if memory.summary:
            prompt += f"\n📋 摘要：{memory.summary}\n"
        
        if memory.pending_items:
            prompt += f"\n⏳ 待处理：\n"
            for item in memory.pending_items:
                prompt += f"   • {item}\n"
        
        prompt += f"\n要继续这个话题吗？（回复「继续」或忽略此提示）"
        
        return prompt
    
    def _format_time_ago(self, seconds: float) -> str:
        """格式化时间差"""
        if seconds < 3600:
            return f"{int(seconds / 60)}分钟"
        elif seconds < 86400:
            return f"{int(seconds / 3600)}小时"
        else:
            return f"{int(seconds / 86400)}天"
    
    def save_topic(self, session_key: str, messages: List[Dict]) -> Optional[str]:
        """
        保存当前话题
        
        Returns:
            话题ID或None
        """
        topic = self.extractor.extract_topic(session_key, messages)
        if topic:
            # 清理旧话题（保持最大数量）
            self._cleanup_old_topics()
            self.store.add(topic)
            return topic.id
        return None
    
    def _cleanup_old_topics(self):
        """清理旧话题，保持最大数量"""
        all_topics = self.store.get_recent(self.max_topics * 2)
        if len(all_topics) > self.max_topics:
            # 删除最旧的话题
            to_delete = all_topics[self.max_topics:]
            for topic in to_delete:
                self.store.delete(topic.id)
    
    def update_topic(self, topic_id: str, messages: List[Dict]) -> bool:
        """更新话题"""
        memory = self.store.get(topic_id)
        if not memory:
            return False
        
        # 重新提取信息
        new_topic = self.extractor.extract_topic(memory.session_key, messages)
        if new_topic:
            self.store.update(
                topic_id,
                summary=new_topic.summary,
                key_points=new_topic.key_points,
                pending_items=new_topic.pending_items,
                updated_at=time.time()
            )
            return True
        return False
    
    def cleanup(self) -> int:
        """清理过期记忆"""
        return self.store.cleanup_expired()


# 便捷函数，供外部调用
def create_skill(config: Optional[Dict] = None) -> CrossSessionMemory:
    """创建 Skill 实例"""
    return CrossSessionMemory(config)


def on_session_start(session_key: str, user_message: str = "", config: Optional[Dict] = None) -> Optional[str]:
    """会话开始时的便捷函数"""
    skill = create_skill(config)
    return skill.on_session_start(session_key, user_message)


def save_current_topic(session_key: str, messages: List[Dict], config: Optional[Dict] = None) -> Optional[str]:
    """保存当前话题的便捷函数"""
    skill = create_skill(config)
    return skill.save_topic(session_key, messages)
