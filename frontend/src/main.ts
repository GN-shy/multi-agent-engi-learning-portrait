import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(ElementPlus)

async function bootstrap() {
  app.use(router)
  await router.isReady()
  app.mount('#app')
}

void bootstrap()
