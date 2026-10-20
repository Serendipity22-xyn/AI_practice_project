<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import HomeButton from '../components/HomeButton.vue'
import Watermark from '../components/Watermark.vue'
import { apiRegister, apiLogin, apiSaveModelConfig } from '../api.js'

const router = useRouter()

// 当前表单：'login' | 'register'
const mode = ref('login')

// 登录字段
const loginId = ref('')
const loginPwd = ref('')
const loginCompanion = ref('')

// 注册字段
const regName = ref('')
const regPwd = ref('')
const regPwd2 = ref('')
const regCompanion = ref('')

// 密码明文开关（各自独立）
const showLoginPwd = ref(false)
const showRegPwd = ref(false)
const showRegPwd2 = ref(false)

// 居中弹窗（校验失败提示）
const modalMsg = ref('')
// 右下角弹窗（注册成功展示 ID）
const successId = ref('')

const shaking = ref(false)

function showModal(msg) {
  modalMsg.value = msg
  shaking.value = true
  setTimeout(() => {
    shaking.value = false
  }, 450)
}

function goBack() {
  router.back()
}

// 跳转：未选性别则提示；hasPersona 为 true 直接进对话页，否则进性格选择
function goNext(hasPersona) {
  const gender = sessionStorage.getItem('gender')
  if (!gender) {
    showModal('请先返回首页选择性别～')
    return
  }
  if (hasPersona) {
    router.push('/chat')
  } else {
    router.push('/persona')
  }
}

async function onLogin() {
  if (!loginId.value.trim()) {
    showModal('请填写用户 ID～')
    return
  }
  if (!loginPwd.value.trim()) {
    showModal('请填写密码～')
    return
  }
  // 调用后端登录接口
  const res = await apiLogin(loginId.value.trim(), loginPwd.value.trim())
  if (res.code !== 0) {
    showModal(res.message)
    return
  }
  const data = res.data
  sessionStorage.setItem('current_user_id', data.user_id)
  sessionStorage.setItem('current_companion', data.companion_name)
  if (data.persona) sessionStorage.setItem('current_persona', JSON.stringify(data.persona))
  if (data.model_config) sessionStorage.setItem('model_config', JSON.stringify(data.model_config))
  if (data.chat_history) sessionStorage.setItem('chat_history', JSON.stringify(data.chat_history))
  goNext(!!data.persona)
}

async function onRegister() {
  if (!regName.value.trim()) {
    showModal('请填写用户名～')
    return
  }
  if (!regPwd.value.trim()) {
    showModal('请填写密码～')
    return
  }
  if (!regPwd2.value.trim()) {
    showModal('请再次输入密码～')
    return
  }
  if (!regCompanion.value.trim()) {
    showModal('请填写伴侣名字～')
    return
  }
  if (regPwd.value !== regPwd2.value) {
    showModal('两次输入的密码不一致～')
    return
  }

  // 调用后端注册接口
  const res = await apiRegister(regName.value.trim(), regPwd.value.trim(), regCompanion.value.trim())
  if (res.code !== 0) {
    showModal(res.message)
    return
  }
  const user_id = res.data.user_id
  sessionStorage.setItem('current_user_id', user_id)
  sessionStorage.setItem('current_companion', res.data.companion_name)

  // 保存模型配置（注册后提交暂存的配置）
  const modelType = sessionStorage.getItem('model_type') || 'default'
  let manualConfig = null
  try {
    manualConfig = JSON.parse(sessionStorage.getItem('manual_config') || 'null')
  } catch {
    manualConfig = null
  }
  await apiSaveModelConfig(user_id, modelType, manualConfig)

  // 弹窗展示 ID
  successId.value = user_id
}

function enterChat() {
  successId.value = ''
  goNext(false)
}
</script>

