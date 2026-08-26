"""把路线主题转换为初学者可直接执行的原子学习单元。"""

from __future__ import annotations

import copy
from typing import Any

CURRICULUM_VERSION = "2026.08-atomic-v1"


# 高频入门主题使用人工编排的顺序，避免把“HTML”“Python”“Agent”继续当成一个任务。
TOPIC_POINT_OVERRIDES: dict[str, list[str]] = {
    "HTML5 语义标签": [
        "安装 VS Code、Live Server，创建 index.html，并会用浏览器 Elements、Console、Network 面板",
        "HTML 文档骨架：DOCTYPE、html、head、body、charset 与 viewport",
        "HTML 注释 <!-- -->、元素嵌套规则、块级/行内/替换元素分类",
        "文本标签：h1–h6、p、strong、em、br、hr、code、pre",
        "图像：img 的 src、alt、width/height，以及 figure 与 figcaption",
        "音视频：audio、video、source、controls、poster 与格式回退",
        "列表：ul/ol/li 与 dl/dt/dd，理解何时使用哪一种列表",
        "链接、相对/绝对路径、URL 编码与 &lt;、&gt;、&amp; 等字符实体",
        "页面结构：header、nav、main、section、article、aside、footer",
        "用 Markdown 的标题、列表、链接、图片和代码块整理本节笔记",
    ],
    "HTML5 语义化": [
        "安装 VS Code、Live Server，创建 index.html，并会用浏览器 Elements、Console、Network 面板",
        "HTML 文档骨架：DOCTYPE、html、head、body、charset 与 viewport",
        "HTML 注释 <!-- -->、元素嵌套规则、块级/行内/替换元素分类",
        "文本标签：h1–h6、p、strong、em、br、hr、code、pre",
        "图像：img 的 src、alt、width/height，以及 figure 与 figcaption",
        "音视频：audio、video、source、controls、poster 与格式回退",
        "列表：ul/ol/li 与 dl/dt/dd，理解何时使用哪一种列表",
        "链接、相对/绝对路径、URL 编码与常用字符实体",
        "页面结构：header、nav、main、section、article、aside、footer",
        "用 Markdown 的标题、列表、链接、图片和代码块整理本节笔记",
    ],
    "表单与可访问性": [
        "form、label、input、textarea、button 的语义与提交关系",
        "text、email、password、number、radio、checkbox、file 等输入类型",
        "name、value、placeholder、autocomplete、required 的作用和限制",
        "用 for/id 关联标签，用 fieldset/legend 组织一组表单项",
        "键盘 Tab 顺序、可见焦点、错误文本、aria-invalid 与 aria-describedby",
        "在浏览器无障碍树中检查控件名称、角色、状态和错误关联",
    ],
    "CSS3 盒模型": [
        "CSS 引入方式、规则结构、层叠、继承、优先级和 !important 风险",
        "标签、类、ID、属性选择器以及 :hover、:focus、::before 等伪类/伪元素",
        "后代、子代、相邻兄弟（+）和通用兄弟（~）关系选择器",
        "content、padding、border、margin 与 box-sizing: border-box",
        "block、inline、inline-block、none 的尺寸和换行差异",
        "宽高、min/max、overflow、边框、圆角、阴影和背景的计算结果",
        "文本布局：text-align、line-height、letter-spacing、white-space、word-break 与 text-overflow",
        "字体样式：font-family、font-size、font-weight、font-style、Web Font 与回退字体",
        "用 DevTools 的 Styles、Computed、Box Model 定位样式覆盖和尺寸问题",
    ],
    "Flexbox": [
        "主轴、交叉轴、flex container 与 flex item",
        "display:flex、flex-direction、flex-wrap 与 gap",
        "justify-content、align-items、align-content、align-self",
        "flex-grow、flex-shrink、flex-basis 与 flex 简写",
        "order 的视觉顺序与 DOM/键盘顺序不能被混淆",
        "完成导航栏、等高卡片和页脚贴底三种布局",
    ],
    "CSS Grid": [
        "网格容器、网格线、轨道、单元格和区域",
        "grid-template-columns/rows、repeat、minmax 与 fr",
        "gap、auto-fit、auto-fill 与响应式列数",
        "grid-column、grid-row、grid-template-areas 的定位方式",
        "justify/align-items 与 justify/align-content 的差异",
        "完成仪表盘主区域、侧栏和卡片矩阵布局",
    ],
    "Flexbox/Grid": [
        "Flexbox 的主轴、交叉轴、换行、对齐与 flex 简写",
        "Grid 的网格线、轨道、repeat、minmax、fr 与模板区域",
        "用 Flexbox 处理一维导航/按钮组，用 Grid 处理二维页面/卡片布局",
        "在 DevTools 布局面板中查看 flex/grid 覆盖层和溢出来源",
        "完成一个桌面双栏、平板两列、手机单列的页面骨架",
    ],
    "响应式布局": [
        "viewport 元标签、移动优先与内容驱动的断点选择",
        "媒体查询的 min-width、max-width、orientation 与 hover/pointer",
        "百分比、rem、vw、clamp、min/max 和容器宽度",
        "图片 max-width、aspect-ratio、object-fit 与 srcset/sizes",
        "窄屏导航、表格横向滚动、长文本换行和触控目标",
        "用 DevTools 在 375px、768px、1440px 和 200% 缩放下检查页面",
    ],
    "响应式设计": [
        "viewport 元标签、移动优先与内容驱动的断点选择",
        "媒体查询的 min-width、max-width、orientation 与 hover/pointer",
        "百分比、rem、vw、clamp、min/max 和容器宽度",
        "响应式图片、导航、表格、长文本与触控目标",
        "用 DevTools 在 375px、768px、1440px 和 200% 缩放下检查页面",
    ],
    "CSS 动画": [
        "transition-property、duration、timing-function 与 delay",
        "transform 的 translate、scale、rotate 及其合成层优势",
        "@keyframes、animation 简写、fill-mode 与 iteration-count",
        "hover、focus、loading、enter/leave 四类常见动效状态",
        "prefers-reduced-motion 下停止非必要动画",
        "用 Performance 面板检查重排、重绘和掉帧",
    ],
    "Sass": [
        "安装 sass、建立 scss 入口并接入 Vite 构建",
        "变量、嵌套、父选择器 & 与选择器嵌套深度",
        "@use、@forward、模块命名空间与 partial 文件",
        "mixin、function、循环和条件的适用边界",
        "把颜色、间距、断点整理为 token，不在组件中散落魔法值",
    ],
    "JavaScript ES6+": [
        "let/const、基本类型、类型转换、=== 与空值判断",
        "数组、对象、解构、展开、模板字符串与可选链",
        "函数声明、箭头函数、参数、返回值、作用域和 this",
        "map/filter/reduce/find/some/every 等数组方法",
        "错误对象、try/catch/finally 和自定义 Error",
        "在浏览器断点中查看调用栈、作用域、变量和异常",
    ],
    "DOM 与事件": [
        "querySelector、元素创建/插入/删除与 textContent",
        "classList、dataset、属性和表单值的读写",
        "事件对象、target/currentTarget、冒泡、捕获和默认行为",
        "事件委托、一次性监听与 removeEventListener",
        "DOMContentLoaded、表单提交、键盘和输入法 composition 事件",
        "用断点和 Event Listener 面板定位重复绑定与冒泡错误",
    ],
    "DOM 与事件机制": [
        "querySelector、元素创建/插入/删除与 textContent",
        "classList、dataset、属性和表单值的读写",
        "事件对象、target/currentTarget、冒泡、捕获和默认行为",
        "事件委托、一次性监听与 removeEventListener",
        "DOMContentLoaded、表单提交、键盘和输入法 composition 事件",
        "用断点和 Event Listener 面板定位重复绑定与冒泡错误",
    ],
    "Promise/async-await": [
        "同步任务、微任务、宏任务和事件循环的执行顺序",
        "Promise 的 pending/fulfilled/rejected 与 then/catch/finally",
        "async 函数返回值、await 暂停点和 try/catch 错误传播",
        "Promise.all、allSettled、race、any 的失败行为",
        "fetch 的 HTTP 错误判断、超时、AbortController 和重复请求取消",
        "构造成功、404、500、超时和取消五种请求并记录结果",
    ],
    "闭包与原型链": [
        "词法作用域、执行上下文、作用域链与变量生命周期",
        "闭包保存状态的条件、计数器/工厂函数示例和内存风险",
        "对象原型、prototype、__proto__ 与属性查找顺序",
        "构造函数、new 的步骤、class 语法和继承",
        "用 DevTools Memory/Scope 观察闭包引用和原型链",
    ],
    "TypeScript": [
        "安装 TypeScript、tsconfig 与 tsc/noEmit 类型检查",
        "基础类型、数组、元组、枚举的替代方案与字面量类型",
        "interface/type、联合、交叉、可选属性与判别联合",
        "函数参数/返回值、泛型、keyof、typeof 和常用工具类型",
        "unknown、never、any 的差异与类型收窄",
        "给 API 请求、组件属性和错误结果建立可区分类型",
    ],
    "TypeScript 类型系统": [
        "基础类型、字面量、数组、元组与 readonly",
        "interface/type、联合、交叉、可选属性与判别联合",
        "函数重载、泛型约束、keyof、typeof 与索引访问",
        "Partial、Pick、Omit、Record、ReturnType 等工具类型",
        "unknown、never、any 的差异与类型守卫",
        "用 tsc --noEmit 消除一个 API 数据流中的全部类型错误",
    ],
    "ES Modules": [
        "命名导出、默认导出、导入别名和仅类型导入",
        "模块作用域、严格模式、路径解析与扩展名",
        "静态导入、动态 import、循环依赖和副作用模块",
        "浏览器 ESM、Node ESM 与 bundler 处理方式的差异",
        "把单文件示例拆为数据、视图、事件三个模块",
    ],
    "Git": [
        "安装 Git，配置 user.name/user.email，理解工作区、暂存区和仓库",
        "git init/status/add/commit/log/diff 的日常顺序",
        "分支创建、切换、合并，以及冲突标记的读取和解决",
        ".gitignore、README、提交信息和小步提交",
        "用 restore/revert 安全恢复文件或撤销提交，不改写共享历史",
    ],
    "Git/GitHub": [
        "安装 Git，配置身份，理解工作区、暂存区、本地和远程仓库",
        "init/status/add/commit/log/diff/branch/switch/merge 的日常顺序",
        "SSH 或 HTTPS 远程、clone、pull、push 和 upstream",
        "GitHub 仓库、README、Issue、Pull Request 与代码评审",
        "制造并解决一次合并冲突，保留冲突前后提交记录",
    ],
    "npm/pnpm": [
        "安装 Node.js LTS，检查 node/npm/pnpm 版本并配置镜像故障排查",
        "package.json、scripts、dependencies 与 devDependencies",
        "npm/pnpm install、add、remove、run 和 dlx 的区别",
        "lockfile、语义化版本、依赖树与可重复安装",
        "处理命令不存在、版本冲突、缓存和安装失败",
    ],
    "Python": [
        "安装 Python 3.11+、VS Code Python 扩展，确认 python/pip 命令和解释器路径",
        "创建 .venv、激活虚拟环境、安装依赖并生成 requirements.txt 或 pyproject.toml",
        "变量、字符串、数字、布尔、None、list/dict/set/tuple",
        "if/for/while、函数参数与返回值、模块导入和包目录",
        "类、dataclass、异常类型、try/except/finally 与上下文管理器",
        "用断点、调用栈、变量监视和日志定位 KeyError、TypeError、导入错误",
    ],
    "高级语法": [
        "列表/字典/集合推导式与生成器表达式",
        "迭代器协议、yield、生成器发送和惰性计算",
        "装饰器、闭包、functools.wraps 与参数化装饰器",
        "上下文管理器、with、contextlib 与资源释放",
        "dataclass、枚举、模式匹配和描述符的适用场景",
    ],
    "异步编程": [
        "同步、并发、并行的区别以及 I/O 密集与 CPU 密集任务",
        "async def、await、coroutine、event loop 与 task",
        "asyncio.create_task/gather/wait_for 与结构化并发",
        "超时、取消、CancelledError、异常收集和资源清理",
        "用 asyncio.Semaphore 限制并发并记录执行时间",
        "完成成功、单任务失败、超时、取消四条异步路径",
    ],
    "工程结构": [
        "src/tests/docs/scripts 目录职责和包导入边界",
        "pyproject.toml 中的项目元数据、依赖、格式化、检查和测试配置",
        "配置与密钥通过环境变量注入，不写入源码或 Git",
        "日志初始化、异常边界、类型检查和统一命令入口",
        "README 写清安装、运行、测试、目录和常见错误",
    ],
    "测试": [
        "安装 pytest，理解测试发现、Arrange-Act-Assert 与断言失败信息",
        "单元、集成、端到端测试的边界和替身使用原则",
        "fixture、parametrize、临时目录与异常断言",
        "覆盖正常、空输入、非法输入、依赖失败和超时",
        "运行 pytest -q 并读懂通过、失败、跳过和覆盖率输出",
    ],
    "模型 API": [
        "API Key、base URL、model、messages/input 与常用请求参数",
        "system/user/assistant 消息职责和多轮上下文拼装",
        "同步与流式响应的数据结构、usage 和 finish reason",
        "401、429、5xx、超时、连接失败的识别和重试边界",
        "把密钥放入环境变量并确保日志、前端和仓库不泄露",
    ],
    "SSE": [
        "HTTP 长连接、text/event-stream、event/data/id/retry 字段",
        "服务端逐块发送、flush、心跳与客户端 EventSource/fetch 读取",
        "增量 token 合并、结束标记、Unicode 分块和 UI 更新节流",
        "断线、重复事件、取消、代理缓冲和超时处理",
        "用浏览器 Network 面板验证首字节时间和事件顺序",
    ],
    "Function Calling": [
        "工具名称、用途、JSON Schema 参数和必填字段",
        "模型提出工具调用、应用校验参数、执行工具、回传结果的完整循环",
        "区分模型建议与真实执行，危险工具必须授权和确认",
        "处理未知工具、参数缺失、参数越权、工具超时和返回过大",
        "记录 tool_call_id、参数摘要、结果状态和耗时用于审计",
    ],
    "结构化输出": [
        "JSON Schema 的 object、array、enum、required 和 additionalProperties",
        "用 Pydantic/Schema 校验模型输出并给出字段级错误",
        "区分语法错误、结构错误和业务语义错误",
        "修复请求、有限重试、默认值和人工接管策略",
        "冻结 10 组输入，统计首次通过率与重试后通过率",
    ],
    "提示工程": [
        "目标、上下文、约束、输入、输出格式和成功标准六部分提示结构",
        "zero-shot、few-shot、角色说明与反例的适用场景",
        "把长上下文分成稳定指令、检索证据和当前任务",
        "抵抗提示注入：不把检索文本当系统指令，不泄露密钥和内部提示",
        "用冻结样例比较两个提示版本的正确率、格式通过率、延迟和成本",
    ],
    "LangChain": [
        "模型、PromptTemplate、Runnable 与输出解析器的职责",
        "用 LCEL 的管道、并行、分支和 fallback 组合调用",
        "消息历史、检索器、工具与回调/追踪的连接方式",
        "处理解析失败、模型超时、重试和版本不兼容",
        "先用原生 SDK 实现同一调用，再说明引入 LangChain 的收益与成本",
    ],
    "LangGraph": [
        "State 的字段、Reducer、节点输入输出与状态合并",
        "START/END、普通边、条件边和显式终止条件",
        "checkpoint、thread_id、持久化与中断后恢复",
        "循环次数上限、超时、节点异常、重试与 fallback",
        "绘制状态图并用轨迹验证正常、工具失败、恢复三条路径",
    ],
    "MCP": [
        "MCP host、client、server 以及 tools/resources/prompts 的职责",
        "stdio 与 HTTP 传输、初始化协商和能力声明",
        "工具 JSON Schema、资源 URI、错误返回和分页",
        "进程权限、文件/网络边界、密钥隔离与用户授权",
        "连接一个本地 MCP 服务并记录发现、调用、失败和断开流程",
    ],
    "技能封装": [
        "把单一能力定义为清晰名称、用途、输入 Schema、输出 Schema 和错误码",
        "将鉴权、超时、重试、幂等和日志放在技能边界",
        "区分可重试错误、业务拒绝、权限拒绝与未知结果",
        "为技能准备正常、缺参、越权、超时和依赖失败测试",
        "记录版本、调用次数、成功率、延迟与失败原因",
    ],
    "多 Agent 协作": [
        "何时需要多 Agent，何时单 Agent + 工具已经足够",
        "为规划、执行、审核角色定义互斥职责、输入输出和可见上下文",
        "共享状态、消息格式、任务队列和结果合并规则",
        "冲突仲裁、最大轮次、超时、重复工作检测和终止条件",
        "记录每个角色的输入、输出、工具调用、耗时和最终采纳理由",
    ],
    "切分索引": [
        "按标题、段落、代码块和表格边界解析文档",
        "比较固定长度、递归字符和语义切分及 overlap",
        "给 chunk 保存文档 ID、标题层级、页码、权限和版本元数据",
        "生成 Embedding、建立索引并处理新增、更新、删除",
        "用 20 个问题检查目标证据是否进入候选结果",
    ],
    "混合检索": [
        "关键词检索 BM25 与向量召回的得分含义和优缺点",
        "查询清洗、同义词、metadata filter 与权限过滤",
        "并行召回、分数归一、加权融合和 Reciprocal Rank Fusion",
        "比较只用关键词、只用向量和混合检索的 Recall@k",
        "记录无结果、低相关结果、权限过滤和索引过期四类失败",
    ],
    "重排": [
        "召回与重排的职责边界以及候选数量/延迟权衡",
        "Cross-Encoder/Reranker 的 query-document 输入和相关性分数",
        "top-k 截断、分数阈值、去重和长文档截断",
        "用标注查询比较重排前后的 MRR、nDCG 或命中排名",
        "处理模型不可用、超时和成本超限时的降级",
    ],
    "向量数据库": [
        "collection/index、向量维度、距离度量和 metadata",
        "创建集合、批量写入、相似度查询、过滤、更新和删除",
        "余弦、内积、欧氏距离与归一化的关系",
        "索引参数、召回率、延迟、内存和数据规模的权衡",
        "验证维度不匹配、重复 ID、权限过滤和删除后不可召回",
    ],
    "任务成功率": [
        "把业务目标拆成可判定的成功、部分成功和失败条件",
        "建立冻结任务集、输入夹具、预期产物和评分脚本",
        "区分步骤完成率、最终成功率、人工接管率和恢复率",
        "统计均值、分位数、置信区间并按任务类型切片",
        "每次提示、模型、工具或工作流变更后运行回归对比",
    ],
    "幻觉评测": [
        "区分无依据事实、错误引用、数字失真和遗漏限定条件",
        "建立包含答案要点、允许来源和不可回答项的冻结集",
        "核验引用存在、证据片段支持、实体/数字一致和权限范围",
        "分开报告自动检测指标与人工盲评结果",
        "对不支持主张执行拒答、降级或转人工，不伪造确定答案",
    ],
    "安全审计": [
        "列出模型、工具、数据源、用户和外部系统之间的信任边界",
        "检查提示注入、越权工具、敏感数据泄露和不安全输出执行",
        "记录身份、动作、资源、参数摘要、结果、时间和追踪 ID",
        "验证最小权限、显式授权、危险操作确认与密钥隔离",
        "用越权、注入、重放、日志脱敏和审计追踪用例回归",
    ],
    "成本治理": [
        "记录每次调用的模型、输入/输出 token、缓存命中、工具费用和耗时",
        "按用户、功能、任务和日期聚合预算与单位成功任务成本",
        "设置软告警、硬上限、并发限制和超预算降级",
        "比较小模型路由、提示压缩、缓存和批处理的质量/成本变化",
        "对未知账单、重试放大和循环调用建立熔断与审计",
    ],
}


