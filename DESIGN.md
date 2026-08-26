---
version: alpha
name: "工学智链"
description: "以工程蓝图和可验证证据链为视觉母题的计算机能力成长与多智能体协同平台。"
colors:
  primary: "#2563EB"
  primary-dark: "#2053CA"
  brand-navy: "#0B2C63"
  brand-cyan: "#00AEEF"
  brand-yellow: "#FFD500"
  canvas-deep: "#061328"
  background: "#F7F9FC"
  surface: "#FFFFFF"
  surface-soft: "#F7F9FD"
  border: "#E5EBF4"
  text: "#18233B"
  muted: "#66748B"
  success: "#17A673"
  warning: "#E89025"
  danger: "#E24F64"
  focus: "#4C82FF"
typography:
  display:
    fontFamily: "Space Grotesk, HarmonyOS Sans SC, MiSans, PingFang SC, Microsoft YaHei UI, sans-serif"
  sans:
    fontFamily: "Inter, HarmonyOS Sans SC, MiSans, PingFang SC, Microsoft YaHei, system-ui, sans-serif"
  utility:
    fontFamily: "Space Grotesk, HarmonyOS Sans SC, MiSans, PingFang SC, sans-serif"
rounded:
  sm: "0.5rem"
  DEFAULT: "0.625rem"
  md: "0.8125rem"
  lg: "1.625rem"
spacing:
  control-height: "2.75rem"
  panel-gap: "1.125rem"
  page-max: "105rem"
  auth-shell-max: "92.5rem"
  sidebar-default: "15.875rem"
  sidebar-min: "13.75rem"
  sidebar-max: "22.5rem"
  sidebar-collapsed: "4.75rem"
components:
  button:
    height: "2.75rem"
    radius: "0.625rem"
  input:
    height: "2.875rem"
    radius: "0.625rem"
  panel:
    radius: "0.8125rem"
  auth-shell:
    radius: "1.625rem"
---

# 工学智链 Design System

## Overview

### Creative North Star

界面应像一张正在运行的工程系统蓝图：路径有先后关系，节点有明确职责，数据有来源与去向，关键结论有“已校验”的视觉证据。它不是通用 AI 聊天壳，也不是霓虹装饰墙；每一条线都应能解释系统如何把学习者背景转化为可执行、可评测的工程学习路径。

### Product context and register

- **Audience and primary job:** 面向计算机专业学习者、转岗学习者和培训管理者，帮助他们选择方向、生成学习资源、完成实操并用证据更新能力画像。业务依据见 `README.md` 与 `SOP_功能操作与比赛痛点说明.md`。
- **Target market(s) and evidence:** 当前为中国高校与中文技能培训场景；赛题方案要求面向应用型工程技术人才，强调个性化、专业准确性和多智能体协同可视化。
- **Locale(s) and language policy:** 产品界面以 `zh-CN` 为主，技术名词保留行业通用英文缩写；用户可见文案和可访问名称不得出现无意的英文回退。
- **Usage scene:** 桌面端用于路线比较、资源生成与项目演示，窄屏设备用于继续任务和查阅结果。产品属于中等信息密度的高频工具。
- **Register:** 混合型。登录页左侧承担品牌表达，右侧认证区及所有登录后页面保持产品工具的安静、熟悉和高可读性。
- **Memorable signature:** “多智能体证据回路”——多个真实业务角色围绕可验证知识核心传递数据脉冲，并明确展示分析、检索、双策略生成、仲裁与反馈的闭环。
- **Restraint:** 品牌黄只用于图标、校验通过与少量关键状态；认证表单、正文、表格和长任务区不使用持续动效或大面积高饱和底色。
- **Anti-references:** 不做无业务含义的发光 AI 球、随机粒子宇宙、聊天机器人首屏或大面积玻璃拟态；这些表达会掩盖项目真正的工程闭环与证据可信度。
- **Token ownership/runtime mapping:** 采用 Model B：`frontend/src/App.vue` 中的 CSS 变量是现有颜色、字体与形状令牌源，侧栏几何与交互常量由共享 `frontend/src/components/layout/AppShell.vue` 持有；本文件镜像并解释已接受值。令牌变更需同步更新对应运行时 owner 和受影响共享组件，并通过构建、严格审计与浏览器截图检查漂移。

## Colors

`primary` 与 `primary-dark` 延续现有产品动作层级；`brand-navy`、`brand-cyan`、`brand-yellow` 来自用户提供的新软件图标，分别承担工程结构、数据传递和证据确认。`canvas-deep` 只用于品牌/协作可视化画布，登录表单仍使用 `surface`、`text` 与 `muted`。错误、警告、成功继续使用既有语义色，不以品牌黄替代警告，也不以品牌蓝替代焦点或错误状态。

## Typography

标题使用 `display` 栈，西文与数字以自托管的 Space Grotesk 变量字体（`public/fonts/`，`font-display: swap`）为首选，中文依序回退到 HarmonyOS Sans SC、MiSans、PingFang SC 等现代无衬线字体；正文和控件沿用 `sans` 栈，西文为系统 Inter 回退，避免远程字体造成首屏跳动。编号、Agent 序号和运行状态使用 `utility` 栈，形成接近工程仪表标注的节奏。正文基线不小于 14px，登录说明不超过约 38 个汉字的行宽；全大写只用于短英文状态标识。

