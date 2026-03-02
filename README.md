---
AIGC:
    ContentProducer: Minimax Agent AI
    ContentPropagator: Minimax Agent AI
    Label: AIGC
    ProduceID: "00000000000000000000000000000000"
    PropagateID: "00000000000000000000000000000000"
    ReservedCode1: 30450221009d10b76dd9f8a5821b265016aa24c125bf41d38596149b519e49a14c9bdcf825022030b6eda7db1034c1b4af3ff492c6196fabcef5ac34a0b74094cdfed92bfb0c69
    ReservedCode2: 30450220550dea07d4bfbb41686329867bd34722e3a574a2a66f3fc010e6021ab4a8ff5f022100f5270e880a87797f0fa23b10677e761504cfa5f286f5547128809e84068d2ea3
---

# OpenClaw Skills - Phase 1-2

## 项目概述

开发两个经典 Skills，增强 OpenClaw 的跨会话记忆和方案确认追踪能力。

## Skills 列表

### 1. cross-session-memory
跨设备话题记忆延续 - 让用户在不同会话间无缝衔接对话上下文。

**核心功能：**
- 自动检测并提取会话中的关键话题
- 持久化存储话题记忆
- 新会话中主动恢复上下文
- 支持跨设备记忆访问

### 2. scheme-confirmation
方案确认与追踪机制 - 确保重要方案得到用户确认，并追踪执行状态。

**核心功能：**
- 自动识别对话中的方案/建议
- 管理方案生命周期（提出→确认→执行→完成）
- 提醒用户确认和执行
- 追踪方案执行状态

## 目录结构

```
openclaw-skills/
├── cross-session-memory/    # 跨会话记忆 Skill
│   ├── skill.yaml           # Skill 定义
│   ├── main.py              # 主逻辑（~350行）
│   └── README.md            # 说明文档
├── scheme-confirmation/     # 方案确认 Skill
│   ├── skill.yaml           # Skill 定义
│   ├── main.py              # 主逻辑（~500行）
│   └── README.md            # 说明文档
├── tests/                   # 测试用例
│   └── test_skills.py       # 完整测试套件
├── docs/                    # 文档
│   └── installation.md      # 安装文档
└── README.md                # 本文件
```

## 快速开始

### 安装

```bash
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

## 状态

- ✅ cross-session-memory: 开发完成，测试通过
- ✅ scheme-confirmation: 开发完成，测试通过
- ✅ 安装文档: 已完成
- ✅ 测试套件: 已完成
