#!/usr/bin/env python3
"""
Cross-Session Memory Skill - 跨会话记忆管理（兼容版）

兼容现有系统：
1. 读取 /workspace/memory/ 现有记忆文件
2. 读取 /workspace/diary/ 日记文件
3. 写入时同步到现有路径和 Skill 路径

功能：
1. 检测并提取会话中的关键话题
2. 持久化存储话题记忆
3. 在新会话中恢复上下文
"""

import json
import os
import time
import re
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
    source: str = "skill"  # 来源：skill, memory, diary
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() - self.updated_at > self.ttl
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TopicMemory':
        # 兼容旧格式（没有 source 字段）
        if 'source' not in data:
            data['source'] = 'skill'
        return cls(**data)


class CompatibilityStore:
    """兼容存储管理器 - 桥接现有系统和 Skill"""
    
    # 存储路径优先级（从高到低）
    LEGACY_PATHS = {
        'memory': Path("/workspace/memory"),
        'diary': Path("/workspace/diary"),
        'plans': Path("/workspace/plans/active"),
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.compatibility_mode = self.config.get('compatibility_mode', True)
        self.use_legacy_storage = self.config.get('use_legacy_storage', True)
        
        # Skill 自身存储路径
        skill_dir = os.path.expanduser("~/.openclaw/skills/cross-session-memory")
        self.skill_storage = Path(skill_dir)
        self.skill_storage.mkdir(parents=True, exist_ok=True)
        self.memories_file = self.skill_storage / "memories.json"
        
        self._memories: Dict[str, TopicMemory] = {}
        self._load()
    
    def _load(self):
        """加载记忆 - 优先从现有系统读取"""
        loaded = False
        
        if self.compatibility_mode:
            # 1. 尝试从现有系统加载
            loaded = self._load_from_legacy()
        
        if not loaded:
            # 2. 从 Skill 自身存储加载
            self._load_from_skill()
    
    def _load_from_legacy(self) -> bool:
        """从现有系统路径加载记忆"""
        try:
            # 读取 memory 目录的 markdown 文件
            memory_dir = self.LEGACY_PATHS['memory']
            if memory_dir.exists():
                for md_file in memory_dir.glob("*.md"):
                    topic = self._parse_memory_file(md_file)
                    if topic:
                        self._memories[topic.id] = topic
            
            # 读取 diary 目录
            diary_dir = self.LEGACY_PATHS['diary']
            if diary_dir.exists():
                for md_file in diary_dir.glob("*.md"):
                    topic = self._parse_diary_file(md_file)
                    if topic:
                        self._memories[topic.id] = topic
            
            return len(self._memories) > 0
        except Exception as e:
            print(f"[CompatibilityStore] 从现有系统加载失败: {e}")
            return False
    
    def _parse_memory_file(self, file_path: Path) -> Optional[TopicMemory]:
        """解析现有 memory 文件为 TopicMemory"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # 提取标题（文件名或第一行）
            title = file_path.stem
            if content.strip():
                first_line = content.strip().split('\n')[0]
                if first_line.startswith('# '):
                    title = first_line[2:]
            
            # 提取关键点（列表项）
            key_points = re.findall(r'[-*]\s*(.+)', content)[:5]
            
            # 提取待办事项
            pending_items = re.findall(r'(?:TODO|待办|待处理)[：:]?\s*(.+)', content, re.IGNORECASE)[:3]
            
            # 获取文件修改时间
            mtime = file_path.stat().st_mtime
            
            topic_id = f"memory_{file_path.stem}_{int(mtime)}"
            
            return TopicMemory(
                id=topic_id,
                title=title[:50],
                summary=content[:200].replace('\n', ' '),
                key_points=key_points,
                pending_items=pending_items,
                created_at=mtime,
                updated_at=mtime,
                session_key="legacy",
                source="memory"
            )
        except Exception as e:
            print(f"[CompatibilityStore] 解析 memory 文件失败 {file_path}: {e}")
            return None
    
    def _parse_diary_file(self, file_path: Path) -> Optional[TopicMemory]:
        """解析 diary 文件为 TopicMemory"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # 日记标题通常是日期
            title = f"日记 {file_path.stem}"
            
            # 提取关键点
            key_points = re.findall(r'[-*]\s*(.+)', content)[:5]
            
            mtime = file_path.stat().st_mtime
            topic_id = f"diary_{file_path.stem}"
            
            return TopicMemory(
                id=topic_id,
                title=title,
                summary=content[:200].replace('\n', ' '),
                key_points=key_points,
                pending_items=[],
                created_at=mtime,
                updated_at=mtime,
                session_key="legacy",
                source="diary"
            )
        except Exception as e:
            print(f"[CompatibilityStore] 解析 diary 文件失败 {file_path}: {e}")
            return None
    
    def _load_from_skill(self):
        """从 Skill 自身存储加载"""
        if self.memories_file.exists():
            try:
                with open(self.memories_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for topic_id, topic_data in data.items():
                        self._memories[topic_id] = TopicMemory.from_dict(topic_data)
            except Exception as e:
                print(f"[CompatibilityStore] 从 Skill 加载失败: {e}")
                self._memories = {}
    
    def _save(self):
        """保存记忆 - 同步到所有启用的路径"""
        try:
            # 1. 保存到 Skill 自身存储
            data = {k: v.to_dict() for k, v in self._memories.items()}
            with open(self.memories_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 2. 如果启用 legacy 模式，同步到现有系统
            if self.use_legacy_storage:
                self._sync_to_legacy()
                
        except Exception as e:
            print(f"[CompatibilityStore] 保存失败: {e}")
    
    def _sync_to_legacy(self):
        """同步到现有系统路径"""
        try:
            # 只同步 skill 来源的记忆到 memory 目录
            memory_dir = self.LEGACY_PATHS['memory']
            memory_dir.mkdir(parents=True, exist_ok=True)
            
            for topic in self._memories.values():
                if topic.source == "skill":
                    # 转换为 markdown 格式写入
                    md_content = self._topic_to_markdown(topic)
                    md_file = memory_dir / f"{topic.id}.md"
                    md_file.write_text(md_content, encoding='utf-8')
        except Exception as e:
            print(f"[CompatibilityStore] 同步到现有系统失败: {e}")
    
    def _topic_to_markdown(self, topic: TopicMemory) -> str:
        """将 TopicMemory 转换为 Markdown 格式"""
        lines = [
            f"# {topic.title}",
            "",
            f"**创建时间**: {datetime.fromtimestamp(topic.created_at).strftime('%Y-%m-%d %H:%M')}",
            f"**来源**: {topic.source}",
            "",
            "## 摘要",
            topic.summary,
            "",
        ]
        
        if topic.key_points:
            lines.extend(["## 关键点", ""])
            for point in topic.key_points:
                lines.append(f"- {point}")
            lines.append("")
        
        if topic.pending_items:
            lines.extend(["## 待处理", ""])
            for item in topic.pending_items:
                lines.append(f"- [ ] {item}")
            lines.append("")
        
        return "\n".join(lines)
    
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
    
    def get_recent(self, limit: int = 5) -> List[TopicMemory]:
        """获取最近更新的记忆"""
        sorted_memories = sorted(
            self._memories.values(),
            key=lambda m: m.updated_at,
            reverse=True
        )
        return sorted_memories[:limit]
    
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
        """清理过期记忆"""
        expired = [k for k, v in self._memories.items() if v.is_expired()]
        for topic_id in expired:
            del self._memories[topic_id]
        if expired:
            self._save()
        return len(expired)


class TopicExtractor:
    """话题提取器 - 从对话中提取关键信息"""
    
    TOPIC_PATTERNS = {
        'task': ['任务', '待办', 'todo', '需要', '计划', '安排'],
        'question': ['问题', '疑问', '怎么', '如何', '为什么', '吗？', '呢？'],
        'decision': ['决定', '选择', '方案', '建议', '推荐', '对比'],
        'info': ['信息', '资料', '数据', '报告', '文档', '链接'],
    }
    
    def __init__(self):
        pass
    
    def extract_topic(self, session_key: str, messages: List[Dict]) -> Optional[TopicMemory]:
        """从消息列表中提取话题"""
        if not messages:
            return None
        
        recent_msgs = messages[-5:] if len(messages) > 5 else messages
        
        title = self._generate_title(recent_msgs)
        summary = self._generate_summary(recent_msgs)
        key_points = self._extract_key_points(recent_msgs)
        pending_items = self._extract_pending(recent_msgs)
        
        topic_id = f"{session_key}_{int(time.time())}"
        
        return TopicMemory(
            id=topic_id,
            title=title,
            summary=summary,
            key_points=key_points,
            pending_items=pending_items,
            created_at=time.time(),
            updated_at=time.time(),
            session_key=session_key,
            source="skill"
        )
    
    def _generate_title(self, messages: List[Dict]) -> str:
        """生成话题标题"""
        for msg in messages:
            if msg.get('role') == 'user':
                content = msg.get('content', '')
                title = content.replace('\n', ' ')[:30]
                if len(content) > 30:
                    title += '...'
                return title
        return "未命名话题"
    
    def _generate_summary(self, messages: List[Dict]) -> str:
        """生成话题摘要"""
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
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('- ') or line.startswith('* ') or line.startswith('• '):
                    key_points.append(line[2:])
                elif len(line) > 3 and line[0].isdigit() and line[1:3] in ['. ', '、']:
                    key_points.append(line[3:])
        return key_points[:5]
    
    def _extract_pending(self, messages: List[Dict]) -> List[str]:
        """提取待办/待确认事项"""
        pending = []
        pending_keywords = ['待办', 'todo', '需要', '计划', '确认', '决定', '选择']
        
        for msg in messages:
            content = msg.get('content', '')
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if any(kw in line for kw in pending_keywords):
                    if len(line) > 5:
                        pending.append(line)
        
        return list(set(pending))[:3]


class CrossSessionMemory:
    """跨会话记忆主类（兼容版）"""
    
    DEFAULT_CONFIG = {
        'compatibility_mode': True,      # 兼容现有系统
        'use_legacy_storage': True,      # 使用现有存储路径
        'auto_resume': False,            # 默认关闭自动恢复（避免冲突）
        'auto_save': False,              # 默认关闭自动保存
        'memory_ttl': 86400,
        'max_topics': 10,
        'similarity_threshold': 0.7,
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self.store = CompatibilityStore(self.config)
        self.extractor = TopicExtractor()
    
    def on_session_start(self, session_key: str, user_message: str = "") -> Optional[str]:
        """
        会话开始时检查是否有可恢复的话题
        注意：默认 auto_resume=False，需要手动调用
        """
        if not self.config.get('auto_resume', False):
            return None
        
        active_memories = self.store.get_active(self.config['memory_ttl'])
        
        if not active_memories:
            return None
        
        active_memories.sort(key=lambda m: m.updated_at, reverse=True)
        
        if user_message:
            related = self._find_related_topic(user_message, active_memories)
            if related:
                return self._generate_resume_prompt(related, is_related=True)
        
        most_recent = active_memories[0]
        time_diff = time.time() - most_recent.updated_at
        
        if time_diff < 300:  # 5分钟内不提示
            return None
        
        return self._generate_resume_prompt(most_recent)
    
    def manual_resume_check(self, session_key: str, user_message: str = "") -> Optional[str]:
        """手动检查可恢复话题（推荐用法）"""
        return self.on_session_start(session_key, user_message)
    
    def _find_related_topic(self, message: str, memories: List[TopicMemory]) -> Optional[TopicMemory]:
        """查找与消息相关的话题"""
        message_lower = message.lower()
        
        for memory in memories:
            title_words = set(memory.title.lower().split())
            message_words = set(message_lower.split())
            
            overlap = title_words & message_words
            if len(overlap) >= 2:
                return memory
            
            for point in memory.key_points:
                if any(word in message_lower for word in point.lower().split()[:3]):
                    return memory
        
        return None
    
    def _generate_resume_prompt(self, memory: TopicMemory, is_related: bool = False) -> str:
        """生成恢复提示"""
        time_str = self._format_time_ago(time.time() - memory.updated_at)
        source_icon = "💾" if memory.source == "memory" else "📔" if memory.source == "diary" else "💭"
        
        if is_related:
            prompt = f"{source_icon} 看起来你在继续之前的话题「{memory.title}」\n"
        else:
            prompt = f"{source_icon} {time_str}前我们讨论过：「{memory.title}」\n"
        
        if memory.summary:
            prompt += f"\n📋 摘要：{memory.summary[:100]}...\n"
        
        if memory.pending_items:
            prompt += f"\n⏳ 待处理：\n"
            for item in memory.pending_items[:3]:
                prompt += f"   • {item}\n"
        
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
        """保存当前话题"""
        topic = self.extractor.extract_topic(session_key, messages)
        if topic:
            self._cleanup_old_topics()
            self.store.add(topic)
            return topic.id
        return None
    
    def _cleanup_old_topics(self):
        """清理旧话题"""
        max_topics = self.config.get('max_topics', 10)
        all_topics = self.store.get_recent(max_topics * 2)
        if len(all_topics) > max_topics:
            to_delete = all_topics[max_topics:]
            for topic in to_delete:
                if topic.source == "skill":  # 只删除 skill 来源的
                    self.store.delete(topic.id)
    
    def update_topic(self, topic_id: str, messages: List[Dict]) -> bool:
        """更新话题"""
        memory = self.store.get(topic_id)
        if not memory:
            return False
        
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
    
    def list_topics(self, limit: int = 10) -> List[Dict]:
        """列出所有话题（供手动查询）"""
        topics = self.store.get_recent(limit)
        return [{
            'id': t.id,
            'title': t.title,
            'source': t.source,
            'updated_at': datetime.fromtimestamp(t.updated_at).strftime('%Y-%m-%d %H:%M'),
            'pending_count': len(t.pending_items)
        } for t in topics]
    
    def cleanup(self) -> int:
        """清理过期记忆"""
        return self.store.cleanup_expired()


# 便捷函数
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


def list_all_topics(limit: int = 10, config: Optional[Dict] = None) -> List[Dict]:
    """列出所有话题的便捷函数"""
    skill = create_skill(config)
    return skill.list_topics(limit)
