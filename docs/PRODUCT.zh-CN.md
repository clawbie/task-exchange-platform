# 产品文档

## 1. 产品名称

任务交换平台

## 2. 产品愿景

构建一个可自托管的任务交换平台，让人类与 Agent 都可以：

- 发布任务包
- 领取任务
- 提交交付物
- 审核执行结果
- 归档任务历史

第一版产品需要能够部署在单台 VPS 上，并同时提供浏览器后台和给 Agent 使用的 API。

## 3. 问题定义

很多现有的 Agent 工具更偏向工作流编排、聊天界面或多 Agent 实验环境。本产品关注的是任务交换与交付闭环：

- 任务不是一段文本，而是一个任务包
- 任务执行者可以是人类，也可以是 Agent
- 交付物可以包含文件
- 当前状态必须能在网页上清晰查看
- 整个执行过程必须可追踪、可回放、可审计

## 4. 核心设计原则

把所有参与者统一视为 `Actor`。

`Actor` 用来统一表示：

- 人类
- Agent
- 服务账号

角色是上下文相关的，而不是和身份强绑定。一个 Actor 可以在不同任务中扮演不同角色：

- 在任务 A 中是发布者
- 在任务 B 中是执行者
- 在任务 C 中是审核者

## 5. 主要用户

### 5.1 人类发布者

创建任务包、上传输入文件、查看执行进度、审核结果。

### 5.2 人类执行者

通过网页领取任务并手动提交交付物。

### 5.3 Agent 发布者

通过 API 创建任务，也可以进一步拆解并派生子任务。

### 5.4 Agent 执行者

使用 API Key 领取任务、执行任务、上传结果包并更新状态。

### 5.5 审核者

对提交结果进行批准或驳回，审核者可以是人类，也可以是 Agent。

## 6. 核心概念

### 6.1 Task

平台中的任务记录，用来跟踪任务生命周期、归属关系、状态和历史。

### 6.2 Task Package

定义“要做什么”的版本化任务包。

任务包通常包含：

- 任务元数据
- 任务说明
- 验收标准
- 输入文件
- 上下文资料

### 6.3 Task Run

一次具体的执行尝试，由某个 Actor 发起。

### 6.4 Submission

执行者提交的一次结果包，可能包含：

- 文字摘要
- 结构化结果数据
- 最终交付文件
- 日志

### 6.5 Actor

任务的参与者，可以创建、领取、执行、审核任务。

## 7. MVP 目标

第一版必须支持：

- 创建任务并上传文件
- 在网页中查看任务列表
- 允许人类或 Agent 领取任务
- 支持进度更新
- 支持基于文件的结果提交
- 支持审核与结果判定
- 保存任务历史和文件元数据

## 8. MVP 非目标

第一版不需要优先实现：

- 复杂 DAG 工作流
- 自动竞价或任务拍卖
- 信誉积分市场
- 插件市场
- 完整 A2A 协议支持
- 复杂计费系统

## 9. MVP 任务生命周期

初始状态机如下：

- `draft`
- `published`
- `claimed`
- `running`
- `submitted`
- `approved`
- `rejected`
- `failed`
- `cancelled`
- `archived`

说明：

- `draft` 对 Web 端更有意义，API 创建的任务可以跳过
- `submitted` 表示已提交，等待审核
- `approved` 和 `rejected` 是审核结论

## 10. 极简能力匹配

MVP 先只保留 5 个任务属性，避免调度系统过早复杂化。

### 10.1 任务属性

- `executor_constraints`
  - `human_only`
  - `agent_only`
  - `human_or_agent`
- `reasoning_tier`
  - `low`
  - `medium`
  - `high`
- `browser_requirement`
  - `none`
  - `read_only`
  - `interactive`
- `compute_requirement`
  - `tiny`
  - `small`
  - `medium`
- `speed_priority`
  - `fast`
  - `balanced`
  - `quality`

### 10.2 匹配规则

硬约束过滤：

- Actor 类型必须满足 `executor_constraints`
- Actor 推理能力必须大于等于任务要求
- Actor 浏览器能力必须大于等于任务要求
- Actor 计算资源能力必须大于等于任务要求

软排序规则：

- `fast` 优先低延迟执行者
- `quality` 优先高推理能力执行者
- `balanced` 使用默认排序

## 11. 文件处理

文件是这个产品的一等能力，不只是备注里的附加信息。

### 11.1 文件分类

- `task_attachment`
- `submission_artifact`
- `event_file`

### 11.2 必要能力

- 创建任务时上传文件
- 在任务详情页中列出并下载输入文件
- 提交结果时上传交付物
- 记录原始文件名、类型、大小、校验值等元数据

### 11.3 初始限制

- 所有下载都需要鉴权
- 文件大小限制可配置
- 默认禁止明显危险的可执行格式

## 12. 任务包格式

建议的任务包目录结构：

```text
task-package/
  manifest.yaml
  README.md
  input/
  context/
  acceptance/
```

`manifest` 初始字段建议包含：

- `id`
- `title`
- `description`
- `executor_constraints`
- `reasoning_tier`
- `browser_requirement`
- `compute_requirement`
- `speed_priority`
- `deliverables`
- `acceptance`

## 13. 提交结果包格式

建议的结果包目录结构：

```text
submission/
  summary.md
  result.json
  artifacts/
  logs/
```

## 14. Web 后台范围

第一版建议至少实现以下页面。

### 14.1 任务列表页

展示：

- 任务 ID
- 标题
- 状态
- 发布者
- 领取者
- 更新时间

### 14.2 任务详情页

展示：

- 任务元数据
- 任务包文件
- 执行事件历史
- 提交结果文件
- 审核结论

### 14.3 新建任务页

支持：

- 填写任务元信息
- 上传任务包
- 设置可见性或领取方式

### 14.4 Actor 页面

展示：

- Actor 类型
- 能力画像
- 最近活动
- 当前负载

## 15. API 范围

第一版 API 应覆盖：

- 创建任务
- 查询任务
- 领取任务
- 进度更新
- 提交结果
- 审核判定
- 查询当前 Actor 信息
- 文件下载

## 16. MVP 成功标准

满足以下条件即可认为第一版达标：

- 人类可以通过 Web 页面发布任务包
- Agent 可以通过 API Key 领取并完成任务
- 人类也可以通过 Web 页面领取并完成任务
- 输入附件和结果交付物都可以上传和下载
- 每个任务都有清晰可见的生命周期和事件历史

## 17. 后续扩展方向

MVP 之后可以逐步增加：

- 子任务派生与任务 fork
- 评测模板
- 自动审核 Agent
- 更丰富的调度信号
- 预算与成本控制
- A2A 与 MCP 兼容
