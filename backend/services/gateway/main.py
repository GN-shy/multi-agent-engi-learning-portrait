"""兼容入口。

正式实现已经迁移到模块化单体 ``app.main``。保留此模块仅避免旧启动命令失效。
"""

from app.main import app


# 旧版文件以下内容不再执行。
__legacy_source__ = r'''

import json, logging, uuid
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from shared.schemas import *
from shared.config import settings, DEMO_MODE

logger = logging.getLogger("gateway")
app = FastAPI(title="工学智链 API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

if DEMO_MODE:
    logger.info("=== Demo模式已激活，使用规则引擎生成内容 ===")

_ws: dict[str, WebSocket] = {}
_sessions: dict[str, SessionResult] = {}
_users: dict[str, dict] = {"demo": {"id":"u001","username":"用户昵称","password":"demo123","email":"user@example.com","phone":"","avatar":"","role":"student"}}
_tokens: dict[str, str] = {}

# ==================== 工具函数 ====================
def uid(): return uuid.uuid4().hex[:12]
def now(): return datetime.now().isoformat()
def ok(data=None): return APIResponse(data=data or {})
def err(code: int, msg: str): return APIResponse(code=code, message=msg)

# ==================== 用户认证 ====================
@app.post("/api/v1/user/register")
async def user_register(body: dict):
    un = body.get("username",""); pw = body.get("password","")
    if not un or not pw: return err(1001, "用户名和密码不能为空")
    if un in _users: return err(1001, "用户已存在")
    _users[un] = {"id":uid(),"username":un,"password":pw,"email":body.get("email",""),"phone":body.get("phone",""),"avatar":"","role":"student","learning_direction":[],"learning_mode":"balanced"}
    return ok({"message":"注册成功","username":un})

@app.post("/api/v1/user/login")
async def user_login(body: dict):
    account = body.get("account",""); pw = body.get("password","")
    user = _users.get(account)
    if not user or user["password"] != pw: return err(1001, "账号或密码错误")
    token = uid() + uid()
    _tokens[token] = account
    return ok({"token":token,"username":user["username"],"avatar":user.get("avatar",""),"user_id":user["id"]})

@app.get("/api/v1/user/info")
async def user_info():
    return ok({"id":"u001","username":"用户昵称","email":"user@example.com","phone":"","avatar":"","role":"student","learning_direction":["Java开发"],"learning_mode":"balanced","created_at":"2026-07-01"})

@app.put("/api/v1/user/update")
async def user_update(body: dict):
    return ok({"message":"用户信息已更新"})

# ==================== Dashboard ====================
@app.get("/api/v1/dashboard")
async def dashboard():
    return ok({
        "user": {"username":"用户昵称","avatar":"","level":"Lv5","level_label":"高级工程学习者"},
        "study_time": {"today":2.5,"total":128},
        "ability_score": {"score":86,"change":8,"gauge_data":86},
        "knowledge_rate": {"overall":82,"details":[{"name":"Java","rate":90},{"name":"数据库","rate":78},{"name":"AI","rate":65},{"name":"算法","rate":80}]},
        "resource_count": {"total":36,"lecture":12,"practice":8,"test":10,"report":6},
        "agent_status": {"running":4,"total":6},
        "today_tasks": [
            {"title":"完成SpringBoot实践第3章：RESTful API设计","done":False,"priority":"high"},
            {"title":"Java集合框架源码分析：HashMap实现原理","done":False,"priority":"high"},
            {"title":"完成一道LeetCode算法题（动态规划）","done":True,"priority":"normal"},
        ],
        "learning_path": [
            {"title":"基础学习","desc":"Java/Python/数据库","progress":100,"status":"completed"},
            {"title":"能力提升","desc":"SpringBoot/微服务/算法","progress":65,"status":"active"},
            {"title":"项目实践","desc":"企业级项目/开源贡献","progress":20,"status":"pending"},
            {"title":"综合训练","desc":"系统设计/架构能力","progress":0,"status":"pending"},
        ],
        "radar_data": {"dimensions":["理论基础","工程实践","创新能力","编程能力","问题分析","综合设计"],"values":[82,72,65,85,78,70]},
        "knowledge_distribution": [{"name":"Java","value":35,"color":"#4a7dff"},{"name":"数据库","value":25,"color":"#6c5ce7"},{"name":"AI开发","value":20,"color":"#00bcd4"},{"name":"算法","value":20,"color":"#ff9800"}],
        "agents": [
            {"key":"lms","name":"学情诊断Agent","status":"running","statusText":"运行中","task":"分析用户能力"},
            {"key":"krs","name":"知识检索Agent","status":"running","statusText":"运行中","task":"检索知识库"},
            {"key":"dgs","name":"内容生成Agent","status":"running","statusText":"生成中","task":"正在生成讲义"},
            {"key":"ars","name":"仲裁审核Agent","status":"running","statusText":"审核中","task":"交叉验证"},
            {"key":"tis","name":"导学交互Agent","status":"idle","statusText":"等待中","task":""},
            {"key":"coord","name":"决策协调Agent","status":"idle","statusText":"等待中","task":""},
        ],
        "ai_reminder": "AI建议：你已经连续学习5天！建议完成SpringBoot实践第3章",
        "streak_days": 12,
    })

@app.get("/api/v1/recommend")
async def recommend(): return ok({"courses":[],"projects":[],"tests":[]})

@app.get("/api/v1/agent/status")
async def agent_status(): return ok({"agents":[],"running":4,"total":6})

# ==================== 学情画像 ====================
@app.get("/api/v1/profile/info")
async def profile_info():
    return ok({
        "comprehensive_score":86,"ability_level":"良好","score_change":8,
        "radar":{"dimensions":["理论基础","工程实践","创新能力","编程能力","问题分析","综合设计"],"values":[82,72,65,85,78,70]},
        "knowledge":[{"domain":"Java","rate":90,"sub":[{"name":"基础","rate":95},{"name":"集合","rate":90},{"name":"多线程","rate":75},{"name":"JVM","rate":60}]},{"domain":"数据库","rate":78},{"domain":"AI","rate":65},{"domain":"算法","rate":82}],
        "growth_trend":{"labels":["1月","2月","3月","4月","5月","6月","7月"],"values":[70,73,75,78,80,83,86]},
        "weak_points":[{"name":"JVM内存模型","rate":60,"advice":"学习JVM调优"},{"name":"数据库优化","rate":55,"advice":"学习SQL优化与索引"},{"name":"系统架构设计","rate":50,"advice":"完成大型项目实践"}],
        "ai_advice":"你的后端开发能力增长明显(+15%)。优势：基础知识扎实、编码能力较强。不足：缺少大型项目经验、系统设计能力不足。建议：完成微服务项目实践。",
    })

@app.get("/api/v1/profile/trend")
async def profile_trend(period: str = "30d"): return ok({"labels":["7/1","7/5","7/10","7/15","7/20"],"values":[78,80,82,84,86]})

@app.get("/api/v1/profile/knowledge")
async def profile_knowledge(): return ok({"domains":[{"name":"Java","rate":90},{"name":"数据库","rate":78},{"name":"AI","rate":65}]})

@app.post("/api/v1/profile/analyze")
async def profile_analyze(): return ok({"message":"AI分析完成","advice":"你的后端开发能力增长明显。"})

# ==================== 知识库 ====================
@app.get("/api/v1/knowledge/search")
async def knowledge_search(q: str = "", domain: str = "", top_k: int = 10):
    chunks = [
        {"chunk_id":"kb_001","document_id":"doc_001","title":"Python变量与数据类型","content":"Python是动态类型语言，变量不需要声明类型。","domain":"ai_python","credibility":98,"difficulty":"easy","keywords":["变量","数据类型"]},
        {"chunk_id":"kb_002","document_id":"doc_001","title":"Python控制流","content":"Python使用if-elif-else进行条件判断，使用for和while进行循环。","domain":"ai_python","credibility":95,"difficulty":"easy"},
        {"chunk_id":"kb_003","document_id":"doc_002","title":"Python面向对象","content":"使用class关键字定义类，__init__是构造函数。","domain":"ai_python","credibility":96,"difficulty":"medium"},
        {"chunk_id":"kb_004","document_id":"doc_003","title":"Spring Boot自动配置","content":"Spring Boot基于@EnableAutoConfiguration实现自动配置。","domain":"java","credibility":98,"difficulty":"medium"},
        {"chunk_id":"kb_005","document_id":"doc_003","title":"RAG技术原理","content":"RAG检索增强生成结合了信息检索与文本生成。","domain":"ai","credibility":95,"difficulty":"hard"},
    ]
    if q:
        chunks = [c for c in chunks if q.lower() in c["title"].lower() or q.lower() in c["content"].lower()]
    return ok({"chunks": chunks[:top_k], "total": len(chunks)})

@app.get("/api/v1/knowledge/categories")
async def knowledge_categories():
    return ok({"categories":[
        {"id":1,"name":"软件工程","children":[{"id":11,"name":"设计模式"},{"id":12,"name":"架构设计"}]},
        {"id":2,"name":"Java开发","children":[{"id":21,"name":"Java基础"},{"id":22,"name":"Spring"},{"id":23,"name":"微服务"}]},
        {"id":3,"name":"人工智能","children":[{"id":31,"name":"大模型"},{"id":32,"name":"RAG"},{"id":33,"name":"Agent"}]},
        {"id":4,"name":"数据库","children":[{"id":41,"name":"MySQL"},{"id":42,"name":"Redis"}]},
    ]})

@app.get("/api/v1/knowledge/detail/{chunk_id}")
async def knowledge_detail(chunk_id: str):
    return ok({"chunk_id":chunk_id,"title":"Python变量与数据类型","content":"Python是动态类型语言...","source":"Python官方文档","credibility":98,"related":[]})

@app.get("/api/v1/knowledge/graph")
async def knowledge_graph():
    return ok({"nodes":[{"id":"python","name":"Python"},{"id":"java","name":"Java"}],"edges":[{"source":"python","target":"java","relation":"同属编程语言"}]})

@app.get("/api/v1/knowledge/rag-visualize")
async def rag_visualize(): return ok({"steps":[{"name":"Query理解","status":"done"},{"name":"Embedding","status":"done"},{"name":"向量检索","status":"done"},{"name":"重排序","status":"done"}]})

# ==================== 学习会话与AI生成 ====================
@app.post("/api/v1/sessions")
async def create_session(body: dict):
    sid = uid()
    bg = body.get("background","")
    sa = body.get("self_assessment",{})
    pt = body.get("pre_test_results",{})
    # 规则引擎生成画像
    kb_val = 0.15; kd_val = 0.10; ea_val = 0.10
    if any(w in bg for w in ["研究生","博士","精通","3年"]): kb_val,kd_val,ea_val = 0.85,0.80,0.75
    elif any(w in bg for w in ["大三","大四","计算机","软件","2年","项目"]): kb_val,kd_val,ea_val = 0.50,0.55,0.45
    elif any(w in bg for w in ["大二"]): kb_val,kd_val,ea_val = 0.30,0.25,0.20
    ls = "practice_first" if any(w in bg for w in ["实践","项目","实操"]) else "balanced"
    profile = LearnerProfile(user_id="u001",comprehensive_score=int(kb_val*100),knowledge_breadth=kb_val,knowledge_depth=kd_val,learning_style=ls,engineering_ability=ea_val,cognitive_load=0.6 if kb_val<0.2 else 0.3,dimension_scores={"python":kb_val,"algorithms":kd_val})
    # 模拟六Agent流程
    lecture = f"## 个性化讲义\n\n> 基于学情画像（广度:{kb_val:.0%} 深度:{kd_val:.0%} 风格:{ls}）自动生成\n\n### Python基础\nPython是动态类型语言，变量无需声明。\n\n```python\nname = input('你的名字: ')\nprint(f'你好, {{name}}!')\n```\n\n### 条件判断\n```python\nscore = 85\nif score >= 90: print('优秀')\nelif score >= 60: print('及格')\n```"
    gen = GeneratedContent(agent_id="fusion",strategy="fused",lecture_notes=lecture,practice_guide="## 实操指南\n\n创建命令行计算器：\n```python\ndef add(a,b): return a+b\n# ...\n```",quiz_questions=[{"type":"single_choice","difficulty":"easy","question":"Python定义变量的正确方式是？","answer":"x = 10"}],knowledge_points_covered=["变量","控制流","函数"],source_references=[{"chunk_id":"kb_001","title":"Python变量","confidence":98}])
    result = SessionResult(session_id=sid,status="complete",learner_profile=profile,final_content=gen,debate_summary={"triggered":True,"rounds":1,"disputed_points":1},confidence_scores={"变量":0.95,"控制流":0.92},source_traces=gen.source_references)
    _sessions[sid] = result
    return ok({"session": result.model_dump()})

@app.get("/api/v1/sessions/{sid}")
async def get_session(sid: str):
    s = _sessions.get(sid)
    return ok({"session": s.model_dump()}) if s else err(1002,"会话不存在")

@app.post("/api/v1/sessions/{sid}/interact")
async def session_interact(sid: str, body: dict):
    ans = body.get("content",{}).get("answer","")
    return ok({"interaction": InteractionResponse(response_type="进阶挑战" if len(ans)>10 else "降维解释",content="回答得很好！" if len(ans)>10 else "需要重新讲解吗？").model_dump()})

@app.get("/api/v1/sessions/{sid}/report")
async def session_report(sid: str):
    return ok({"report":{"radar_chart":{"dimensions":["理论基础","工程实践","创新能力","编程能力","问题分析","综合设计"],"values":[82,72,65,85,78,70]},"knowledge_map":{"mastered":["Python变量","控制流"],"in_progress":["函数","面向对象"],"not_started":["装饰器","多线程"]},"learning_path":[{"order":1,"topic":"Python基础","status":"completed"},{"order":2,"topic":"面向对象","status":"in_progress"},{"order":3,"topic":"高级特性","status":"next"}]}})

# ==================== AI讲义生成 ====================
@app.post("/api/v1/lecture/generate")
async def lecture_generate(body: dict):
    return ok({"task_id":uid(),"status":"generating"})
@app.get("/api/v1/lecture/list")
async def lecture_list():
    return ok({"list":[{"id":"l001","title":"Python入门讲义","domain":"Python","created":"2026-07-20","confidence":95},{"id":"l002","title":"SpringBoot实战讲义","domain":"Java","created":"2026-07-18","confidence":92}]})
@app.get("/api/v1/lecture/detail/{lid}")
async def lecture_detail(lid: str):
    return ok({"id":lid,"title":"Python入门讲义","content":"## Python基础\n\nPython是动态类型语言...","sources":[{"chunk_id":"kb_001","title":"Python变量","confidence":98}]})

# ==================== 实操指南 ====================
@app.post("/api/v1/practice/generate")
async def practice_generate(body: dict): return ok({"task_id":uid()})
@app.get("/api/v1/practice/list")
async def practice_list():
    return ok({"list":[{"id":"p001","title":"校园二手交易系统","domain":"Java","difficulty":"中级","progress":65,"tech":["SpringBoot","MySQL","Vue3"]}]})
@app.get("/api/v1/practice/detail/{pid}")
async def practice_detail(pid: str):
    return ok({"id":pid,"title":"校园二手交易系统","project_intro":"掌握SpringBoot接口开发","requirements":"<h4>功能需求</h4><ul><li>用户注册登录</li><li>商品发布浏览</li></ul>","system_design":"Vue3 → SpringBoot → MySQL","steps":[{"title":"环境搭建","desc":"创建项目","done":True},{"title":"数据库设计","desc":"设计表结构","done":True},{"title":"接口开发","desc":"RESTful API","done":False}],"current_step":2,"score":85})
@app.post("/api/v1/practice/{pid}/submit")
async def practice_submit(pid: str, body: dict): return ok({"score":85,"feedback":"功能完成度良好"})
@app.get("/api/v1/practice/{pid}/report")
async def practice_report(pid: str): return ok({"report":"项目总结报告..."})
@app.post("/api/v1/practice/{pid}/ai-help")
async def practice_ai_help(pid: str, body: dict):
    q = body.get("question","")
    return ok({"answer":f"关于「{q[:30]}」的问题，根据项目配置分析：请检查相关配置文件。"})

# ==================== 分阶测试 ====================
@app.post("/api/v1/test/generate")
async def test_generate(body: dict): return ok({"paper_id":uid()})
@app.get("/api/v1/test/list")
async def test_list():
    return ok({"list":[{"id":"t001","title":"Java中级能力测试","domain":"Java","difficulty":"medium","total":10,"time_limit":30},{"id":"t002","title":"Python基础测试","domain":"Python","difficulty":"easy","total":15,"time_limit":20}]})
@app.get("/api/v1/test/detail/{tid}")
async def test_detail(tid: str):
    return ok({"id":tid,"title":"Java中级能力测试","time_limit":30,"questions":[{"index":0,"type":"single_choice","difficulty":"easy","question":"Spring Boot的核心特性不包括？","options":["自动配置","起步依赖","内嵌服务器","分布式事务"],"knowledge_point":"Spring Boot基础"},{"index":1,"type":"single_choice","difficulty":"medium","question":"@SpringBootApplication注解包含以下哪些？","options":["@Configuration","@EnableAutoConfiguration","@ComponentScan","以上都是"],"knowledge_point":"Spring注解"},{"index":2,"type":"coding","difficulty":"hard","question":"编写一个REST控制器，实现GET /api/hello接口。","knowledge_point":"REST API"}]})
@app.post("/api/v1/test/{tid}/submit")
async def test_submit(tid: str, body: dict):
    return ok({"total_score":85,"max_score":100,"time_spent":1500,"wrong_analysis":[{"index":0,"your_answer":0,"correct_answer":3,"question":"Spring Boot的核心特性不包括？","analysis":"Spring Boot不直接提供分布式事务"}],"ai_advice":"Java基础扎实，建议深入学习并发编程。"})
@app.get("/api/v1/test/{tid}/result")
async def test_result(tid: str): return ok({"score":85,"details":[]})

# ==================== 学情报告 ====================
@app.get("/api/v1/report/latest")
async def report_latest():
    return ok({"id":"r001","period":"2026-07","comprehensive_score":86,"radar":{"dimensions":["理论基础","工程实践","创新能力","编程能力","问题分析","综合设计"],"values":[82,72,65,85,78,70]},"knowledge_mastery":{"Java":90,"数据库":78,"AI":65,"算法":80},"growth_trend":{"labels":["1月","2月","3月","4月","5月","6月","7月"],"values":[70,73,75,78,80,83,86]},"weak_points":[{"name":"JVM内存模型","rate":60,"advice":"学习JVM调优"}],"ai_advice":"后端开发能力提升明显","career":{"role":"Java后端开发工程师","match":85},"next_path":["SpringBoot进阶","微服务架构","AI Agent开发"],"created_at":"2026-07-21"})
@app.post("/api/v1/report/create")
async def report_create(): return ok({"report_id":uid()})
@app.get("/api/v1/report/detail/{rid}")
async def report_detail(rid: str): return ok({"id":rid})
@app.get("/api/v1/report/export/{rid}")
async def report_export(rid: str): return ok({"pdf_url":f"/reports/{rid}.pdf"})
@app.get("/api/v1/report/history")
async def report_history():
    return ok({"list":[{"id":"r001","name":"2026年7月学习报告","date":"07-21","score":86},{"id":"r002","name":"2026年6月学习报告","date":"06-21","score":78}]})

# ==================== 学习记录 ====================
@app.get("/api/v1/records/list")
async def records_list():
    return ok({"records":[{"time":"2026-07-21 14:30","type":"lecture","action":"完成AI讲义阅读","detail":"Spring Boot入门讲义","duration":"45分钟"},{"time":"2026-07-21 10:15","type":"test","action":"完成分阶测试","detail":"Java中级测试 - 85分","duration":"30分钟"},{"time":"2026-07-20 16:00","type":"practice","action":"实操任务","detail":"接口开发完成","duration":"2小时"},{"time":"2026-07-20 09:00","type":"checkin","action":"学习计划打卡","detail":"完成2/3项","duration":"—"}]})
@app.get("/api/v1/records/statistics")
async def records_statistics(): return ok({"total_hours":128,"courses_completed":15,"projects_completed":8,"avg_daily_hours":2.5,"peak_time":"晚上","learning_distribution":{"video":40,"reading":30,"practice":30}})
@app.get("/api/v1/records/calendar")
async def records_calendar(month: str = "2026-07"): return ok({"days":[{"date":"2026-07-01","hours":2.5},{"date":"2026-07-02","hours":3.0}]})

# ==================== 学习计划与监督 ====================
@app.get("/api/v1/plan/current")
async def plan_current():
    return ok({"id":"plan001","title":"Java高级开发工程师学习计划","goal":"成为Java高级开发工程师","career_direction":"Java开发","total_phases":4,"current_phase":2,"progress":45,"status":"active","target_date":"2026-10-01","phases":[{"id":1,"title":"基础学习","progress":100,"status":"completed"},{"id":2,"title":"能力提升","progress":65,"status":"active"},{"id":3,"title":"项目实践","progress":20,"status":"pending"},{"id":4,"title":"综合训练","progress":0,"status":"pending"}],"stats":{"completed_tasks":18,"total_tasks":40,"streak_days":12}})
@app.post("/api/v1/plan/create")
async def plan_create(body: dict): return ok({"plan_id":uid()})
@app.put("/api/v1/plan/update")
async def plan_update(body: dict): return ok({"message":"计划已更新"})
@app.get("/api/v1/plan/supervision")
async def plan_supervision():
    return ok({"enabled":True,"remind_time":"09:00","remind_methods":["email","app"],"adjust_after_days":3,"email":"user@example.com"})
@app.post("/api/v1/plan/supervision")
async def plan_supervision_update(body: dict): return ok({"message":"监督设置已更新"})
@app.post("/api/v1/plan/checkin")
async def plan_checkin(body: dict):
    completed = body.get("completed_ids",[])
    return ok({"message":f"打卡成功，完成{len(completed)}项任务","streak_days":13,"completed_count":len(completed)})
@app.get("/api/v1/plan/adjustments")
async def plan_adjustments():
    return ok({"adjustments":[{"id":1,"time":"2026-07-18","type":"warning","reason":"连续3天未完成'微服务架构'章节","change":"推迟至第4阶段"},{"id":2,"time":"2026-07-10","type":"success","reason":"提前2天完成'Java基础'","change":"提前进入能力提升阶段"}]})
@app.get("/api/v1/plan/reminders")
async def plan_reminders():
    return ok({"reminders":[{"date":"2026-07-20","time":"09:00","type":"email","content":"今日有2项学习任务待完成","status":"sent"},{"date":"2026-07-19","time":"09:00","type":"email","content":"已连续2天未完成，请尽快补上","status":"sent"}]})

# ==================== 多Agent协同中心 ====================
@app.get("/api/v1/agents/status")
async def agents_status():
    return ok({"agents":[{"key":"lms","name":"学情诊断Agent","status":"running","task":"分析用户能力画像"},{"key":"krs","name":"知识检索Agent","status":"running","task":"检索相关知识"},{"key":"dgs","name":"内容生成Agent","status":"running","task":"双生成+辩论"},{"key":"ars","name":"仲裁审核Agent","status":"idle","task":""},{"key":"tis","name":"导学交互Agent","status":"idle","task":""},{"key":"coord","name":"决策协调Agent","status":"running","task":"协调任务分配"}],"running":4,"total":6})
@app.get("/api/v1/agents/{name}/detail")
async def agent_detail(name: str):
    return ok({"name":name,"status":"running","current_task":"分析用户能力","steps":[{"name":"数据采集","status":"done"},{"name":"特征提取","status":"done"},{"name":"画像生成","status":"active"}],"io":{"input":"用户学习数据","output":"六维画像"},"communication":[{"from":"Coordinator","to":name,"content":"请求分析用户画像"}]})
@app.get("/api/v1/agents/tasks")
async def agent_tasks():
    return ok({"tasks":[{"id":1,"agent":"lms","task_type":"profile_analysis","status":"completed","duration_ms":1200,"created_at":"2026-07-21 10:30"}]})

# ==================== 系统设置 ====================
@app.get("/api/v1/settings")
async def get_settings(): return ok({"content_detail":"standard","code_ratio":50,"notify_email":True,"notify_sms":False,"notify_app":True,"learning_mode":"balanced","learning_direction":["Java开发"]})
@app.put("/api/v1/settings")
async def update_settings(body: dict): return ok({"message":"设置已更新"})
@app.put("/api/v1/settings/password")
async def change_password(body: dict): return ok({"message":"密码已修改"})
@app.put("/api/v1/settings/security")
async def security_settings(body: dict): return ok({"message":"安全设置已更新"})

# ==================== 消息中心 ====================
@app.get("/api/v1/message/list")
async def message_list():
    return ok({"messages":[{"id":1,"title":"AI讲义生成完成","content":"你的Java集合框架学习报告已生成","type":"ai_task","is_read":False,"created_at":"2026-07-21 10:30"},{"id":2,"title":"学习提醒","content":"今日有2项任务待完成","type":"reminder","is_read":True,"created_at":"2026-07-21 09:00"}]})

# ==================== WebSocket ====================
@app.websocket("/ws/sessions/{sid}")
async def ws_session(ws: WebSocket, sid: str):
    await ws.accept(); _ws[sid] = ws
    events = [
        {"event":"agent.status","agent":"lms","status":"analyzing"},{"event":"agent.status","agent":"lms","status":"completed"},
        {"event":"agent.status","agent":"krs","status":"retrieving"},{"event":"agent.status","agent":"krs","status":"completed"},
        {"event":"generation.progress","agent":"gen_a","chunk":"正在生成讲义..."},{"event":"generation.progress","agent":"gen_b","chunk":"正在生成实操指南..."},
        {"event":"arbitration.compare","knowledge_point":"Python基础","score_a":0.92,"score_b":0.85},
        {"event":"fusion.complete","final_content":"融合输出完成"},
    ]
    try:
        for ev in events: await ws.send_text(json.dumps(ev, ensure_ascii=False))
        while True:
            data = await ws.receive_text()
            await ws.send_text(json.dumps({"event":"echo","data":data}, ensure_ascii=False))
    except WebSocketDisconnect:
        _ws.pop(sid, None)

# ==================== 健康检查 ====================
@app.get("/api/v1/health")
async def health(): return ok({"version":"0.1.0","demo_mode":DEMO_MODE})

if __name__ == "__main__":
    import uvicorn; uvicorn.run(app, host="0.0.0.0", port=settings.gw_port)
'''