<template>
  <div class="page">
    <HomeButton />
    <Watermark />
    <!-- 背景装饰：云朵 + 气泡 -->
    <div class="bg" aria-hidden="true">
      <span class="cloud cloud-1"></span>
      <span class="cloud cloud-2"></span>
      <span class="cloud cloud-3"></span>
      <span class="bubble bubble-1"></span>
      <span class="bubble bubble-2"></span>
      <span class="bubble bubble-3"></span>
      <span class="bubble bubble-4"></span>
    </div>

    <main class="card">
      <button class="back" @click="goBack">
        <span class="back-arrow">←</span>返回
      </button>

      <header class="hero">
        <div class="mascot">🐾</div>
        <h1 class="title">欢迎回来</h1>
        <p class="subtitle">登录或注册，开启你们的专属时光～</p>
      </header>

      <!-- 登录 / 注册 切换 -->
      <div class="tabs">
        <button class="tab" :class="{ active: mode === 'login' }" @click="mode = 'login'">登录</button>
        <button class="tab" :class="{ active: mode === 'register' }" @click="mode = 'register'">注册</button>
      </div>

      <!-- 登录表单 -->
      <form v-if="mode === 'login'" class="form" @submit.prevent="onLogin">
        <label class="field">
          <span class="field-label">用户 ID</span>
          <input v-model="loginId" class="input" type="text" placeholder="请输入 8 位用户 ID" />
        </label>
        <label class="field">
          <span class="field-label">密码</span>
          <div class="input-wrap">
            <input
              v-model="loginPwd"
              class="input input-key"
              :type="showLoginPwd ? 'text' : 'password'"
              placeholder="请输入密码"
            />
            <button class="eye" type="button" @click="showLoginPwd = !showLoginPwd">
              {{ showLoginPwd ? '🙈' : '👁️' }}
            </button>
          </div>
        </label>
        <label class="field">
          <span class="field-label">伴侣名字</span>
          <input v-model="loginCompanion" class="input" type="text" placeholder="给你的伴侣起个名字吧～" />
        </label>
        <button class="submit" :class="{ shake: shaking }" type="submit">确认</button>
      </form>

      <!-- 注册表单 -->
      <form v-else class="form" @submit.prevent="onRegister">
        <label class="field">
          <span class="field-label">用户名</span>
          <input v-model="regName" class="input" type="text" placeholder="请输入用户名" />
        </label>
        <label class="field">
          <span class="field-label">密码</span>
          <div class="input-wrap">
            <input
              v-model="regPwd"
              class="input input-key"
              :type="showRegPwd ? 'text' : 'password'"
              placeholder="请输入密码"
            />
            <button class="eye" type="button" @click="showRegPwd = !showRegPwd">
              {{ showRegPwd ? '🙈' : '👁️' }}
            </button>
          </div>
        </label>
        <label class="field">
          <span class="field-label">密码确认</span>
          <div class="input-wrap">
            <input
              v-model="regPwd2"
              class="input input-key"
              :type="showRegPwd2 ? 'text' : 'password'"
              placeholder="请再次输入密码"
            />
            <button class="eye" type="button" @click="showRegPwd2 = !showRegPwd2">
              {{ showRegPwd2 ? '🙈' : '👁️' }}
            </button>
          </div>
        </label>
        <label class="field">
          <span class="field-label">伴侣名字</span>
          <input v-model="regCompanion" class="input" type="text" placeholder="给你的伴侣起个名字吧～" />
        </label>
        <button class="submit" :class="{ shake: shaking }" type="submit">确认</button>
      </form>
    </main>

    <!-- 居中模态弹窗（校验失败提示） -->
    <Transition name="modal">
      <div v-if="modalMsg" class="modal-mask" @click.self="modalMsg = ''">
        <div class="modal-card">
          <div class="modal-icon">😢</div>
          <p class="modal-text">{{ modalMsg }}</p>
          <button class="modal-btn" @click="modalMsg = ''">知道了</button>
        </div>
      </div>
    </Transition>

    <!-- 右下角弹窗（注册成功展示 ID） -->
    <Transition name="notify">
      <div v-if="successId" class="notify">
        <div class="notify-title">🎉 注册成功</div>
        <p class="notify-text">您的用户 ID：<b>{{ successId }}</b></p>
        <button class="notify-btn" @click="enterChat">进入对话</button>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 20px;
  overflow: hidden;
}

/* ---------- 背景云朵 / 气泡 ---------- */
.bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.cloud {
  position: absolute;
  width: 130px;
  height: 44px;
  background: rgba(255, 255, 255, 0.82);
  border-radius: 44px;
  filter: blur(0.5px);
  animation: drift 18s ease-in-out infinite;
}
.cloud::before,
.cloud::after {
  content: '';
  position: absolute;
  background: inherit;
  border-radius: 50%;
}
.cloud::before {
  width: 56px;
  height: 56px;
  top: -24px;
  left: 20px;
}
.cloud::after {
  width: 38px;
  height: 38px;
  top: -16px;
  right: 18px;
}
.cloud-1 { top: 12%; left: -60px; opacity: 0.9; }
.cloud-2 { top: 26%; right: -50px; transform: scale(0.8); animation-delay: -6s; }
.cloud-3 { bottom: 14%; left: 8%; transform: scale(0.65); animation-delay: -12s; }

