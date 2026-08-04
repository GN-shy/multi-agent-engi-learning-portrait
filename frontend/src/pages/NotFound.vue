<template>
  <div class="not-found">
    <div class="code">404</div>
    <h2>页面未找到</h2>
    <p>你访问的页面不存在或已被移除</p>
    <el-button type="primary" @click="$router.replace('/')">返回首页</el-button>
  </div>
</template>

<style scoped>
.not-found {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: radial-gradient(circle at 50% 40%, #dce9ff, transparent 50%), #f7f9fd;
}
.code {
  font-size: 96px;
  font-weight: 900;
  background: linear-gradient(145deg, #2768ff, #6c4cf4);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
h2 { margin: 0; font-size: 24px; color: #152039; }
p { margin: 0 0 8px; color: var(--muted); }
</style>
