import { createRouter, createWebHashHistory } from 'vue-router'
import Home from '../views/Home.vue'
import ModelConfig from '../views/ModelConfig.vue'
import Login from '../views/Login.vue'
import Persona from '../views/Persona.vue'
import Chat from '../views/Chat.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', name: 'home', component: Home },
    // 页面一：模型配置页
    { path: '/model-config', name: 'model-config', component: ModelConfig },
    // 页面二：登录 / 注册页
    { path: '/login', name: 'login', component: Login },
    // 页面三 / 页面四：性格选项页（共用，按性别渲染女/男选项）
    { path: '/persona', name: 'persona', component: Persona },
    // 页面五：对话主页面（占位，后续迭代）
    { path: '/chat', name: 'chat', component: Chat },
  ],
})

export default router
