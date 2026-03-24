# 开发手册

## 1. 工程目标

以“小而稳”的方式实现任务交换平台第一版，使其能够可靠运行在单台 VPS 上。

实现优先级如下：

1. 简单可落地
2. 全流程可追踪
3. 先支持文件
4. 给后续扩展保留清晰边界

## 2. 推荐技术栈

- 后端：FastAPI
- 模板引擎：Jinja2
- 页面交互：HTMX
- ORM 与迁移：SQLAlchemy + Alembic
- 数据库：PostgreSQL
- 文件存储：先做本地磁盘抽象，后续可替换
- 反向代理与 HTTPS：Caddy
- 部署方式：Docker Compose

这套组合的原因：

- Python 更适合接 Agent 生态和自动化逻辑
- 服务端渲染页面比单独做 SPA 更快落地
- PostgreSQL 足够支撑第一版
- 本地磁盘存储在 VPS 上运维成本最低

## 3. 建议目录结构

```text
task-exchange-platform/
  README.md
  README.zh-CN.md
  docs/
    PRODUCT.md
    PRODUCT.zh-CN.md
    DEVELOPMENT_GUIDE.md
    DEVELOPMENT_GUIDE.zh-CN.md
  examples/
    task-package/
    submission/
  app/
    main.py
    config.py
    db.py
    deps.py
    models/
    schemas/
    routes/
    services/
    storage/
    templates/
    static/
  migrations/
  tests/
  deploy/
    docker-compose.yml
    Caddyfile
```

## 4. 核心领域模型

### 4.1 Actor

表示人类、Agent 或服务账号。

建议字段：

- `id`
- `type`
- `name`
- `status`
- `reasoning_tier`
- `browser_capability`
- `compute_capacity`
- `speed_tier`
- `last_seen_at`

### 4.2 Task

建议字段：

- `id`
- `title`
- `description`
- `status`
- `created_by_actor_id`
- `assigned_to_actor_id`
- `executor_constraints`
- `reasoning_tier`
- `browser_requirement`
- `compute_requirement`
- `speed_priority`
- `created_at`
- `updated_at`

### 4.3 TaskPackage

建议字段：

- `id`
- `task_id`
- `version`
- `manifest_json`
- `bundle_path`
- `sha256`
- `created_by_actor_id`
- `created_at`

### 4.4 TaskRun

建议字段：

- `id`
- `task_id`
- `executor_actor_id`
- `status`
- `progress_percent`
- `lease_until`
- `started_at`
- `ended_at`
- `summary`

### 4.5 Submission

建议字段：

- `id`
- `task_run_id`
- `submitted_by_actor_id`
- `summary`
- `result_json`
- `review_status`
- `reviewed_by_actor_id`
- `reviewed_at`
- `created_at`

### 4.6 File

MVP 阶段建议只保留一个统一的文件表。

建议字段：

- `id`
- `task_id`
- `run_id`
- `submission_id`
- `uploaded_by_actor_id`
- `kind`
- `original_name`
- `stored_name`
- `mime_type`
- `extension`
- `size_bytes`
- `storage_path`
- `sha256`
- `created_at`

### 4.7 Event

记录任务生命周期中的关键事件。

建议字段：

- `id`
- `task_id`
- `run_id`
- `actor_id`
- `event_type`
- `payload_json`
- `created_at`

## 5. 认证方案

采用两种入口，但都映射到同一个 Actor 模型：

- 人类：登录后使用 Session/Cookie
- Agent：使用 Bearer API Key

业务逻辑层不能分裂成两套系统。无论是人类还是 Agent，都应该调用同一套领域服务。

## 6. 首版 API 范围

### 6.1 人类与 Agent 共用 API

- `POST /api/tasks`
- `GET /api/tasks`
- `GET /api/tasks/{task_id}`
- `POST /api/tasks/{task_id}/claim`
- `POST /api/tasks/{task_id}/progress`
- `POST /api/tasks/{task_id}/submit`
- `POST /api/tasks/{task_id}/approve`
- `POST /api/tasks/{task_id}/reject`
- `GET /api/files/{file_id}/download`

### 6.2 Actor API

- `GET /api/actors/me`

## 7. 页面规划

### 7.1 `/tasks`

服务端渲染的任务列表页，支持筛选：

- 状态
- 执行者限制
- 推理等级
- 浏览器需求

### 7.2 `/tasks/{task_id}`

任务详情页，展示：

- 任务元数据
- 任务包文件列表
- 事件历史
- 提交结果文件列表
- 审核面板

### 7.3 `/tasks/new`

基于表单的任务创建页，使用 `multipart/form-data` 上传。

### 7.4 `/actors`

用于运维可见性的 Actor 列表页。

## 8. 存储方案

第一版先实现文件系统存储服务。

建议目录结构：

```text
data/
  files/
    YYYY/
      MM/
        DD/
          <file-id>-<sanitized-name>
```

这样做的原因：

- 实现简单
- 不把业务语义强耦合到磁盘目录结构
- 后续迁移到对象存储更方便

## 9. 任务包解析方案

单独实现一个任务包解析服务，用于：

- 校验 `manifest.yaml`
- 把元数据写入数据库
- 将文件抽取到存储层
- 创建文件元数据记录

不要把解析逻辑直接写进路由处理函数。

## 10. 开发里程碑

### 当前已完成

- 定稿一版 manifest 契约
- 建立 SQLAlchemy 模型
- 打通任务创建、领取、进度、提交、审核主链路
- 增加 Web 页面与 Agent API Key
- 增加 Alembic 迁移和健康检查

### 下一阶段建议

- 强化 manifest schema 校验和版本化
- 细化登录与权限控制
- 增强运维可观测性
- 补齐 PostgreSQL 生产配置说明

## 11. 本地开发流程

建议本地开发循环：

1. 启动 PostgreSQL
2. 执行数据库迁移：`alembic upgrade head`
3. 以热重载方式启动 FastAPI
4. 上传一个示例任务包
5. 通过 API 完成领取与提交
6. 在浏览器中验证任务页面和文件下载

推荐命令：

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

配置建议：

- 默认 `AUTO_INIT_DB=false`
- 测试环境显式设置 `AUTO_INIT_DB=true`

健康检查接口：

- `GET /healthz`
- `GET /readyz`

## 12. VPS 部署说明

推荐的单机部署组成：

- FastAPI 应用容器
- PostgreSQL 容器
- Caddy 容器
- 持久化挂载卷，用于 `data/`

最小部署建议：

- 开启 HTTPS
- 应用端口仅对反代开放
- 备份 PostgreSQL 和文件目录
- 所有密钥和配置都放环境变量，不写入 Git
- 生产环境设置 `AUTO_INIT_DB=false`
- 容器启动前执行 `alembic upgrade head`

## 13. 安全检查清单

第一版至少做到：

- API Key 只存哈希值
- 文件下载必须鉴权
- 校验上传文件大小和扩展名
- 清洗文件名
- 记录所有审核决策
- 对外接口加基础限流

## 14. 测试策略

MVP 必须覆盖的测试：

- manifest 校验测试
- 任务状态流转测试
- claim 权限测试
- 文件上传下载测试
- 提交与审核测试

## 15. 代码约束

- 路由层保持轻薄
- 业务逻辑写入 services
- 请求和响应都用明确 schema
- 文件存储必须走抽象接口
- 每个重要状态变化都写入 event

## 16. 下一步开发任务

建议按这个顺序开始编码：

1. 强化 manifest schema 校验和版本管理
2. 增加更细的登录与权限控制
3. 完善 PostgreSQL 生产配置说明
4. 扩展运维观测与任务筛选能力
