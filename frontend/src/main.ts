import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import { useUserStore } from '@/stores/user'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(ElementPlus)

async function bootstrap() {
  const user = useUserStore(pinia)
  await user.initialize()
  router.beforeEach((to) => {
    if (to.meta.public) {
      if (to.path === '/login' && to.query.reset === '1') return true
      return user.isLoggedIn && to.path === '/login' ? '/' : true
    }
    return user.isLoggedIn ? true : { path: '/login', query: { redirect: to.fullPath } }
  })
  app.use(router)
  await router.isReady()
  app.mount('#app')
}

void bootstrap()
