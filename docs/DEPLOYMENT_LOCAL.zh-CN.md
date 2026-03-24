# 本地部署手册

这份文档用于指导一个执行型 Agent 在 Linux VPS 上完成本项目的非 Docker 部署。

本文默认采用以下部署结构：

- 应用：直接运行在宿主机 Python 虚拟环境中
- 数据库：使用宿主机或现有面板提供的 PostgreSQL
- 反向代理：使用宿主机现有的 Caddy
- 进程托管：使用 `systemd`

如果没有特殊说明，以下命令按 `root` 或具备 `sudo` 权限的用户执行。

## 1. 目标环境

推荐环境：

- 操作系统：Ubuntu 22.04+ 或 Debian 12+
- Python：3.11 或 3.12
- PostgreSQL：14+
- Caddy：已安装并能正常 reload
- Git：已安装

需要对外开放的端口：

- `80`
- `443`

应用端口：

- `8000`

注意：

- `8000` 只监听 `127.0.0.1`，不应直接暴露到公网
- 公网访问统一通过 Caddy 转发

## 2. 部署前准备

在开始之前，先准备好以下信息：

- 站点域名，例如 `tasks.example.com`
- PostgreSQL 地址，默认可用 `127.0.0.1:5432`
- PostgreSQL 数据库名，例如 `taskhub`
- PostgreSQL 用户名，例如 `taskhub`
- PostgreSQL 密码

推荐的项目路径：

```text
/opt/projects/task-exchange-platform
```

推荐的日志与数据归属：

- 代码目录：`/opt/projects/task-exchange-platform`
- 文件存储目录：`/opt/projects/task-exchange-platform/data/files`
- systemd 服务名：`task-exchange-platform`

## 3. 安装系统依赖

Ubuntu / Debian:

```bash
apt update
apt install -y git python3 python3-venv python3-pip libpq-dev
```

验证：

```bash
python3 --version
git --version
```

## 4. 准备 PostgreSQL

如果数据库和用户已经存在，可以直接跳到下一节。

如果需要新建，可参考：

```bash
sudo -u postgres psql
```

在 `psql` 中执行：

```sql
CREATE USER taskhub WITH PASSWORD '<DB_PASSWORD>';
CREATE DATABASE taskhub OWNER taskhub;
```

退出：

```sql
\q
```

验证连接：

```bash
psql "postgresql://taskhub:<DB_PASSWORD>@127.0.0.1:5432/taskhub" -c "select 1;"
```

## 5. 创建运行用户

推荐使用独立系统用户运行服务：

```bash
id -u taskhub >/dev/null 2>&1 || useradd --system --create-home --shell /usr/sbin/nologin taskhub
```

## 6. 获取项目代码

```bash
mkdir -p /opt/projects
git clone https://github.com/clawbie/task-exchange-platform.git /opt/projects/task-exchange-platform
cd /opt/projects/task-exchange-platform
```

如果目录已经存在且是旧版本仓库：

```bash
cd /opt/projects/task-exchange-platform
git pull
```

## 7. 创建虚拟环境并安装依赖

```bash
cd /opt/projects/task-exchange-platform
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 8. 配置环境变量

创建配置文件：

```bash
cd /opt/projects/task-exchange-platform
cp .env.example .env
```

把 `.env` 改成类似下面这样：

```env
APP_NAME=Task Exchange Platform
APP_ENV=production
DEBUG=false
DATABASE_URL=postgresql+psycopg://taskhub:<DB_PASSWORD>@127.0.0.1:5432/taskhub
STORAGE_ROOT=/opt/projects/task-exchange-platform/data/files
MAX_UPLOAD_SIZE_MB=100
AUTO_INIT_DB=false
```

说明：

- `DATABASE_URL` 必须替换成真实密码
- 如果数据库不在本机，把 `127.0.0.1` 改成实际地址
- `AUTO_INIT_DB=false` 表示生产环境只通过 Alembic 迁移建表

## 9. 设置目录权限

```bash
mkdir -p /opt/projects/task-exchange-platform/data/files
chown -R taskhub:taskhub /opt/projects/task-exchange-platform
```

## 10. 执行数据库迁移

```bash
cd /opt/projects/task-exchange-platform
source .venv/bin/activate
alembic upgrade head
```

成功后，数据库中应出现：

- `actors`
- `tasks`
- `task_runs`
- `submissions`
- `files`
- `events`
- `task_packages`
- `api_keys`
- `alembic_version`

## 11. 先做一次手动启动验证

```bash
cd /opt/projects/task-exchange-platform
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另开一个终端验证：

```bash
curl http://127.0.0.1:8000/healthz
curl http://127.0.0.1:8000/readyz
```

预期返回：

