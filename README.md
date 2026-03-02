# OpenClaw Skills

[![GitHub](https://img.shields.io/badge/GitHub-rc8314%2Fopenclaw--skills-blue)](https://github.com/rc8314/openclaw-skills)
[![Status](https://img.shields.io/badge/status-stable-success)](https://github.com/rc8314/openclaw-skills)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

增强 OpenClaw 的跨会话记忆和方案确认追踪能力。

## 项目概述

两个生产级 Skills，解决 AI 助手在多会话场景下的上下文断层问题。

## Skills 列表

### 1. cross-session-memory
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

### 2. scheme-confirmation
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

## 目录结构

```
openclaw-skills/
├── cross-session-memory/    # 跨会话记忆 Skill
│   ├── skill.yaml           # Skill 定义
│   ├── main.py              # 主逻辑（~350行）
│   └── README.md            # 详细说明
├── scheme-confirmation/     # 方案确认 Skill
│   ├── skill.yaml           # Skill 定义
│   ├── main.py              # 主逻辑（~500行）
│   └── README.md            # 详细说明
├── tests/                   # 测试用例
│   └── test_skills.py       # 完整测试套件
├── docs/                    # 文档
│   └── installation.md      # 安装文档
└── README.md                # 本文件
```

## 快速开始

### 安装

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
cd /workspace/projects/openclaw-skills
python3 tests/test_skills.py
```

## 技术亮点

1. **模块化设计**：每个 Skill 独立，可单独使用
2. **完整状态管理**：支持状态流转和持久化
3. **自动检测**：智能识别话题和方案
4. **完整测试覆盖**：10+ 测试用例，全部通过

## 项目状态

| Skill | 状态 | 测试 |
|-------|------|------|
| cross-session-memory | ✅ 稳定 | 10+ 用例通过 |
| scheme-confirmation | ✅ 稳定 | 10+ 用例通过 |

## 贡献

欢迎提交 Issue 和 PR！

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

**作者**: [rc8314](https://github.com/rc8314)  
**项目**: [openclaw-skills](https://github.com/rc8314/openclaw-skills)
