---
AIGC:
    ContentProducer: Minimax Agent AI
    ContentPropagator: Minimax Agent AI
    Label: AIGC
    ProduceID: "00000000000000000000000000000000"
    PropagateID: "00000000000000000000000000000000"
    ReservedCode1: 3046022100ffe90cb1a5e7b0ffc01a12f3e56992702cdecc05da653784b2dc6cb3e174a40c02210092e1283be7fff0a3330af90edee90e5257dae3d500de55377933b42a3fd30abf
    ReservedCode2: 3045022100c49b876be476b8fbecb787fbcc9f83d6b73ff0e7e505164c67f0e7c80dab9e3c022038ca1b0acc675a2eb5654ff012302bd1ba1e07cfc3c0069f6c468655b4762d9d
---

# Scheme Confirmation Skill

> 解决 AI 协作中"方案确认"与"实际执行"之间的信息断层问题
> 版本: 1.0.0
> 适用 OpenClaw: >= 2026.2.x

---

## 一句话描述

让 AI 像专业项目经理一样管理你的任务：方案确认、执行追踪、主动提醒、失败复盘。

---

## 痛点场景

### 场景1: 方案确认后执行断层
```
你: "帮我设计一个定时任务方案"
AI: "提供3个方案：A高频/B中频/C低频"
你: "确认方案B"
AI: "好的"

[3天后]
你: "那个定时任务方案执行了吗？"
AI: "什么方案？"
你: "...就是前几天确认的"
AI: "抱歉，我不记得了"
```

### 场景2: 执行结果无法追溯
```
你: "上周让你配置的服务器怎么样了？"
AI: "好像配置过了...或者没有..."
你: "到底有没有？出错了还是成功了？"
AI: "抱歉，没有记录"
```

### 场景3: 同类错误反复出现
```
[第一次]
AI: "API Key 配置错了，任务失败"
[第二次] 
AI: "API Key 配置错了，任务失败"
[第三次]
AI: "API Key 配置错了，任务失败"
你: "怎么又是这个问题？！"
```

---

## 解决方案

建立"确认-追踪-执行-复盘"的完整闭环：

```
方案确认 ──▶ 归档到 plans/ ──▶ 追踪到 pending ──▶ 等待执行
    │                              │                    │
    │                              │                    ▼
    │                              │            用户说"执行"
    │                              │                    │
    │                              ▼                    ▼
    │                         主动提醒（24h）    执行并记录
    │                              │                    │
    │                              ▼                    ▼
    │                         用户说"先放一放"   更新 execution-logs/
    │                              │                    │
    │                              ▼                    ▼
    └─────────────────────── 暂缓，基于记忆 ◀── 成功/失败
                               主动提醒重启            │
                                                    失败写入
                                                   anti-capsule/
```

---

## 核心特性

### 1. 方案必归档
- 任何确认的方案立即写入 `plans/`
- 明确标注执行状态
- 拒绝口头承诺，只看文件记录

### 2. 执行必追踪
- 待处理事项自动加入 `.pending-schemes.json`
- 24小时无响应主动提醒
- 7天无响应自动归档

### 3. 结果必验证
- 执行后提供可验证凭证（任务ID/文件路径）
- 用户可独立核查
- 失败立即记录，不隐藏

### 4. 失败必复盘
- 错误写入 `anti-capsule.md`
- 提取失败模式
- 机制自我完善

---

## 安装

### 方式1: OpenClaw CLI（推荐）
```bash
openclaw skills add scheme-confirmation
```

### 方式2: 手动安装
```bash
git clone https://github.com/your-repo/openclaw-skills.git
cd openclaw-skills/scheme-confirmation
./install.sh
```

---

## 配置

### 默认配置 (config.json)
```json
{
  "confirmation": {
    "auto_archive": true,
    "archive_after_days": 7
  },
  "execution": {
    "require_explicit_trigger": true,
    "default_timeout": 300
  },
  "reminder": {
    "enabled": true,
    "first_reminder_hours": 24,
    "max_reminders": 3
  },
  "review": {
    "on_failure": true,
    "update_anti_capsule": true,
    "update_soul_md": true
  },
  "states": {
    "waiting_command": {
      "label": "等待命令",
      "color": "yellow",
      "action": "加入追踪列表"
    },
    "ready": {
      "label": "准备就绪",
      "color": "green",
      "action": "可立即执行"
    },
    "dependency_pending": {
      "label": "有依赖待解决",
      "color": "orange",
      "action": "等待依赖完成"
    },
    "deferred": {
      "label": "暂缓",
      "color": "blue",
      "action": "基于记忆主动提醒"
    }
  }
}
```