## Layout

登录页在桌面端采用约 58/42 的非对称双栏：左侧是带固定几何范围的协作蓝图，右侧是认证功能区。宽度低于 900px 时变为纵向结构，蓝图压缩而不完全消失；宽度低于 560px 时只保留核心回路与简短说明，表单保持自然文档滚动。登录后页面的桌面侧栏默认 254px，展开时允许在 220–360px 内调整，收起后为 76px；调整只改变共享侧栏与工作区交界，不挤压或重排侧栏内部控件。900px 以下固定使用 76px 窄栏，560px 以下隐藏侧栏并保留既有替代导航策略。内容继续使用 105rem 上限；媒体、错误提示、按钮忙碌态和滚动条均保留稳定几何。

## Elevation & Depth

常规产品表面以边框和轻微色阶区分，既有 `--shadow` 只用于主要面板。登录外壳允许一次更深的环境阴影，将系统从深蓝页面背景中抬起；左侧深度来自工程网格、线宽和有限光晕，而不是堆叠半透明卡片。表格、表单字段与长文本区禁止装饰性发光。

## Shapes

控件使用 10px 左右圆角，常规面板使用 13px，登录外壳使用 26px。新图标的六边形结构是品牌形状来源，但六边形只用于 Agent 节点与协作核心，不扩散到每张卡片。线条默认 1px–1.5px，焦点环宽度至少 3px 且与边框保持偏移。

## Components

### Foundational visual states

交互控件必须具备默认、悬停、键盘焦点、按下、禁用和忙碌状态。焦点使用 `focus` 令牌且不被阴影吞没。忙碌按钮保持原尺寸并由 Element Plus 的加载状态提供可感知反馈；错误保留在表单内并与字段或表单范围关联。默认加载使用稳定区域内的应用自有指示器，不启用骨架屏。

### Buttons and actions

主动作使用实心 `primary`，次动作使用中性描边或文字按钮；危险动作仅使用 `danger` 语义且与安全主动作分隔。按钮文案用真实动词，如“进入学习空间”“注册并开始诊断”。图标按钮必须有中文可访问名称，忙碌时不改变宽高。

### Navigation and data display

共享导航继续使用 Element Plus 图标和当前路由高亮。新软件图标只作为产品身份标识，不替代导航语义图标。表格和图表优先保证比较关系与证据可读性，窄屏变形必须保留原动作和完整值访问路径。

### Forms and overlays

表单由 Element Plus `el-form`/`el-form-item` 统一校验，原生校验气泡关闭；密码默认遮罩，使用库自带的键盘可访问显示/隐藏按钮。登录失败在表单内展示，保留账号输入并避免重复提交。弹层、消息和确认继续使用 Element Plus 的共享实现，不调用浏览器原生对话框。

### Iconography

产品功能图标统一使用 `@element-plus/icons-vue` 的线性图标。软件品牌使用 `/app-icon.png`。协作蓝图内的节点图形为无文字也可辨认的装饰性线稿，但旁边始终保留中文角色名称；不以图标单独承载业务状态。

### Motion

协作蓝图允许一组持续、低速的环路信号动画，用于表达证据在多个智能体节点之间流转；信号以有明确朝向的陨石形态沿圆角环路运动（三色对应证据/数据/反馈），由连续亮芯和扩散尾气组成拖尾。陨石、亮芯和尾气共用同一条曲线路径，进入节点拐角时同步转弯，尾气短暂保留后逐级淡出；节点只做轻微呼吸，不随机漂移。蓝图网格以极低速率做无缝平移，并辅以周期性的淡入扫描线表达“系统在线”；这些均为低速、克制的装饰性动效，不引入随机粒子或高频闪烁。微交互为 160–240ms，页面进入不超过 300ms。`prefers-reduced-motion: reduce` 下停止路径传递、节点呼吸、网格平移与扫描，陨石及尾气隐藏，只保留静态完整拓扑。

### Content and data visualization

文案直接说明用户能够完成的任务，并使用“画像、检索、生成、仲裁、证据、反馈”等项目真实词汇。用户可见文案统一使用“多智能体协作”，不强调固定智能体数量；角色或轨迹详情可以按实际结果展示具体职责。技术指标必须附口径或来源，不用装饰性百分比。青色表示信息流，黄色表示通过校验，语义成功/警告/错误仍使用各自令牌并辅以文本。

## Do's and Don'ts

- **Do:** 让结构和动画对应真实的多智能体协作职责与证据流向。
- **Do:** 在品牌表达之外复用 Element Plus、既有布局和运行时语义令牌。
- **Don't:** 用随机粒子、无含义波形或持续闪烁制造“AI 感”。
- **Don't:** 为了视觉冲击削弱表单标签、错误信息、键盘焦点、窄屏可达性或减少动态效果支持。
