# multi-agent-coordinator

多机器人协作协调器技能。管理多个 Worker 代理，实现任务分配、进度跟踪和结果汇总。

## 架构

```
Coordinator (总协调)
    ↓
Worker 代理池 (4 个)
    ├── worker-finance (财务分析)
    ├── worker-data (数据抓取)
    ├── worker-doc (文档处理)
    └── worker-monitor (监控预警)
```

## 功能

### 1. 任务分发
- 接收用户请求
- 智能分配给合适的 Worker
- 支持并行任务执行

### 2. 进度跟踪
- 实时监控 Worker 状态
- 任务完成度汇报
- 超时预警

### 3. 结果汇总
- 收集各 Worker 输出
- 整合为统一报告
- 返回给用户

## 使用方式

### 通过 sessions_send 分发任务
```python
# 发送任务给 Worker
sessions_send(
    label='worker-finance',
    message='分析 2024 年 4 月 -2026 年 2 月银行对账单'
)
```

### 通过 subagents 管理状态
```python
# 查看所有 Worker 状态
subagents(action='list')

#  steering Worker
subagents(action='steer', target='worker-data', message='优先处理港股数据')
```

## Worker 配置

| Worker | 会话 Label | 核心技能 |
|--------|-----------|----------|
| Finance | worker-finance | finance-scraper, company-analysis |
| Data | worker-data | tavily-search, kimi-fetch |
| Doc | worker-doc | feishu-doc, feishu-wiki |
| Monitor | worker-monitor | cron, healthcheck |

## 任务分配规则

| 任务类型 | 分配给 |
|----------|--------|
| 股价/行情查询 | worker-finance |
| 网络搜索/抓取 | worker-data |
| 文档/知识库 | worker-doc |
| 定时任务/监控 | worker-monitor |
| 复杂多步骤 | 并行分配给多个 Worker |

## 依赖

- OpenClaw sessions 系统
- sessions_send 工具
- subagents 工具

## 版本

v1.0 - 2026.03.13