### 状态机配置

你可以自定义状态流转规则：

```json
{
  "transitions": [
    {
      "from": "waiting_command",
      "trigger": "用户说'执行'",
      "to": "in_progress"
    },
    {
      "from": "waiting_command",
      "trigger": "用户说'先放一放'",
      "to": "deferred"
    },
    {
      "from": "dependency_pending",
      "trigger": "依赖解决",
      "to": "ready"
    }
  ]
}
```

---

## 使用方式

### 基础用法

#### 1. 方案确认
```
你: "帮我设计一个定时任务方案"
AI: "提供3个方案：
    A. 高频检查（每30分钟）
    B. 中频检查（每2小时）  
    C. 低频检查（每4小时）
    请选择"

你: "选B"
AI: "确认选择方案B（每2小时检查）？"

你: "确认"
AI: "方案已归档: plans/2026-03-01-cron.md
    执行状态: 等待命令
    输入'执行'开始实施"
```

#### 2. 执行触发
```
你: "执行"
AI: "开始执行方案B...
    [执行任务1]
    [执行任务2]
    ✅ 执行完成
    证据: job_id=xxx
    验证命令: openclaw cron list
    日志: execution-logs/2026-03-01-cron.json"
```

#### 3. 暂缓与提醒
```
你: "这个先放一放"
AI: "方案已归档，状态: 暂缓
    我会在合适时机主动提醒你"

[一周后]
AI: "关于之前暂缓的定时任务方案，
    这周工作节奏是否适合实施？"
```

### 高级用法

#### 查看待处理事项
```
你: "有哪些待处理方案？"
AI: "你有3个待处理方案：
    
    1. [等待命令] 定时任务重建
       确认时间: 3天前
       
    2. [暂缓] 学习资料整理
       已暂缓: 1周
       
    3. [有依赖] 数据库迁移
       等待: 账号权限
       
    输入编号查看详情"
```

#### 查看执行历史
```
你: "查看昨天的执行记录"
AI: "2026-03-01 执行记录：
    
    ✅ 成功:
    - 定时任务创建 (job_id=xxx)
    - 脚本路径修复
    
    ❌ 失败:
    - 邮件配置更新 (API Key 过期)
      已记录: execution-logs/xxx-failed.md
      建议: 更新163邮箱授权码"
```

---

## 文件结构

安装后生成的文件：

```
你的工作区/
├── plans/
│   ├── README.md                    # 机制说明
│   ├── 2026-03-01-cron.md           # 具体方案1
│   ├── 2026-03-02-backup.md         # 具体方案2
│   └── mechanism-improvement-       # 机制完善模板
│       template.md
│
├── execution-logs/
│   ├── 2026-03-01-cron.json         # 执行日志1
│   ├── 2026-03-01-cron-failed.md    # 失败复盘1
│   └── 2026-03-02-backup.json       # 执行日志2
│
├── .execution-state.json            # 当前执行状态
├── .pending-schemes.json            # 待处理追踪
└── anti-capsule.md                  # 失败经验库
```

---

## 工作原理

### 方案确认流程

```python
def confirm_scheme(user_input, scheme_content):
    # 1. 创建方案文件
    plan_file = create_plan_file(scheme_content)
    
    # 2. 判断执行状态
    if has_dependency(scheme_content):
        status = "有依赖待解决"
    elif user_said_execute_now(user_input):
        status = "准备就绪"
    else:
        status = "等待命令"
    
    # 3. 写入文件
    write_plan_file(plan_file, {
        'content': scheme_content,
        'status': status,
        'confirmed_at': now()
    })
    
    # 4. 如需要，加入追踪
    if status == "等待命令":
        add_to_pending_schemes(plan_file)
    
    return f"方案已归档: {plan_file}, 状态: {status}"
```

