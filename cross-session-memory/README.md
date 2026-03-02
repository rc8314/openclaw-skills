---
AIGC:
    ContentProducer: Minimax Agent AI
    ContentPropagator: Minimax Agent AI
    Label: AIGC
    ProduceID: "00000000000000000000000000000000"
    PropagateID: "00000000000000000000000000000000"
    ReservedCode1: 304502200cd010280cedcf4144888610e5bc3c8c9eee0765dd143415483b02942430d831022100ef908e0b7a814bd96afe6fa447f27290ab5182a41b6a2d4c928674008a64e40c
    ReservedCode2: 3046022100ed3da72c6f528e15963a50c1dd07b79199ac5e17b02af7a993a9d90a24115ca3022100eb122f307b30eb7a95738d416bd2a765dfa0d70838053163046900ec55c2a67b
---

# Cross-Session Memory Skill

## 功能描述

跨设备话题记忆延续 - 自动检测话题中断，在新会话中主动恢复上下文。

## 核心能力

1. **话题检测**: 识别正在进行的对话主题
2. **记忆存储**: 将会话关键信息持久化存储
3. **上下文恢复**: 在新会话中主动提示延续话题
4. **多设备同步**: 支持跨设备记忆访问

## 触发条件

- 用户在新会话中发送第一条消息
- 检测到之前有未完成的对话主题
- 时间间隔在可配置范围内（默认24小时）

## 记忆内容

- 话题标题
- 最后讨论的关键点
- 待办事项/待确认事项
- 时间戳

## 配置项

```yaml
memory_ttl: 86400  # 记忆有效期（秒）
max_topics: 10     # 最大保存话题数
auto_resume: true  # 是否自动恢复
```
