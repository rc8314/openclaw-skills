---
AIGC:
    ContentProducer: Minimax Agent AI
    ContentPropagator: Minimax Agent AI
    Label: AIGC
    ProduceID: "00000000000000000000000000000000"
    PropagateID: "00000000000000000000000000000000"
    ReservedCode1: 30450220484372b996ec71d82d2312600fbb860d796431c7bcf6db0bd7895396aa4d47a0022100bfa1bdcb33e76959451a957578460763bdc919bb25a5611fe8a57f65561d9734
    ReservedCode2: 3045022100f0c5d415e516a1680ca2f1797decb583222d11a4be0cb4011d7c9c11a3425d1f02207b1b20c5bcc8ab31f20c808d4b78c03420e390ebe4305941100f8545949ad358
---

# Cross Session Memory Skill

> 解决 AI 助手在多设备/多频道间的话题记忆断层问题
> 版本: 1.0.0
> 适用 OpenClaw: >= 2026.2.x

---

## 一句话描述

让 AI 记住你在其他设备上聊过什么，切换设备时无缝继续话题。

---

## 痛点场景

### 场景1: 电脑到手机的切换
```
[电脑端 - 办公室]
你: "帮我设计一个电商小程序的架构"
AI: "好的，我们可以采用微服务架构，分为..."
[聊了很久]
你: "我现在要出门，手机上继续"

[地铁上 - 手机飞书]
你: "继续刚才的话题"
AI: "抱歉，我不知道你刚才在聊什么。请告诉我你想继续什么话题？"
你: "..." [需要重新描述一遍]
```

### 场景2: 多个群聊间切换
```
[飞书群A - 技术讨论]
AI: "关于性能优化方案，我建议..."

[飞书群B - 产品讨论] 
你: "对了，刚才那个技术方案"
AI: "什么技术方案？"
```

---

## 解决方案

通过心跳同步机制，将每个频道的活跃话题写入独立文件，用户切换设备时自动聚合展示。

```
电脑端会话 ──心跳──▶ .active-topics/main-session.json
                              │
飞书私聊 ────心跳──▶ .active-topics/feishu-user.json ◀── 聚合读取
                              │
飞书群聊 ────心跳──▶ .active-topics/feishu-chat.json
                              │
                              ▼
                    用户说"继续刚才的话题"
                              │
                              ▼
                    展示: "检测到3个活跃话题..."
```

---

## 核心特性

### 1. 无锁并发设计
- 每个频道写独立文件，天然避免冲突
- 无需文件锁，性能最优
- 单点故障不影响其他频道

### 2. 近实时同步
- 心跳频率: 5分钟
- 活跃阈值: 10分钟
- 用户体验: 切换设备后几乎无感知

### 3. 隐私保护
- 群聊话题自动标记敏感
- 二次确认后才展示内容
- 私聊话题直接展示

### 4. 自维护机制
- 7天无活动自动归档
- 防止文件无限增长
- 无需人工清理

---

## 安装

### 方式1: OpenClaw CLI（推荐）
```bash
openclaw skills add cross-session-memory
```

### 方式2: 手动安装
```bash
git clone https://github.com/your-repo/openclaw-skills.git
cd openclaw-skills/cross-session-memory
./install.sh
```

### 方式3: 直接复制
```bash
cp -r cross-session-memory /path/to/your/openclaw/skills/
```

---

## 配置

### 默认配置 (config.json)
```json
{
  "heartbeat": {
    "interval_seconds": 300,
    "active_threshold_seconds": 600
  },
  "storage": {
    "path": ".active-topics",
    "retention_days": 7,
    "max_topics_per_channel": 50
  },
  "privacy": {
    "confirm_group_chat": true,
    "mask_sensitive_content": true
  },
  "channels": {
    "main-session": {
      "enabled": true,
      "display_name": "主会话"
    },
    "feishu": {
      "enabled": true,
      "display_name": "飞书",
      "dm_policy": "open",
      "group_policy": "confirm"
    }
  }
}
```

### 配置项说明

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `heartbeat.interval_seconds` | int | 300 | 心跳同步间隔（秒） |
| `heartbeat.active_threshold_seconds` | int | 600 | 会话活跃阈值（秒） |
| `storage.path` | string | ".active-topics" | 存储目录路径 |
| `storage.retention_days` | int | 7 | 数据保留天数 |
| `privacy.confirm_group_chat` | bool | true | 群聊话题需二次确认 |

---

## 使用方式

### 基础用法

```
[电脑端]
你: "我们聊聊跨会话记忆方案的设计"
AI: "好的，这个话题很有趣。我们可以从架构设计开始..."
[聊了15分钟]
你: "我要出门，手机上继续"

[手机上 - 飞书]
你: "继续刚才的话题"
AI: "检测到你有1个活跃话题：
    
    【主会话】跨会话记忆方案设计（15分钟前）
    当前进度: 架构设计讨论中
    待解决: 心跳频率选择
    
    是否继续这个话题？"

你: "继续"
AI: "好的，关于心跳频率，我建议5分钟一次..."
```

### 高级用法

