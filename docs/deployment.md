# 部署说明

## 1. 环境要求

- 本地开发：Python 3.11+、Node.js 20+
- 容器部署：Docker 24+、Docker Compose v2+

## 2. 本地开发

后端：

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

前端：

```powershell
cd frontend
npm ci
npm run dev
```

访问地址：

- 前端：`http://localhost:5173`
- Swagger：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/api/v1/health`

## 3. Docker Compose

复制配置：

```bash
cp .env.example .env
```

生产必填：

```dotenv
DB_PASSWORD=使用强随机数据库密码
JWT_SECRET=使用至少32位的强随机字符串
```

如需后端加密保存用户密钥，还要设置 `BYOK_MASTER_KEY`。未设置时仍可使用临时密钥模式。

启动：

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f gateway
```

更新版本时先备份数据库，再拉取代码并执行 `docker compose up -d --build`。后端入口会自动执行 `alembic upgrade head`。

## 4. 治理账号

系统没有默认管理员口令。需要治理端时设置：

```dotenv
BOOTSTRAP_ADMIN_EMAIL=admin@example.com
BOOTSTRAP_ADMIN_USERNAME=治理管理员
BOOTSTRAP_ADMIN_PASSWORD=至少12位强密码
```

首次启动会创建或提升该账号；删除环境变量不会删除已有账号。

## 5. 上线检查

- `.env` 未提交到版本库，密钥和密码均为强随机值。
- CORS 只包含正式前端域名，全站使用 HTTPS。
- `pytest`、`ruff` 和 `npm run build` 通过。
- Alembic 能从空库升级到 `head`。
- 反向代理限制请求体大小、连接超时和访问频率。
- 备份与恢复流程经过验证。
- 外部模型/搜索连接由用户自行测试，失败不会阻断核心学习闭环。

## 6. 数据与恢复

开发环境默认使用 `data/gongxue_v1.db`。生产 PostgreSQL 使用 `pgdata` 卷。不要用 `docker compose down -v` 作为普通停止命令，因为它会删除生产数据库卷。