def _add_topic_aliases(aliases: tuple[str, ...], points: list[str]) -> None:
    for alias in aliases:
        TOPIC_POINT_OVERRIDES.setdefault(alias, points)


_add_topic_aliases(
    ("环境搭建", "Vite 环境配置"),
    [
        "安装运行时、编辑器与对应语言扩展，核对版本和可执行文件路径",
        "创建项目目录、初始化包/依赖文件并运行第一个开发命令",
        "理解开发、测试、构建、预览四个命令及其输出目录",
        "配置断点、变量监视、调用栈、终端与日志查看入口",
        "处理命令不存在、端口占用、依赖安装失败和环境变量缺失",
        "把安装、启动、测试和故障处理命令写入 README",
    ],
)
_add_topic_aliases(
    ("布局", "布局约束", "样式"),
    [
        "坐标系、父子约束、内容尺寸与可用空间的传递方式",
        "水平/垂直排列、间距、对齐、伸缩和换行",
        "固定尺寸、内容自适应、最小/最大尺寸与安全区域",
        "滚动容器、溢出、层叠顺序和键盘遮挡",
        "长文本、空内容、加载中、错误和不同屏幕尺寸下的布局",
        "用布局检查器定位约束冲突、截断和不必要重排",
    ],
)
_add_topic_aliases(
    ("排版",),
    [
        "字体家族、字号、字重、行高、字距和中英文混排",
        "标题、正文、说明、数据、按钮五类文字层级",
        "行长、段距、对齐、换行、截断与完整值访问",
        "数字等宽、代码字体、回退字体和字体加载",
        "对比度、200% 缩放、粗体/高对比模式和可读性",
        "在真实长中文、英文技术名和极端数据下检查版面",
    ],
)
_add_topic_aliases(
    ("错误处理", "异常处理", "错误恢复", "失败恢复"),
    [
        "区分输入错误、业务拒绝、依赖失败、超时、取消和未知结果",
        "定义可判别错误类型/错误码、用户提示和内部诊断信息",
        "在正确边界捕获异常，保留 cause/stack/trace ID，不静默吞错",
        "只对安全且幂等的操作有限重试，并使用退避和抖动",
        "失败后保留安全输入，执行回滚、补偿、降级或人工接管",
        "为每类错误编写触发用例并检查恢复后状态一致",
    ],
)
_add_topic_aliases(
    ("认证", "认证鉴权", "认证授权", "Auth.js"),
    [
        "注册、登录、退出、刷新令牌和会话过期状态",
        "密码哈希、Cookie/Token 存储、CSRF 与传输安全",
        "身份认证与角色/资源授权的职责边界",
        "401、403、令牌失效、重复刷新和多标签页会话",
        "后端强制授权，前端只负责入口提示而不充当安全边界",
        "用未登录、普通用户、管理员、过期会话四组请求验证",
    ],
)
_add_topic_aliases(
    ("权限", "权限边界", "权限路由", "权限指令与动态路由"),
    [
        "主体、角色、资源、动作和作用域五个授权要素",
        "RBAC/ABAC、默认拒绝、最小权限与职责分离",
        "导航隐藏、控件禁用、403 页面与后端授权的关系",
        "对象级权限、租户隔离、批量操作和越权 ID 枚举",
        "权限变化、会话缓存失效和审计日志",
        "用横向越权、纵向越权、直接 URL 和 API 请求回归",
    ],
)
_add_topic_aliases(
    ("网络", "网络层", "网络协议"),
    [
        "IP、子网、网关、DNS、端口与客户端/服务端角色",
        "TCP 建连/断开、可靠传输、UDP 特点与适用场景",
        "HTTP 方法、状态码、请求头、响应头、Cookie 与缓存",
        "TLS 证书、握手、主机名校验和常见安全错误",
        "用 ping/nslookup/curl 和抓包定位 DNS、连接、TLS、HTTP 问题",
        "构造断网、拒绝连接、超时、丢包和错误代理配置",
    ],
)
_add_topic_aliases(
    ("数据库", "数据建模"),
    [
        "实体、属性、主键、外键、唯一约束和空值语义",
        "一对一、一对多、多对多关系及中间表",
        "规范化、反规范化、索引与读写成本权衡",
        "增删改查、事务边界、隔离级别和约束错误",
        "迁移、种子数据、备份恢复和环境间结构一致",
        "用执行计划、约束失败和并发更新验证模型",
    ],
)
_add_topic_aliases(
    ("缓存", "浏览器缓存"),
    [
        "缓存键、值、TTL、命中、未命中和淘汰策略",
        "Cache-Aside 的读取、写入、失效和回源顺序",
        "缓存穿透、击穿、雪崩、热点键与解决手段",
        "数据一致性、双写失败、延迟失效和版本键",
        "浏览器 Cache-Control、ETag、强缓存与协商缓存",
        "记录命中率、延迟，并验证过期、并发回源和脏数据",
    ],
)
_add_topic_aliases(
    ("日志", "日志追踪", "可观测性", "监控", "观测"),
    [
        "结构化日志的时间、级别、服务、事件、trace ID 和错误字段",
        "指标的 counter、gauge、histogram 与标签基数",
        "分布式 trace、span、父子关系和跨服务上下文传播",
        "健康检查、SLI/SLO、告警阈值和告警降噪",
        "敏感字段脱敏、采样、保留周期和访问权限",
        "从一次失败请求沿日志、指标、追踪定位到具体步骤",
    ],
)
_add_topic_aliases(
    ("性能", "性能优化", "性能调优", "性能分析"),
    [
        "先定义吞吐、延迟分位数、资源占用、包体或帧率等目标指标",
        "建立固定数据、环境、预热和重复次数的可复现基线",
        "用 profiler/Performance/trace 找热点，不凭感觉修改",
        "区分 CPU、内存、I/O、网络、锁竞争和渲染瓶颈",
        "一次只改变一个因素，记录优化前后与副作用",
        "加入性能回归阈值，并验证低端设备或高负载边界",
    ],
)
_add_topic_aliases(
    ("安全", "API 安全", "Web 基础"),
    [
        "资产、攻击者、入口、信任边界和风险影响的威胁模型",
        "输入校验、输出编码、参数化查询和文件/URL 安全",
        "身份、权限、会话、密钥与最小权限",
        "XSS、CSRF、注入、SSRF、越权和敏感数据泄露",
        "安全响应头、依赖扫描、日志审计和漏洞修复验证",
        "只在自有/授权环境运行攻击用例，并保留修复前后证据",
    ],
)
_add_topic_aliases(
    ("发布", "应用发布", "生产部署", "线上部署作品", "线上作品集"),
    [
        "区分开发、测试、预发布、生产环境与配置来源",
        "构建版本号、制品、校验和与不可变发布物",
        "部署前迁移、密钥注入、健康检查和依赖检查",
        "滚动/蓝绿/灰度发布的流量切换和回滚条件",
        "域名、TLS、缓存、日志、指标与告警验证",
        "执行一次发布失败和回滚演练，记录恢复时间与结果",
    ],
)
_add_topic_aliases(
    ("状态", "状态管理"),
    [
        "区分局部 UI、跨页面、服务端缓存、持久化和派生状态",
        "定义状态结构、初始值、允许事件和状态转换",
        "保持单向数据流，避免重复来源和不可追踪直接修改",
        "处理加载、空、错误、过期、并发更新和乐观回滚",
        "选择内存、URL、服务端或本地存储，并说明生命周期",
        "用状态图和测试验证正常、失败、刷新和返回路径",
    ],
)
_add_topic_aliases(
    ("并发", "协程", "Goroutine", "Channel"),
    [
        "并发、并行、同步、异步以及 I/O/CPU 密集任务差异",
        "任务创建、调度、等待、取消和异常传播",
        "共享状态、竞态条件、锁、原子操作与消息传递",
        "超时、背压、并发上限、资源池和优雅关闭",
        "用竞态检测、日志时间线或 trace 观察实际交错顺序",
        "验证单任务失败、部分失败、取消、超时和资源释放",
    ],
)
_add_topic_aliases(
    ("React", "React JSX 与组件"),
    [
        "用 Vite 创建 React + TypeScript 项目并认识入口、组件和静态资源目录",
        "JSX 表达式、属性、className、条件渲染和列表 key",
        "函数组件、props、children、事件与受控表单",
        "state 更新、批处理、不可变数据和组件重新渲染",
        "组件拆分、组合、状态提升和错误边界",
        "用 React DevTools 检查 props/state，并完成空、错、加载状态",
    ],
)
_add_topic_aliases(
    ("Vue 3", "Vue 3 单文件组件"),
    [
        "用 Vite 创建 Vue 3 + TypeScript 项目并认识 main、App 与组件目录",
        "SFC 的 template/script setup/style 与 scoped 样式",
        "插值、v-bind、v-on、v-if、v-for、key 和 v-model",
        "ref/reactive/computed/watch 的用途和更新时机",
        "props、emit、slot、provide/inject 与组件职责",
        "用 Vue Devtools 检查状态，并完成空、错、加载状态",
    ],
)
_add_topic_aliases(
    ("Java",),
    [
        "安装 JDK、配置 JAVA_HOME，用 javac/java 或构建工具运行首个程序",
        "基本类型、包装类型、String、数组、运算符和类型转换",
        "条件、循环、方法、参数传递、重载和可变参数",
        "类、对象、构造器、封装、继承、多态、接口和抽象类",
        "异常体系、checked/unchecked、try-with-resources 与自定义异常",
        "用 IDE 断点查看线程、调用栈、变量和异常传播",
    ],
)
_add_topic_aliases(
    ("面向对象",),
    [
        "对象、类、字段、方法、构造器和实例生命周期",
        "封装、不变量、访问控制与避免贫血/上帝对象",
        "继承、组合、接口、多态和依赖倒置",
        "值对象、实体、不可变对象与相等性",
        "SOLID 原则及一个违反/重构对照例",
        "为对象正常创建、非法状态和协作替身编写测试",
    ],
)
_add_topic_aliases(
    ("集合",),
    [
        "List、Set、Map、Queue 的语义和选型",
        "ArrayList/LinkedList、HashSet/TreeSet、HashMap/TreeMap 的结构差异",
        "遍历、查找、排序、去重、分组和不可变集合",
        "equals/hashCode、Comparator 与泛型类型安全",
        "并发修改、空值、重复键和线程安全集合",
        "用不同数据规模比较查找、插入、删除的时间与内存",
    ],
)
_add_topic_aliases(
    ("Linux", "Linux 管理"),
    [
        "目录树、绝对/相对路径、文件类型与当前工作目录",
        "ls/cd/pwd/cp/mv/mkdir/touch/less/tail/find/grep 的安全使用",
        "用户、组、rwx 权限、chmod/chown 和 sudo 边界",
        "进程、PID、信号、前后台任务、systemd 与退出码",
        "磁盘、内存、CPU、端口、DNS 和日志的查看命令",
        "用 shell 历史和日志定位权限、路径、端口占用和进程退出问题",
    ],
)