.bubble {
  position: absolute;
  bottom: -40px;
  border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.9), rgba(77, 159, 255, 0.16));
  animation: rise 12s linear infinite;
}
.bubble-1 { left: 12%; width: 22px; height: 22px; animation-duration: 14s; }
.bubble-2 { left: 30%; width: 12px; height: 12px; animation-duration: 11s; animation-delay: -3s; }
.bubble-3 { left: 62%; width: 18px; height: 18px; animation-duration: 16s; animation-delay: -7s; }
.bubble-4 { left: 82%; width: 14px; height: 14px; animation-duration: 13s; animation-delay: -5s; }

/* ---------- 主卡片 ---------- */
.card {
  position: relative;
  width: 100%;
  max-width: 440px;
  background: var(--white);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  padding: 24px 30px 32px;
}

/* ---------- 返回按钮 ---------- */
.back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 800;
  color: var(--blue-deep);
  background: var(--blue-light);
  border-radius: 999px;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.back:hover {
  transform: translateX(-2px);
  box-shadow: var(--shadow-soft);
}
.back-arrow {
  font-size: 16px;
  line-height: 1;
}

/* ---------- 标题区 ---------- */
.hero {
  text-align: center;
  margin: 8px 0 20px;
  animation: riseIn 0.6s cubic-bezier(0.22, 0.9, 0.32, 1.15) both;
}

