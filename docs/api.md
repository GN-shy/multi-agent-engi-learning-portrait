# API 说明

基础路径：`/api/v1`。Swagger：`http://localhost:8000/docs`。

成功响应统一为：

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "request_id": "request-id"
}
```

业务接口除注册、登录、健康检查、路线目录和集成目录外均需要 Bearer Access Token。Refresh Token 只通过 HttpOnly Cookie 传递。

## 主要接口

| 模块 | 方法与路径 | 用途 |
|---|---|---|
| 系统 | `GET /health` | 版本、领域目录和能力状态 |
| 认证 | `POST /auth/register`、`POST /auth/login` | 注册与登录 |
| 认证 | `POST /auth/refresh`、`POST /auth/logout` | 刷新轮换与退出 |
| 用户 | `GET/PATCH /auth/me` | 当前用户与资料更新 |
| 用户 | `PUT /auth/password` | 修改密码并撤销其它会话 |
| 用户 | `GET /auth/data-export`、`DELETE /auth/me` | 数据导出与账号注销 |
| 路线 | `GET /tracks/tree`、`GET /tracks/{code}` | 路线树、技能图谱和诊断 |
| 路线 | `POST /tracks/compare`、`POST /tracks/select` | 反事实比较与正式选择 |
| 岗位 | `POST /career/jobs/parse` | 从真实 JD 提取可确认的岗位要求 |
| 岗位 | `POST /career/targets`、`GET /career/targets/current` | 确认目标岗位、读取当前目标与技能差距 |
| 画像 | `PUT /profiles/me/analyze` | 生成/更新画像 |
| 画像 | `GET /profiles/me`、`GET /profiles/me/trend` | 当前画像和版本趋势 |
| 知识 | `GET /knowledge/search` | 本地审核知识检索 |
| 知识 | `POST /knowledge/contributions` | 用户贡献知识 |
| 会话 | `POST /sessions` | 运行六 Agent 学习闭环 |
| 会话 | `GET /sessions/{id}` | 会话、轨迹、证据、审计 |
| 会话 | `POST /sessions/{id}/feedback` | 难度/帮助反馈并调路 |
| 资源 | `GET /resources`、`GET /resources/{id}` | 讲义、实操、工作样本测评、计划 |
| 实操 | `POST /practice/{resource_id}/submit` | 提交步骤和运行证据 |
| 测评 | `POST /assessments/{resource_id}/submit` | 结构化工作样本评分；仅合格成果证据按可信度回写画像 |
| 计划 | `GET /plans/current`、`POST /plans/{id}/checkin` | 当前计划与打卡 |
| 计划 | `GET /plans/{id}/workspace` | 目标岗位、成果证据与路线版本工作区 |
| 计划 | `POST /plans/{id}/tasks/{task_id}/evidence` | 提交任务成果并在证据通过后更新画像 |
| 计划 | `POST /plans/{id}/recalibrate` | 根据 JD、难度、阻塞、时间或成果生成待确认路线 |
| 计划 | `POST /plans/{id}/revisions/{revision_id}/decision` | 接受、拒绝或撤销路线版本 |
| 报告 | `GET /reports/latest`、`GET /reports/latest/print` | 数据报告和打印版 |
| 记录 | `GET /records` | 学习活动时间线 |
| 消息 | `GET /notifications`、`PATCH /notifications/{id}/read` | 通知和已读状态 |
| 集成 | `GET/POST /integrations/providers` | 用户外部服务配置 |
| 集成 | `POST /integrations/providers/{id}/test` | 连接测试 |
| 集成 | `GET /integrations/usage` | 请求、Token 和成本统计 |
| 评测 | `GET /evaluation/summary` | 冻结评测集摘要 |
| 评测 | `POST /evaluation/run` | 管理员执行离线可复现实验 |

## 创建学习会话

```json
{
  "track_code": "agent_engineering",
  "goal": "完成一个可评测的多智能体项目",
  "topic": "状态图、工具调用与轨迹评测",
  "source_mode": "knowledge_only",
  "llm_config_id": null,
  "search_config_id": null
}
```

`source_mode` 可取 `knowledge_only`、`knowledge_web`、`knowledge_ai`、`full`。缺少服务、超限、超时或外部响应不合格时，会话记录降级原因并继续使用本地知识和规则生成。

## 密钥约束

创建/更新外部服务时允许提交 `api_key`，之后任何读取接口都只返回脱敏尾号。密钥不会出现在会话、报告、导出、轨迹或错误响应中。

## 路线调整与证据边界

- `checkin.feedback_type` 支持 `normal`、`too_hard`、`too_easy`、`no_time`、`blocked`。非正常反馈只触发一份 `pending` 建议，不直接覆盖当前路线。
- `evidence_type` 支持 `repository`、`commit`、`test`、`deployment`、`document`、`screenshot_note`、`note`。
- URL 与提交哈希的自动结果只代表格式有效；接口会返回 `verification.scope`，不得将其表述成仓库可运行或代码归属已确认。
- 只有达到证据阈值且包含代码、提交、测试、部署或文档等强证据时，才会更新对应技能分与画像版本。

## 工作样本测评

`POST /assessments/{resource_id}/submit` 的 `answers` 以题目 ID 为键，每项包含 `action`、`validation`、`boundary`、`reasoning` 与 `evidence[]`。返回形成性总分、验证后得分、五维评分、证据可信度、完整反馈，以及实际写入画像的 `skill_updates`。

没有达到成果证据门槛时返回 `result_type=formative`，用于提示改进但不创建新的能力画像版本；达到门槛后才按证据强度设置回写权重。仓库和部署地址当前只校验格式，外部真实性仍需 CI、沙箱或人工复核。