TRACK_PROFILES: dict[str, dict[str, str]] = {
    "web_frontend": {
        "lab": "在独立网页中实现并接入浏览器 DevTools 检查 DOM、样式、网络和控制台",
        "failure": "构造窄屏、键盘操作、空内容和资源加载失败，定位并修复显示或交互问题",
        "evidence": "源代码 + 页面截图 + DevTools 检查记录 + 失败修复前后对比",
        "acceptance": "页面可在桌面与 375px 窄屏使用，控制台无未处理错误，键盘可完成主要操作",
    },
    "backend": {
        "lab": "在最小服务中实现一个接口或后台任务，并从命令行发起真实请求",
        "failure": "构造空值、非法参数、依赖不可用、超时和重复请求，核对状态码、错误体与日志",
        "evidence": "服务代码 + 启动命令 + 正常/错误请求响应 + 自动测试输出",
        "acceptance": "接口输入输出明确，正常与失败响应可重复，自动测试通过且日志能定位失败位置",
    },
    "mobile": {
        "lab": "在模拟器或真机完成一个可操作页面，并接入设备日志和调试器",
        "failure": "构造离线、权限拒绝、旋转/重建、慢设备和后台恢复场景",
        "evidence": "项目代码 + 模拟器/真机录屏 + 设备日志 + 失败场景修复记录",
        "acceptance": "主流程可触控完成，离线或权限失败有明确反馈，重建后关键状态符合设计",
    },
    "fullstack": {
        "lab": "完成一个从界面、接口到数据库的纵向功能切片，并记录请求和数据变化",
        "failure": "构造表单非法、接口 4xx/5xx、数据库约束失败和重复提交",
        "evidence": "前后端代码 + 数据库迁移 + 请求响应 + 端到端测试或部署截图",
        "acceptance": "功能可从界面走通到持久化，失败不丢输入、不写脏数据，测试能重复验证",
    },
    "machine_learning": {
        "lab": "用固定数据切分和随机种子完成一个可复现实验，并与简单基线比较",
        "failure": "检查缺失值、类别不平衡、数据泄漏、过拟合和推理输入漂移",
        "evidence": "Notebook/训练代码 + 数据说明 + 指标表 + 固定种子复现日志",
        "acceptance": "从数据到指标可重复运行，指标优于或解释未优于基线，并明确数据与模型限制",
    },
    "agent_engineering": {
        "lab": "实现一个带显式状态、工具调用和轨迹记录的 Agent 节点或工作流",
        "failure": "构造工具缺参、权限拒绝、超时、重复调用和无法终止，验证恢复与人工接管",
        "evidence": "状态/时序图 + 代码 + 正常与失败轨迹 + 自动评测结果",
        "acceptance": "每一步输入输出可追踪，工具权限受控，失败可恢复或转人工，冻结任务可重复通过",
    },
    "llm_application": {
        "lab": "用冻结输入完成一次模型调用、检索或评测链路，并记录来源、token、延迟和输出",
        "failure": "构造无证据、格式错误、429/超时、提示注入和预算超限场景",
        "evidence": "调用代码 + 脱敏请求/响应 + 引用或评测记录 + 失败降级结果",
        "acceptance": "输出格式可校验、事实可追溯、异常有界处理，质量与成本指标可重复计算",
    },
    "data_engineering": {
        "lab": "建立一条可重跑的数据输入、转换、校验和输出链路，并记录行数与口径",
        "failure": "构造重复、迟到、缺失、模式变化和任务中断，验证幂等、回填与告警",
        "evidence": "数据契约 + SQL/管道代码 + 输入输出样本 + 数据质量检查结果",
        "acceptance": "同一批数据重跑结果一致，异常数据可定位，指标口径和血缘可说明",
    },
    "devops": {
        "lab": "在本地或隔离环境完成一次配置、部署、观测和回滚操作",
        "failure": "构造配置错误、健康检查失败、资源不足和依赖不可达，按日志与指标排查",
        "evidence": "配置/脚本 + 执行命令 + 状态/日志/指标截图 + 回滚记录",
        "acceptance": "部署与回滚步骤可重复，健康状态可观测，故障能由证据定位而不是靠猜测",
    },
    "network_security": {
        "lab": "只在自有或明确授权靶场复现一个风险、实施修复并再次验证",
        "failure": "检查未授权访问、恶意输入、密钥泄露、重放和审计缺失",
        "evidence": "授权范围说明 + 请求/抓包或扫描记录 + 修复代码/配置 + 复测报告",
        "acceptance": "复现与修复均在授权范围，风险证据可重复，修复后原攻击路径被阻断且无明显回归",
    },
    "uiux": {
        "lab": "围绕一个真实用户任务产出流程、界面状态和可点击原型",
        "failure": "检查空、错、慢、长文本、窄屏、键盘和低视力场景",
        "evidence": "研究或需求证据 + 流程/原型链接 + 状态清单 + 可用性测试记录",
        "acceptance": "关键任务可由目标用户完成，状态与无障碍要求明确，设计结论能追溯到证据",
    },
    "quality_engineering": {
        "lab": "为一个真实功能建立风险、用例、自动化执行和缺陷回归闭环",
        "failure": "覆盖边界、非法输入、依赖失败、并发、超时和不稳定测试",
        "evidence": "测试设计 + 自动化代码 + 运行报告 + 缺陷与修复复测记录",
        "acceptance": "高风险路径有稳定自动化验证，失败信息可定位，重复运行不产生随机误报",
    },
    "algorithms": {
        "lab": "手算样例后独立实现算法，并用自动评测比较正确性、时间和空间复杂度",
        "failure": "构造空输入、最小规模、最大规模、重复值、极端值和反例",
        "evidence": "算法代码 + 手算过程 + 正确性说明 + 边界用例与复杂度实测",
        "acceptance": "边界用例通过，复杂度与实现一致，能说明为何算法正确以及何时不适用",
    },
    "embedded_iot": {
        "lab": "依据数据手册在开发板或仿真器完成外设/任务配置并采集真实输出",
        "failure": "构造断线、超时、抖动、资源耗尽、掉电或异常中断",
        "evidence": "固件代码 + 接线/寄存器说明 + 串口或逻辑分析输出 + 故障记录",
        "acceptance": "时序和资源占用有实测数据，异常后可恢复，结果能与数据手册对应",
    },
    "operating_systems": {
        "lab": "编写一个调用系统接口的最小程序，并用跟踪/性能工具观察真实行为",
        "failure": "构造非法地址、资源耗尽、并发竞争、死锁或系统调用失败",
        "evidence": "源码 + 编译运行命令 + trace/profile 输出 + 边界与并发测试",
        "acceptance": "程序可重复运行，系统行为能由跟踪证据解释，资源在成功和失败后都正确释放",
    },
    "database_systems": {
        "lab": "实现或配置一个最小存储/查询机制，并用数据集和执行计划观察行为",
        "failure": "构造重复键、并发冲突、崩溃恢复、热点和数据倾斜",
        "evidence": "实现/SQL + 数据集 + 执行计划或内部状态 + 正确性与基准结果",
        "acceptance": "结果正确且崩溃/并发边界可验证，性能结论有可重复基线而非主观描述",
    },
}


