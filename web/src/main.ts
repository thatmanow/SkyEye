import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'
import * as ElIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import '@/styles/main.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })
for (const [name, comp] of Object.entries(ElIconsVue)) {
  app.component(name, comp)
}
app.mount('#app')
