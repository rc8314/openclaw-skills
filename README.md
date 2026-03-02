# OpenClaw Skills

[![GitHub](https://img.shields.io/badge/GitHub-rc8314%2Fopenclaw--skills-blue)](https://github.com/rc8314/openclaw-skills)
[![Status](https://img.shields.io/badge/status-stable-success)](https://github.com/rc8314/openclaw-skills)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[English](#english) | [中文](#中文)

---

<a name="english"></a>
## English

Enhance OpenClaw with cross-session memory and scheme confirmation tracking capabilities.

### Overview

Two production-ready Skills that solve the context fragmentation problem of AI assistants in multi-session scenarios.

### Skills

#### 1. cross-session-memory
Cross-device topic memory continuation - enables seamless conversation context across different sessions.

**Features:**
- Auto-detect and extract key topics from conversations
- Persistent topic memory storage
- Proactive context recovery in new sessions
- Cross-device memory access

**Use Cases:**
- Continue conversation from phone to computer
- Auto-remind unfinished discussions across days
- Multi-device conversation state sync

#### 2. scheme-confirmation
Scheme confirmation and tracking mechanism - ensures important proposals get user confirmation and tracks execution status.

**Features:**
- Auto-recognize proposals/suggestions in conversations
- Manage proposal lifecycle (proposed → confirmed → executed → completed)
- Remind users to confirm and execute
- Track proposal execution status

**Use Cases:**
- Wait for explicit user confirmation after AI proposes a plan
- Long-term task status tracking
- Avoid "said but forgot to execute" situations

### Quick Start

```bash
# Clone repository
git clone https://github.com/rc8314/openclaw-skills.git
cd openclaw-skills

# Copy skills to OpenClaw directory
mkdir -p ~/.openclaw/skills
cp -r cross-session-memory scheme-confirmation ~/.openclaw/skills/
```

See [docs/installation.md](docs/installation.md) for details.

### Testing

```bash
python3 tests/test_skills.py
```

### Project Status

| Skill | Status | Tests |
|-------|--------|-------|
| cross-session-memory | ✅ Stable | 10+ passed |
| scheme-confirmation | ✅ Stable | 10+ passed |

### Contributing

Issues and PRs are welcome!

### License

MIT License - see [LICENSE](LICENSE)

---

<a name="中文"></a>
## 中文

增强 OpenClaw 的跨会话记忆和方案确认追踪能力。

### 项目概述

两个生产级 Skills，解决 AI 助手在多会话场景下的上下文断层问题。

### Skills 列表

#### 1. cross-session-memory（跨会话记忆）
跨设备话题记忆延续 - 让用户在不同会话间无缝衔接对话上下文。

**核心功能：**
- 自动检测并提取会话中的关键话题
- 持久化存储话题记忆
- 新会话中主动恢复上下文
- 支持跨设备记忆访问

**使用场景：**
- 用户手机聊到一半，换电脑继续
- 跨天对话时自动提醒未完成的讨论
- 多设备同步对话状态

#### 2. scheme-confirmation（方案确认）
方案确认与追踪机制 - 确保重要方案得到用户确认，并追踪执行状态。

**核心功能：**
- 自动识别对话中的方案/建议
- 管理方案生命周期（提出→确认→执行→完成）
- 提醒用户确认和执行
- 追踪方案执行状态

**使用场景：**
- AI 提出方案后，等待用户明确确认
- 长期任务的状态追踪
- 避免"说过了但忘了执行"的情况

### 快速开始

```bash
# 克隆仓库
git clone https://github.com/rc8314/openclaw-skills.git
cd openclaw-skills

# 复制 skills 到 OpenClaw 目录
mkdir -p ~/.openclaw/skills
cp -r cross-session-memory scheme-confirmation ~/.openclaw/skills/
```

详见 [docs/installation.md](docs/installation.md)

### 测试

```bash
python3 tests/test_skills.py
```

### 项目状态

| Skill | 状态 | 测试 |
|-------|------|------|
| cross-session-memory | ✅ 稳定 | 10+ 用例通过 |
| scheme-confirmation | ✅ 稳定 | 10+ 用例通过 |

### 安全性说明

**默认安全模式** - 零隐私风险：
- `safe_mode=true` - 只读取 Skill 自身创建的数据
- `use_legacy_storage=false` - 不访问现有系统文件
- **数据隔离** - 默认只使用 Skill 自身存储路径
- **无 Token 消耗** - 纯本地处理，无 LLM 调用

**可选的兼容模式**（需显式开启）：
```python
# 安全模式（默认）
config = {'safe_mode': True}  # 只读取 skill 创建的数据

# 兼容模式（需用户确认）
config = {'safe_mode': False, 'use_legacy_storage': True}
```

### 兼容性说明

**渐进式启用**：
1. **阶段1**（默认）：完全隔离，只使用 Skill 自身存储
2. **阶段2**：手动创建新话题/方案
3. **阶段3**（可选）：开启兼容模式，读取现有系统数据

### 贡献

欢迎提交 Issue 和 PR！

### 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

**Author/作者**: [rc8314](https://github.com/rc8314)  
**Project/项目**: [openclaw-skills](https://github.com/rc8314/openclaw-skills)