DEFAULT_PROFILE = {
    "lab": "在当前路线的阶段作品中建立一个独立、可重复运行的练习",
    "failure": "构造空输入、错误配置、依赖失败和超时，读取实际错误并完成修复",
    "evidence": "练习产物 + 运行命令/步骤 + 实际输出 + 失败修复记录",
    "acceptance": "能够从空目录或空白文件重做，正常与失败结果可重复，并能指出适用边界",
}


def _profile(track_code: str) -> dict[str, str]:
    return TRACK_PROFILES.get(track_code, DEFAULT_PROFILE)


def build_learning_unit(
    topic: str,
    *,
    track_code: str,
    pathway_name: str,
    stage_title: str,
) -> dict[str, Any]:
    """Return an ordered, searchable and verifiable learning unit for one topic."""

    profile = _profile(track_code)
    points = TOPIC_POINT_OVERRIDES.get(topic)
    if not points:
        points = [
            f"{topic} 的准确术语、组成部分、输入输出与适用边界",
            f"{topic} 的安装/启用方式，以及 3 个当前阶段最常用的命令、API 或配置项",
            f"{topic} 在“{stage_title}”中的数据流、调用顺序或状态变化",
            f"用调试器、日志、指标、抓包或可视化工具观察 {topic} 的实际运行结果",
            f"把 {topic} 接入“{pathway_name}”阶段作品，并说明它与前后主题的连接点",
        ]
    practice = f"练习：{profile['lab']}，本单元只聚焦“{topic}”。"
    failure = f"故障练习：{profile['failure']}；记录与“{topic}”直接相关的现象和修复。"
    validation = [
        f"不查看成品代码，重新完成“{topic}”的最小功能并得到预期输出",
        f"主动制造至少 1 个“{topic}”相关失败，依据报错、日志或检查工具定位并修复",
        f"用自己的话说明“{topic}”何时使用、依赖什么、不能解决什么",
    ]
    search_terms = [
        f"{topic} 官方文档 入门",
        f"{topic} quickstart 中文",
        f"{topic} 常用 API 命令 配置",
        f"{topic} 常见错误 调试",
    ]
    return {
        "topic": topic,
        "curriculum_version": CURRICULUM_VERSION,
        "knowledge_points": points,
        "learning_steps": [
            f"先学：按顺序掌握 {len(points)} 个知识点，并逐项写进 Markdown 笔记",
            practice,
            failure,
            "最后做：关闭教程，从空白起重做，并按验收清单逐项检查",
        ],
        "learning_action": (
            f"先学“{points[0]}”；再学“{points[1]}”；随后完成“{points[2]}”；"
            "最后执行动手与故障练习并逐项自测。"
        ),
        "practice": practice,
        "failure_drill": failure,
        "validation": validation,
        "search_terms": search_terms,
        "evidence_required": profile["evidence"],
        "acceptance": profile["acceptance"],
    }


