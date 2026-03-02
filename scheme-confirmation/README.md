---
AIGC:
    ContentProducer: Minimax Agent AI
    ContentPropagator: Minimax Agent AI
    Label: AIGC
    ProduceID: "00000000000000000000000000000000"
    PropagateID: "00000000000000000000000000000000"
    ReservedCode1: 3045022066882be99a408609d87d5aec7c93bba640ddaae12e1bc4557298cb850e59f434022100d81d5b1a813acaaf5fd377aae901f204aed006bbe5b44232bb1a64fddd879883
    ReservedCode2: 304402203edadd9533bac64b7be2835df05ade1d31eab149f3eff86ae409ffba2996f43802207d88725b8acf2cfd1407694572fe93a7959309b3042a94a80f4e212cac8a5983
---

# Scheme Confirmation Skill

## 功能描述

方案确认与追踪机制 - 确保重要方案得到用户确认，并追踪执行状态。

## 核心能力

1. **方案识别**: 自动识别对话中的重要方案/建议
2. **确认请求**: 向用户请求明确确认
3. **状态追踪**: 追踪方案的确认和执行状态
4. **提醒机制**: 对未确认/未执行的方案进行提醒

## 方案状态

- `proposed`: 已提出，待确认
- `confirmed`: 已确认，待执行
- `in_progress`: 执行中
- `completed`: 已完成
- `cancelled`: 已取消

## 触发条件

- 检测到方案性内容（包含"建议"、"方案"、"计划"等关键词）
- 用户主动创建方案
- 定时检查未确认方案

## 配置项

```yaml
confirmation_timeout: 3600  # 确认超时时间（秒）
reminder_interval: 7200     # 提醒间隔（秒）
auto_detect: true          # 是否自动检测方案
```
