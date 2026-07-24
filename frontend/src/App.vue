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
  --bg: #f5f8fd;
  --surface: #ffffff;
  --surface-soft: #f7f9fd;
  --line: #e4ebf5;
  --primary: #3168ee;
  --primary-dark: #2053ca;
  --text: #18233b;
  --muted: #6f7c93;
  --success: #17a673;
  --warning: #e89025;
  --danger: #e24f64;
  --shadow: 0 14px 38px rgba(38, 68, 120, .09);
  font-family: Inter, "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
  color: var(--text);
  background: var(--bg);
}
* { box-sizing: border-box; }
html, body, #app { min-height:100%; margin:0; }
body { background: radial-gradient(circle at 70% 0,#eaf1ff 0,transparent 30%),var(--bg); }
button,input,textarea { font:inherit; }
.panel {
  background:rgba(255,255,255,.94); border:1px solid var(--line); border-radius:18px;
  box-shadow:var(--shadow); padding:22px;
}
.panel-title { display:flex; align-items:center; justify-content:space-between; gap:16px; margin-bottom:18px; }
.panel-title h2,.panel-title h3 { margin:0; }.panel-title p { margin:4px 0 0; color:var(--muted); font-size:13px; }
.grid { display:grid; gap:18px; }.grid.two { grid-template-columns:repeat(2,minmax(0,1fr)); }.grid.three { grid-template-columns:repeat(3,minmax(0,1fr)); }
.metric { padding:18px; border-radius:16px; background:linear-gradient(145deg,#fff,#f4f7fd); border:1px solid var(--line); cursor:pointer; transition:.2s ease; }
.metric:hover,.clickable:hover { transform:translateY(-3px); box-shadow:0 14px 30px rgba(37,78,145,.13); }
.metric strong { display:block; font-size:28px; margin-top:7px; }.muted { color:var(--muted); }
.tag-row { display:flex; gap:8px; flex-wrap:wrap; }
.empty { text-align:center; padding:50px 20px; color:var(--muted); }
.page-enter-active,.page-leave-active { transition: opacity .18s ease, transform .18s ease; }
.page-enter-from { opacity:0; transform:translateY(7px); }.page-leave-to { opacity:0; transform:translateY(-4px); }
@media (max-width:1000px) { .grid.two,.grid.three { grid-template-columns:1fr; } }
</style>