```json
{"status":"ok"}
```

和：

```json
{"status":"ready"}
```

如果这一步通过，再继续配置 `systemd`。

## 12. 配置 systemd

创建服务文件：

```bash
cat >/etc/systemd/system/task-exchange-platform.service <<'EOF'
[Unit]
Description=Task Exchange Platform
After=network.target

[Service]
User=taskhub
Group=taskhub
WorkingDirectory=/opt/projects/task-exchange-platform
EnvironmentFile=/opt/projects/task-exchange-platform/.env
ExecStart=/opt/projects/task-exchange-platform/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
```

加载并启动：

```bash
systemctl daemon-reload
systemctl enable --now task-exchange-platform
systemctl status task-exchange-platform --no-pager
```

查看实时日志：

```bash
journalctl -u task-exchange-platform -f
```

## 13. 配置 Caddy

在现有 Caddy 配置中加入：

```caddyfile
tasks.example.com {
  encode gzip
  reverse_proxy 127.0.0.1:8000
}
```

把 `tasks.example.com` 替换成真实域名。

验证配置并重载：

```bash
caddy validate --config /etc/caddy/Caddyfile
systemctl reload caddy
```

## 14. 最终验收

本机验收：

```bash
curl http://127.0.0.1:8000/healthz
curl http://127.0.0.1:8000/readyz
```

公网验收：

- 打开 `https://你的域名/tasks`
- 页面应能看到任务列表
- `https://你的域名/docs` 应能打开 API 文档

建议再检查：

- 创建一个任务
- 上传一个测试附件
- 打开任务详情页

## 15. 常用运维命令

启动服务：

```bash
systemctl start task-exchange-platform
```

停止服务：

```bash
systemctl stop task-exchange-platform
```

重启服务：

```bash
systemctl restart task-exchange-platform
```

查看状态：

```bash
systemctl status task-exchange-platform --no-pager
```

查看日志：

```bash
journalctl -u task-exchange-platform -f
```

## 16. 更新流程

更新代码：

```bash
cd /opt/projects/task-exchange-platform
git pull
```

更新依赖：

```bash
cd /opt/projects/task-exchange-platform
source .venv/bin/activate
pip install -r requirements.txt
```

执行迁移：

```bash
cd /opt/projects/task-exchange-platform
source .venv/bin/activate
alembic upgrade head
```

重启服务：

```bash
systemctl restart task-exchange-platform
```

## 17. 回滚思路

如果更新后异常，优先按下面顺序处理：

1. 查看 `journalctl -u task-exchange-platform -f`
2. 确认 `.env` 是否被误改
3. 回退代码到上一个稳定提交
4. 重新安装依赖
5. 重启服务

代码回退示例：

```bash
cd /opt/projects/task-exchange-platform
git log --oneline -n 5
git checkout <稳定提交号>
source .venv/bin/activate
pip install -r requirements.txt
systemctl restart task-exchange-platform
```

## 18. 常见问题排查

### 18.1 `readyz` 返回 503

通常是以下原因之一：

- 数据库连接串错误
- PostgreSQL 没启动
- `taskhub` 用户没有权限
- 迁移没有执行

优先检查：

```bash
systemctl status task-exchange-platform --no-pager
journalctl -u task-exchange-platform -n 100 --no-pager
psql "postgresql://taskhub:<DB_PASSWORD>@127.0.0.1:5432/taskhub" -c "select 1;"
```

### 18.2 Caddy 访问 502

通常表示 Caddy 无法连接到应用：

- `task-exchange-platform` 服务没起来
- 应用没监听 `127.0.0.1:8000`
- Caddy 配置写错了

检查：

```bash
curl http://127.0.0.1:8000/healthz
systemctl status task-exchange-platform --no-pager
caddy validate --config /etc/caddy/Caddyfile
```

### 18.3 文件上传失败

检查：

- `STORAGE_ROOT` 是否存在
- 服务用户是否对项目目录有写权限
- 磁盘空间是否足够

命令：

```bash
ls -ld /opt/projects/task-exchange-platform
ls -ld /opt/projects/task-exchange-platform/data/files
df -h
```

## 19. 给执行 Agent 的完成标准

部署任务完成后，应满足以下条件：

1. `systemctl status task-exchange-platform` 为运行中
2. `curl http://127.0.0.1:8000/healthz` 返回 `{"status":"ok"}`
3. `curl http://127.0.0.1:8000/readyz` 返回 `{"status":"ready"}`
4. 域名下的 `/tasks` 可以打开
5. 域名下的 `/docs` 可以打开
6. 数据目录和日志查看方式都已确认

如果某一步失败，执行 Agent 不应跳过，而应保留日志并继续排查到可用为止。