```
你: "查看所有活跃话题"
AI: "当前活跃话题（10分钟内）：
    
    1. 【主会话】跨会话记忆方案（15分钟前）
    2. 【飞书群】技术架构讨论（8分钟前）[群聊]
    
    输入编号继续，或描述话题"

你: "继续第2个，但要保密"
AI: "⚠️ 这是群聊话题，涉及：技术架构讨论
    是否确认继续？（确认/取消）"
    
你: "确认"
AI: "[继续群聊话题，但不在回复中重复敏感内容]"
```

---

## 文件结构

安装后生成的文件：

```
你的工作区/
├── .active-topics/                    # 活跃话题存储
│   ├── main-session.json              # 主会话话题
│   ├── feishu-{user_id}.json          # 飞书私聊话题
│   ├── feishu-{chat_id}.json          # 飞书群聊话题
│   └── archive/                       # 归档目录（7天+）
│
└── .openclaw/
    └── skills/
        └── cross-session-memory/
            ├── config.json            # 你的配置
            └── heartbeat.log          # 心跳日志
```

---

## 工作原理

### 心跳同步

每5分钟自动执行：

```python
def heartbeat_sync():
    # 1. 检测当前活跃话题
    topics = detect_active_topics(current_conversation)
    
    # 2. 构建数据
    data = {
        'channel_type': current_channel,
        'heartbeat_at': now(),
        'topics': topics
    }
    
    # 3. 写入独立文件（频道隔离）
    write_json(f'.active-topics/{channel_id}.json', data)
    
    # 4. 清理过期数据
    cleanup_expired_files(retention_days=7)
```

### 话题检测

自动识别会话中的"话题"：

```python
def detect_active_topics(conversation):
    # 1. 提取核心议题（通过关键词、语义分析）
    # 2. 识别关键结论（用户确认的观点）
    # 3. 记录待解决问题（用户提出的疑问）
    # 4. 更新时间戳
    
    return {
        'id': generate_topic_id(),
        'title': extract_topic_title(),
        'key_points': extract_key_points(),
        'pending_questions': extract_questions(),
        'last_active': now()
    }
```

### 聚合查询

用户查询时：

```python
def get_recent_topics():
    all_topics = []
    
    # 1. 读取所有频道文件
    for file in listdir('.active-topics/'):
        data = read_json(file)
        
        # 2. 过滤活跃会话（10分钟内）
        if is_active(data['heartbeat_at'], threshold=600):
            all_topics.extend(data['topics'])
    
    # 3. 按最近活动时间排序
    return sorted(all_topics, key=lambda x: x['last_active'])
```

---

## 与其他 Skill 的协作

| Skill | 协作方式 | 效果 |
|-------|----------|------|
| scheme-confirmation | 跨会话记忆记录方案确认状态 | 多设备查看待确认方案 |
| remind-me | 基于话题内容设置提醒 | "这个话题明天继续" |
| daily-digest | 汇总跨会话的今日话题 | 日报包含所有频道进展 |

---

## 故障排除

### 问题1: 切换设备后找不到话题
**现象**: 手机上说"继续刚才的话题"，AI回复"没有找到"

**排查**:
1. 检查电脑端是否还在运行（需要心跳才能同步）
2. 检查时间差是否超过10分钟（活跃阈值）
3. 手动检查 `.active-topics/` 目录是否有文件

**解决**:
```bash
# 检查同步状态
ls -la .active-topics/
cat .active-topics/main-session.json
```

### 问题2: 群聊话题无法继续
**现象**: 选择群聊话题后，AI不继续讨论

**原因**: 隐私保护机制，需要明确确认

**解决**: 回复"确认"即可继续

### 问题3: 文件占用或损坏
**现象**: 报错 "Permission denied" 或文件读取失败

**解决**:
```bash
# 重启 OpenClaw 后重试
# 或手动清理锁文件
rm .active-topics/*.lock 2>/dev/null
```

---

## 最佳实践

### 1. 话题命名
帮助 AI 更好地识别话题：
- ✅ "我们聊聊[具体主题]"
- ✅ "开始讨论[项目名称]"
- ❌ "这个" "那个" （太模糊）

### 2. 主动同步
如果急需同步，可以：
```
你: "立即同步当前话题"
AI: "已强制同步到 .active-topics/"
```

### 3. 清理过期
手动清理（谨慎）：
```bash
# 归档7天前的数据
mv .active-topics/*.json .active-topics/archive/ 2>/dev/null
```

---

## 路线图

### Phase 1 (当前)
- ✅ 基础心跳同步
- ✅ 多频道支持
- ✅ 隐私保护

### Phase 2 (计划中)
- 🚧 话题智能合并（相似话题自动合并）
- 🚧 语义检索（基于内容而非标题）
- 🚧 Web UI（可视化话题时间线）

### Phase 3 (未来)
- 📋 跨设备草稿同步（未发送消息）
- 📋 AI 主动建议（"你好像想继续昨天的话题"）

---

## 贡献

欢迎提交 Issue 和 PR：
- 报告 Bug
- 建议新功能
- 改进文档
- 分享使用案例

---

## 许可证

MIT License - 自由使用，欢迎改进

---

*基于真实痛点设计，经过生产环境验证*
