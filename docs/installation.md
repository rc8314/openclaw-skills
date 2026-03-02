---
AIGC:
    ContentProducer: Minimax Agent AI
    ContentPropagator: Minimax Agent AI
    Label: AIGC
    ProduceID: "00000000000000000000000000000000"
    PropagateID: "00000000000000000000000000000000"
    ReservedCode1: 30460221008771076e64c7466540e4e1dc75b48aa8f3a967a96da7a97ce1cad80bfcd51e62022100d651c39c55fc057b4d104baebedcc2ba9a97b32d05154379c5d4d72a977215ba
    ReservedCode2: 3044022070792c896a629d24714fca7c82f39be65a7a79efaa068c9adce97f320fd6bea1022078f12e6726a2d29d651631e56145f3c1c0474d5dd48db9d8d3f4116f98ae8c7d
---

# OpenClaw Skills 安装文档

## 项目概述

Phase 1-2 开发的两个经典 Skills：

1. **cross-session-memory**: 跨设备话题记忆延续
2. **scheme-confirmation**: 方案确认与追踪机制

## 目录结构

```
openclaw-skills/
├── cross-session-memory/     # 跨会话记忆 Skill
│   ├── skill.yaml            # Skill 定义
│   ├── main.py               # 主逻辑
│   └── README.md             # 说明文档
├── scheme-confirmation/      # 方案确认 Skill
│   ├── skill.yaml            # Skill 定义
│   ├── main.py               # 主逻辑
│   └── README.md             # 说明文档
├── tests/                    # 测试用例
│   └── test_skills.py        # 测试脚本
├── docs/                     # 文档
│   └── installation.md       # 本文件
└── README.md                 # 项目总览
```

## 安装步骤

### 1. 复制 Skills 到 OpenClaw 目录

```bash
# 创建 skills 目录（如果不存在）
mkdir -p ~/.openclaw/skills

# 复制 skills
cp -r /workspace/projects/openclaw-skills/cross-session-memory ~/.openclaw/skills/
cp -r /workspace/projects/openclaw-skills/scheme-confirmation ~/.openclaw/skills/
```

### 2. 配置 OpenClaw 加载 Skills

编辑 `~/.openclaw/config.json`，添加 skills 配置：

```json
{
  "skills": {
    "cross-session-memory": {
      "enabled": true,
      "config": {
        "memory_ttl": 86400,
        "max_topics": 10,
        "auto_resume": true
      }
    },
    "scheme-confirmation": {
      "enabled": true,
      "config": {
        "confirmation_timeout": 3600,
        "reminder_interval": 7200,
        "auto_detect": true
      }
    }
  }
}
```

### 3. 验证安装

```bash
# 运行测试
cd /workspace/projects/openclaw-skills
python3 tests/test_skills.py
```

## 使用方法

### Cross-Session Memory

**自动触发场景：**
- 新会话开始时，自动检查是否有可恢复的话题
- 检测到相关话题时，主动提示用户

**手动调用：**

```python
from cross_session_memory.main import CrossSessionMemory

# 创建实例
skill = CrossSessionMemory()

# 保存当前话题
skill.save_topic('session_key', messages)

# 检查会话恢复
prompt = skill.on_session_start('new_session', user_message)
```

### Scheme Confirmation

**自动触发场景：**
- AI 提出方案时，自动创建待确认方案
- 定时检查待确认/待执行方案并提醒

**用户指令：**
- `确认` / `同意` - 确认方案
- `取消` / `拒绝` - 取消方案
- `开始执行` - 开始执行已确认方案
- `已完成` - 标记方案完成
- `查看方案状态` - 查看所有活跃方案

**手动调用：**

```python
from scheme_confirmation.main import SchemeConfirmation

# 创建实例
skill = SchemeConfirmation()

# 处理消息
response = skill.on_message('session_key', message, sender='user')

# 检查提醒
reminders = skill.check_reminders()
```

## 配置说明

### cross-session-memory

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| memory_ttl | number | 86400 | 记忆有效期（秒） |
| max_topics | number | 10 | 最大保存话题数 |
| auto_resume | boolean | true | 是否自动恢复话题 |
| similarity_threshold | number | 0.7 | 话题相似度阈值 |

### scheme-confirmation

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| confirmation_timeout | number | 3600 | 确认超时时间（秒） |
| reminder_interval | number | 7200 | 提醒间隔（秒） |
| auto_detect | boolean | true | 是否自动检测方案 |
| max_active_schemes | number | 20 | 最大活跃方案数 |

## 数据存储

Skills 数据默认存储在：

- Cross-Session Memory: `~/.openclaw/skills/cross-session-memory/memories.json`
- Scheme Confirmation: `~/.openclaw/skills/scheme-confirmation/schemes.json`

## 故障排查

### 测试失败

```bash
# 检查 Python 版本（需要 3.7+）
python3 --version

# 单独运行测试
cd /workspace/projects/openclaw-skills
python3 tests/test_skills.py
```

### 数据未保存

检查存储目录权限：
```bash
ls -la ~/.openclaw/skills/
```

### 方案未检测

检查 `auto_detect` 配置是否开启，以及消息是否包含方案关键词（建议、方案、计划等）。

## 更新日志

### v1.0.0 (2026-03-02)
- 初始版本
- 实现 cross-session-memory 核心功能
- 实现 scheme-confirmation 核心功能
- 通过完整测试套件
