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
:root {
  --bg: #f7f9fc;
  --surface: #ffffff;
  --surface-soft: #f7f9fd;
  --line: #e5ebf4;
  --primary: #2563eb;
  --primary-dark: #2053ca;
  --text: #18233b;
  --muted: #6f7c93;
  --success: #17a673;
  --warning: #e89025;
  --danger: #e24f64;
  --shadow: 0 7px 24px rgba(38, 68, 120, .055);
  font-family: Inter, "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
  color: var(--text);
  background: var(--bg);
}
* { box-sizing: border-box; }
html, body, #app { min-height:100%; margin:0; }
body { background: linear-gradient(135deg,#f8faff,#f5f8fd 50%,#f8faff); }
button,input,textarea { font:inherit; }
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
.el-button{border-radius:8px}.el-button--primary{background:linear-gradient(115deg,#1760ef,#3977f5);border-color:#2868ef}.el-input__wrapper,.el-select__wrapper{border-radius:8px!important}.el-table{--el-table-header-bg-color:#f6f8fc;--el-table-row-hover-bg-color:#f4f7ff;border-radius:10px}.clickable{transition:.18s ease}.clickable:focus-visible,button:focus-visible,a:focus-visible{outline:3px solid rgba(49,104,238,.25);outline-offset:2px}
.page-enter-active,.page-leave-active { transition: opacity .18s ease, transform .18s ease; }
.page-enter-from { opacity:0; transform:translateY(7px); }.page-leave-to { opacity:0; transform:translateY(-4px); }
@media (max-width:1000px) { .grid.two,.grid.three { grid-template-columns:1fr; } }
</style>
