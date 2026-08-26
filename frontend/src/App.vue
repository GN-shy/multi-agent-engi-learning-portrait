<template>
  <el-config-provider :locale="zhCn">
    <RouterView v-slot="{ Component, route }">
      <Transition name="page" mode="out-in">
        <component :is="Component" :key="route.fullPath" />
      </Transition>
    </RouterView>
  </el-config-provider>
</template>

<script setup lang="ts">
import zhCn from 'element-plus/es/locale/lang/zh-cn'
</script>

<style>
@font-face {
  font-family: "Space Grotesk";
  font-style: normal;
  font-weight: 300 700;
  font-display: swap;
  src: url("/fonts/space-grotesk-latin.woff2") format("woff2");
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
:root {
  --bg: #f7f9fc;
  --surface: #ffffff;
  --surface-soft: #f7f9fd;
  --line: #e5ebf4;
  --primary: #2563eb;
  --primary-dark: #2053ca;
  --brand-navy: #0b2c63;
  --brand-cyan: #00aeef;
  --brand-yellow: #ffd500;
  --canvas-deep: #061328;
  --focus: #4c82ff;
  --text: #18233b;
  --muted: #66748b;
  --success: #17a673;
  --warning: #e89025;
  --danger: #e24f64;
  --shadow: 0 7px 24px rgba(38, 68, 120, .055);
  --font-display: "Space Grotesk", "HarmonyOS Sans SC", "MiSans", "PingFang SC", "Microsoft YaHei UI", sans-serif;
  --font-body: Inter, "HarmonyOS Sans SC", "MiSans", "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
  --font-utility: "Space Grotesk", "HarmonyOS Sans SC", "MiSans", "PingFang SC", sans-serif;
  --radius-control: 10px;
  --radius-panel: 13px;
  --radius-auth-shell: 26px;
  --auth-shell-max: 1480px;
  --scrollbar-track: #edf2f8;
  --scrollbar-thumb: #aebbd0;
  --scrollbar-thumb-hover: #8698b4;
  --scrollbar-thumb-active: #657b9d;
  font-family: var(--font-body);
  color: var(--text);
  background: var(--bg);
}
* {
  box-sizing: border-box;
  scrollbar-color: var(--scrollbar-thumb) var(--scrollbar-track);
  scrollbar-width: thin;
}
html { scrollbar-gutter: stable; }
html, body, #app { min-height:100%; margin:0; }
body { background: linear-gradient(135deg,#f8faff,#f5f8fd 50%,#f8faff); }
button,input,textarea { font:inherit; }
button:not(:disabled), a[href] { cursor: pointer; }
*::-webkit-scrollbar { width:10px; height:10px; }
*::-webkit-scrollbar-track { background:var(--scrollbar-track); }
*::-webkit-scrollbar-thumb { min-height:32px; border:2px solid var(--scrollbar-track); border-radius:999px; background:var(--scrollbar-thumb); }
*::-webkit-scrollbar-thumb:hover { background:var(--scrollbar-thumb-hover); }
*::-webkit-scrollbar-thumb:active { background:var(--scrollbar-thumb-active); }
.panel {
  background:rgba(255,255,255,.97); border:1px solid var(--line); border-radius:13px;
  box-shadow:var(--shadow); padding:18px;
}
.panel-title { display:flex; align-items:center; justify-content:space-between; gap:14px; margin-bottom:14px; }
.panel-title h2,.panel-title h3 { margin:0; font-size:16px; }.panel-title p { margin:4px 0 0; color:var(--muted); font-size:11px; }
.grid { display:grid; gap:18px; }.grid.two { grid-template-columns:repeat(2,minmax(0,1fr)); }.grid.three { grid-template-columns:repeat(3,minmax(0,1fr)); }
.metric { padding:16px; border-radius:12px; background:linear-gradient(145deg,#fff,#f4f7fd); border:1px solid var(--line); cursor:pointer; transition:.2s ease; }
.metric:hover,.clickable:hover { transform:translateY(-3px); box-shadow:0 14px 30px rgba(37,78,145,.13); }
.metric strong { display:block; font-size:28px; margin-top:7px; }.muted { color:var(--muted); }
.tag-row { display:flex; gap:8px; flex-wrap:wrap; }
.empty { text-align:center; padding:50px 20px; color:var(--muted); }
.el-button{border-radius:8px}.el-button--primary{background:linear-gradient(115deg,#1760ef,#3977f5);border-color:#2868ef}.el-input__wrapper,.el-select__wrapper{border-radius:8px}.el-table{--el-table-header-bg-color:#f6f8fc;--el-table-row-hover-bg-color:#f4f7ff;border-radius:10px}.clickable{transition:.18s ease}.clickable:focus-visible,button:focus-visible,a:focus-visible{outline:3px solid rgba(49,104,238,.25);outline-offset:2px}
.page-enter-active,.page-leave-active { transition: opacity .18s ease, transform .18s ease; }
.page-enter-from { opacity:0; transform:translateY(7px); }.page-leave-to { opacity:0; transform:translateY(-4px); }
@media (max-width:1000px) { .grid.two,.grid.three { grid-template-columns:1fr; } }
@media (prefers-reduced-motion: reduce) {
  .page-enter-active,.page-leave-active { transition:none; }
  .page-enter-from,.page-leave-to { opacity:1; transform:none; }
}
@media (forced-colors: active) {
  * { scrollbar-color:auto; }
  *::-webkit-scrollbar-track,
  *::-webkit-scrollbar-thumb { background:Canvas; border-color:CanvasText; }
}
</style>