def build_remediation_unit(topic: str, track_code: str = "") -> dict[str, Any]:
    """Build a concrete prerequisite-repair task instead of a generic retry instruction."""

    unit = build_learning_unit(
        topic,
        track_code=track_code,
        pathway_name="当前学习路线",
        stage_title="前置回补",
    )
    return {
        **unit,
        "title": f"回补前置：{topic}",
        "learning_steps": [
            f"定位：从当前任务的报错或卡点中写出与“{topic}”有关的 1 个具体问题",
            f"回补：完成“{unit['knowledge_points'][0]}”和“{unit['knowledge_points'][1]}”",
            unit["practice"],
            unit["failure_drill"],
        ],
        "learning_action": (
            f"先定位一个具体卡点；再回补“{unit['knowledge_points'][0]}”和"
            f"“{unit['knowledge_points'][1]}”；随后完成练习与故障修复。"
        ),
    }


def upgrade_plan_phases(
    phases: list[dict[str, Any]],
    *,
    track_code: str,
    skill_names: dict[str, str] | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    """Upgrade stored legacy plans without changing task identifiers or progress keys."""

    upgraded = copy.deepcopy(phases)
    changed = False
    skill_names = skill_names or {}
    for phase in upgraded:
        week_start = int(phase.get("week_start", 1) or 1)
        week_end = max(week_start, int(phase.get("week_end", week_start) or week_start))
        duration = week_end - week_start + 1
        tasks = list(phase.get("tasks", []))
        if not tasks:
            tasks = [
                {
                    "id": skill,
                    "title": skill_names.get(skill, skill),
                    "skill_code": skill,
                }
                for skill in phase.get("skills", [])
            ]
            if tasks:
                changed = True
        concrete_tasks = []
        for index, task in enumerate(tasks):
            topic = task.get("topic") or task.get("title") or task.get("skill_code", "学习任务")
            unit = build_learning_unit(
                topic,
                track_code=task.get("track_code") or track_code,
                pathway_name=(
                    task.get("pathway_name") or phase.get("pathway_name") or "当前学习路线"
                ),
                stage_title=task.get("stage_title") or phase.get("name", "当前阶段"),
            )
            scheduled_week = task.get("scheduled_week")
            if not isinstance(scheduled_week, int):
                scheduled_week = week_start + min(
                    duration - 1,
                    int(index / max(1, len(tasks)) * duration),
                )
            concrete = {
                **task,
                **unit,
                "id": task.get("id") or f"{phase.get('id', 'phase')}:task-{index + 1}",
                "title": task.get("title") or topic,
                "skill_code": task.get("skill_code", ""),
                "track_code": task.get("track_code") or track_code,
                "sequence": task.get("sequence", index + 1),
                "scheduled_week": scheduled_week,
                "week_label": f"第 {scheduled_week} 周",
                "estimated_hours": task.get("estimated_hours"),
            }
            if task.get("curriculum_version") != CURRICULUM_VERSION:
                changed = True
            concrete_tasks.append(concrete)
        week_counts: dict[int, int] = {}
        for task in concrete_tasks:
            week = task["scheduled_week"]
            week_counts[week] = week_counts.get(week, 0) + 1
        for task in concrete_tasks:
            if task["estimated_hours"] is None:
                task["estimated_hours"] = max(
                    0.5,
                    round(
                        float(phase.get("hours_per_week", 8))
                        / week_counts[task["scheduled_week"]],
                        1,
                    ),
                )
        phase["tasks"] = concrete_tasks
        phase["curriculum_version"] = CURRICULUM_VERSION
    return upgraded, changed