.mascot {
  width: 68px;
  height: 68px;
  margin: 0 auto 12px;
  font-size: 36px;
  line-height: 68px;
  background: linear-gradient(180deg, #eaf4ff, #d3e9ff);
  border-radius: 24px;
  box-shadow: inset 0 -3px 0 rgba(47, 127, 224, 0.12);
  animation: bob 3s ease-in-out infinite;
}

.title {
  font-size: 27px;
  color: var(--blue-dark);
  letter-spacing: 1px;
}

.subtitle {
  margin-top: 6px;
  font-size: 14px;
  color: var(--ink-soft);
}

/* ---------- 登录 / 注册切换 ---------- */
.tabs {
  display: flex;
  gap: 6px;
  background: var(--blue-light);
  padding: 5px;
  border-radius: 999px;
  margin-bottom: 22px;
  animation: riseIn 0.6s cubic-bezier(0.22, 0.9, 0.32, 1.15) 0.1s both;
}

.tab {
  flex: 1;
  padding: 10px;
  font-size: 15px;
  font-weight: 800;
  color: var(--ink-soft);
  border-radius: 999px;
  transition: color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
}
.tab.active {
  color: var(--white);
  background: linear-gradient(135deg, #6db5ff, #4d9fff);
  box-shadow: 0 6px 16px rgba(77, 159, 255, 0.3);
}

/* ---------- 表单 ---------- */
.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.field {
  display: block;
  animation: riseIn 0.6s cubic-bezier(0.22, 0.9, 0.32, 1.15) both;
}
.field:nth-of-type(1) { animation-delay: 0.16s; }
.field:nth-of-type(2) { animation-delay: 0.22s; }
.field:nth-of-type(3) { animation-delay: 0.28s; }
.field:nth-of-type(4) { animation-delay: 0.34s; }

.field-label {
  display: block;
  font-size: 14px;
  font-weight: 800;
  color: var(--ink);
  margin-bottom: 8px;
}

.input {
  width: 100%;
  padding: 13px 16px;
  font-size: 15px;
  font-family: inherit;
  color: var(--ink);
  background: #fbfdff;
  border: 2px solid var(--blue-mist);
  border-radius: var(--radius-md);
  outline: none;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}
.input::placeholder {
  color: #b6c6d6;
}
.input:focus {
  border-color: var(--blue);
  background: #fff;
  box-shadow: 0 0 0 4px rgba(77, 159, 255, 0.12);
}

.input-wrap {
  position: relative;
}
.input-key {
  padding-right: 48px;
}
.eye {
  position: absolute;
  top: 50%;
  right: 14px;
  transform: translateY(-50%);
  font-size: 18px;
  line-height: 1;
  opacity: 0.85;
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.eye:hover {
  opacity: 1;
  transform: translateY(-50%) scale(1.15);
}

/* ---------- 确认按钮 ---------- */
.submit {
  width: 100%;
  padding: 15px;
  font-size: 18px;
  font-weight: 900;
  letter-spacing: 4px;
  color: var(--white);
  background: linear-gradient(135deg, #6db5ff, #4d9fff 55%, #2f7fe0);
  border-radius: 999px;
  box-shadow: 0 10px 24px rgba(47, 127, 224, 0.32);
  transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
  animation: riseIn 0.6s cubic-bezier(0.22, 0.9, 0.32, 1.15) 0.4s both;
}
.submit:hover {
  filter: brightness(1.05);
  transform: translateY(-2px);
  box-shadow: 0 14px 30px rgba(47, 127, 224, 0.4);
}
.submit:active {
  transform: translateY(1px) scale(0.98);
  box-shadow: 0 6px 16px rgba(47, 127, 224, 0.28);
}
.submit.shake {
  animation: shake 0.45s ease;
}

/* ---------- 居中模态弹窗（校验失败） ---------- */
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(43, 58, 74, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  z-index: 30;
}
.modal-card {
  width: 100%;
  max-width: 320px;
  background: var(--white);
  border-radius: var(--radius-lg);
  padding: 28px 24px;
  text-align: center;
  box-shadow: var(--shadow-card);
}
.modal-icon {
  font-size: 42px;
  line-height: 1;
  margin-bottom: 12px;
}
.modal-text {
  font-size: 15px;
  font-weight: 700;
  color: var(--ink);
  line-height: 1.6;
  margin-bottom: 20px;
}
.modal-btn {
  padding: 10px 32px;
  font-size: 15px;
  font-weight: 800;
  color: var(--white);
  background: linear-gradient(135deg, #6db5ff, #4d9fff);
  border-radius: 999px;
  box-shadow: 0 8px 18px rgba(47, 127, 224, 0.3);
  transition: transform 0.15s ease, filter 0.15s ease;
}
.modal-btn:hover {
  filter: brightness(1.05);
  transform: translateY(-1px);
}
.modal-btn:active {
  transform: translateY(1px) scale(0.98);
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}
.modal-enter-active .modal-card,
.modal-leave-active .modal-card {
  transition: transform 0.2s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from .modal-card,
.modal-leave-to .modal-card {
  transform: scale(0.9);
}

/* ---------- 右下角弹窗（注册成功） ---------- */
.notify {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: min(320px, calc(100vw - 40px));
  background: var(--white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 22px 20px;
  text-align: center;
  z-index: 30;
}
.notify-title {
  font-size: 17px;
  font-weight: 900;
  color: var(--blue-dark);
  margin-bottom: 10px;
}
.notify-text {
  font-size: 14px;
  color: var(--ink-soft);
  margin-bottom: 18px;
}
.notify-text b {
  color: var(--blue-deep);
  font-size: 18px;
  letter-spacing: 1px;
}
.notify-btn {
  width: 100%;
  padding: 11px;
  font-size: 15px;
  font-weight: 800;
  color: var(--white);
  background: linear-gradient(135deg, #6db5ff, #4d9fff);
  border-radius: 999px;
  box-shadow: 0 8px 18px rgba(47, 127, 224, 0.3);
  transition: transform 0.15s ease, filter 0.15s ease;
}
.notify-btn:hover {
  filter: brightness(1.05);
  transform: translateY(-1px);
}
.notify-btn:active {
  transform: translateY(1px) scale(0.98);
}

.notify-enter-active,
.notify-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.notify-enter-from,
.notify-leave-to {
  opacity: 0;
  transform: translate(-50%, -48%) scale(0.9);
}

/* ---------- 动画 ---------- */
@keyframes riseIn {
  from { opacity: 0; transform: translateY(24px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes bob {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}
@keyframes drift {
  0%, 100% { transform: translateX(0); }
  50% { transform: translateX(30px); }
}
@keyframes rise {
  0% { transform: translateY(0); opacity: 0; }
  15% { opacity: 1; }
  100% { transform: translateY(-110vh); opacity: 0; }
}
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-8px); }
  40% { transform: translateX(8px); }
  60% { transform: translateX(-5px); }
  80% { transform: translateX(5px); }
}

@media (max-width: 480px) {
  .card { padding: 20px 22px 28px; }
  .title { font-size: 24px; }
}
</style>
