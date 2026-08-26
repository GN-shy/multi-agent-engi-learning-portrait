# 工学智链

面向计算机学习与职业发展的个性化成长平台。系统覆盖 16 个主方向、29 条细分技术路线，包含前端、后端、全栈、Agent 全栈、LLM 应用、算法、数据工程、测试、DevOps、安全、嵌入式、UI/UX 等方向，把“方向迷茫、路径不清、内容不可信、学完不会做、反馈不闭环”转化为可解释、可执行、可评测的学习过程。

## 已实现能力

- 计算机领域三大方向簇、16 个主方向、29 条细分技术路线、技能依赖图谱与代表项目。
- 最多组合 6 条路线，自动去重公共基础、按前置关系重排，并把阶段主题拆成具体周次、知识点、动手/故障练习、搜索词、权威资料入口、成果证据和验收标准。
- 每条细分路线展示对应岗位、工作内容、市场薪资参考、学历竞争力、市场判断和求职作品集要求。
- 支持粘贴真实招聘 JD，确定性提取岗位、城市、学历、经验、薪资原文、职责与技术栈；用户确认后生成岗位能力差距和路线调整建议。
- 五态学情建模、六维能力画像、技能盲区和版本化成长趋势。
- 路线反事实对比、匹配依据和正式选择。
- 多智能体协作：学情建模、知识检索、双策略生成、仲裁审核、导学交互。
- 个性化讲义、项目实操、工作样本测评、学习计划、成长报告和学习记录。
- 工作样本测评采用“实施方案、验收验证、失败处理、技术取舍、成果证据”五部分结构；未达到证据门槛的回答只形成反馈，不抬高能力画像。
- 本周任务工作台、学习状态反馈、成果举证、测试成绩回写画像、计划版本比较、接受/拒绝/撤销与消息通知。
- 成果可提交仓库、提交哈希、测试、部署或文档证据；系统明确区分格式校验、自动校验与仍需人工/沙箱复核的范围。
- 本地知识审核、来源版本、段落引用、仲裁证据和质量指标。
- AI 增强内容先拆成原子主张，再核验有效引用、原文证据片段、数字/技术实体与语义重合；不支持主张直接拦截，系统指标与人工盲测幻觉率分开呈现。
- BYOK 模型/搜索网关、临时或加密密钥、连接测试、限额、预算和安全降级。
- 用户数据导出、密码更新、账号注销和治理端冻结评测。

## 技术栈

| 层级 | 实现 |
|---|---|
| 前端 | Vue 3、TypeScript、Pinia、Element Plus、ECharts、Vite |
| 后端 | FastAPI、SQLAlchemy、Pydantic、Alembic |
| 数据 | 本地 SQLite 开发；PostgreSQL 生产 |
| 外部能力 | OpenAI-compatible LLM 网关；Tavily、Serper、自定义搜索 |
| 部署 | Docker Compose、Nginx、Uvicorn |

## 本地启动

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

访问 `http://localhost:5173`。演示账号：`demo@gongxue.local` / `demo12345`。生产环境必须配置独立的 `JWT_SECRET`，不得使用演示账号承载真实数据。

## 生产部署

复制 `.env.example` 为 `.env`，至少设置 `DB_PASSWORD` 和长度不少于 32 位的随机 `JWT_SECRET`，再执行：

```bash
docker compose up -d --build
```

外部模型和联网搜索不是核心功能的启动前提；用户可登录后在“AI 与搜索”页面按需配置自己的服务。

## 验证

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest
.\venv\Scripts\python.exe -m ruff check app tests

cd ..\frontend
npm run build
```

详细操作、演示流程、痛点映射和排障方法见 [SOP_功能操作与比赛痛点说明.md](./SOP_功能操作与比赛痛点说明.md)。架构、API 与部署说明位于 `docs/`。