### 执行触发判定

```python
def should_execute_now(user_input, plan_status):
    triggers = {
        "确认，执行": True,
        "去做": True,
        "马上执行": True,
        "确认这个方案": False,  # 仅确认，不执行
        "先放一放": False,      # 暂缓
        "都不好": False         # 废弃
    }
    
    # 模糊表述需确认
    if user_input in ["确认", "好的"]:
        return ask_for_clarification()
    
    return triggers.get(user_input, False)
```

### 主动提醒机制

```python
def check_pending_schemes():
    pending = load('.pending-schemes.json')
    
    for item in pending:
        age = now() - item['created_at']
        
        # 24小时后首次提醒
        if age > 24h and item['reminder_count'] == 0:
            send_reminder(item)
            item['reminder_count'] += 1
        
        # 7天后自动归档
        if age > 7d:
            archive_item(item)
            
    save(pending)
```

---

## 核心概念

### 1. "确认"≠"执行"

| 用户表述 | 含义 | AI动作 |
|---------|------|--------|
| "确认，执行" | 认可方案 + 立即执行 | 归档 + 执行 |
| "确认这个方案" | 仅认可方案内容 | 归档，等待执行命令 |
| "先放一放" | 认可方案，时机未到 | 归档为"暂缓" |
| "都不好" | 方案被拒绝 | 废弃，重新设计 |

### 2. 暂缓 vs 取消

- **暂缓**: 方案内容OK，以后可能做 → 归档 + 主动提醒
- **取消**: 需求不存在了 → 废弃 + 不追踪

### 3. 失败经验的价值

不是记录"我错了"，而是记录：
- 失败模式（什么情况下会失败）
- 根因分析（为什么会失败）
- 预防措施（下次如何避免）
- 快速恢复（失败时如何处理）

---

## 与其他 Skill 的协作

| Skill | 协作方式 | 效果 |
|-------|----------|------|
| cross-session-memory | 跨设备查看待确认方案 | 手机上看电脑端确认的方案 |
| remind-me | 基于方案设置提醒 | "明天执行方案X" |
| daily-digest | 汇总今日方案确认/执行情况 | 日报包含方案进展 |
| anti-capsule | 提取失败模式更新检查清单 | 工作前自动提醒注意事项 |

---

## 故障排除

### 问题1: 方案确认后找不到
**现象**: 确认方案后，查询"待处理方案"找不到

**排查**:
```bash
ls -la plans/
cat .pending-schemes.json
```

**原因**: 
- 可能状态是"准备就绪"（不需要追踪）
- 或已自动归档（超过7天）

### 问题2: 提醒太频繁/太少
**解决**: 调整配置
```json
{
  "reminder": {
    "first_reminder_hours": 48,  // 改为48小时
    "max_reminders": 1           // 只提醒1次
  }
}
```

### 问题3: 状态流转不符合预期
**解决**: 自定义状态机（见高级配置）

---

## 最佳实践

### 1. 明确表达意图
- ✅ "确认方案，现在执行"
- ✅ "确认这个方案，等我命令"
- ✅ "这个先放一放，下周再说"
- ❌ "好的" （太模糊，AI需要询问）

### 2. 定期查看待处理
```
你: "有哪些待处理方案？"
```
建议每周查看一次，避免遗漏。

### 3. 主动使用复盘
失败时，不只是"重试"：
```
你: "为什么又失败了？"
AI: "[展示 anti-capsule 中的相关记录]
    这是第3次出现 API Key 问题。
    建议：配置 Key 时同时设置过期提醒"
```

---

## 路线图

### Phase 1 (当前)
- ✅ 方案确认与归档
- ✅ 执行状态追踪
- ✅ 待处理事项提醒

### Phase 2 (计划中)
- 🚧 可视化看板（Web UI 展示方案状态）
- 🚧 甘特图（时间线视图）
- 🚧 协作模式（多用户共同追踪）

### Phase 3 (未来)
- 📋 AI 主动建议（"你好像想继续方案X"）
- 📋 自动化执行（满足条件自动触发）
- 📋 集成第三方（Jira、Notion、飞书项目）

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

*基于真实协作痛点设计，经过生产环境验证*
