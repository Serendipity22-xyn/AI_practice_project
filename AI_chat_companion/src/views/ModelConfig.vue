<script setup>
import { ref, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import HomeButton from '../components/HomeButton.vue'
import Watermark from '../components/Watermark.vue'

const router = useRouter()

// 三个必填项
const modelName = ref('')
const apiKey = ref('')
const apiUrl = ref('')
// APIkey 是否明文显示
const showKey = ref(false)

const tip = ref('')
const shaking = ref(false)
let tipTimer = null

function showTip(msg) {
  tip.value = msg
  shaking.value = true
  clearTimeout(tipTimer)
  tipTimer = setTimeout(() => {
    tip.value = ''
    shaking.value = false
  }, 2200)
}

function goBack() {
  router.push('/')
}

function onSubmit() {
  // 三项全部不能为空，任一为空即提示并禁止跳转
  if (!modelName.value.trim()) {
    showTip('请填写大模型名称～')
    return
  }
  if (!apiKey.value.trim()) {
    showTip('请填写 APIkey～')
    return
  }
  if (!apiUrl.value.trim()) {
    showTip('请填写调用地址～')
    return
  }

  // 暂存手动配置，登录/注册后提交后端保存
  sessionStorage.setItem('model_type', 'manual')
  sessionStorage.setItem(
    'manual_config',
    JSON.stringify({
      url: apiUrl.value.trim(),
      model: modelName.value.trim(),
      api_key: apiKey.value.trim(),
    })
  )
  // 校验通过，跳转页面二（登录 / 注册页）
  router.push('/login')
}

onUnmounted(() => clearTimeout(tipTimer))
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
        <div class="mascot">🔧</div>
        <h1 class="title">模型配置</h1>
        <p class="subtitle">填好信息，配置你的专属大模型～</p>
      </header>

      <section class="form">
        <label class="field">
          <span class="field-label">大模型名称</span>
          <input
            v-model="modelName"
            class="input"
            type="text"
            placeholder="请输入大模型名称"
          />
        </label>

        <label class="field">
          <span class="field-label">APIkey</span>
          <div class="input-wrap">
            <input
              v-model="apiKey"
              class="input input-key"
              :type="showKey ? 'text' : 'password'"
              placeholder="请输入 APIkey"
            />
            <button
              class="eye"
              type="button"
              :aria-label="showKey ? '隐藏 APIkey' : '显示 APIkey'"
              @click="showKey = !showKey"
            >
              {{ showKey ? '🙈' : '👁️' }}
            </button>
          </div>
        </label>

        <label class="field">
          <span class="field-label">调用地址</span>
          <input
            v-model="apiUrl"
            class="input"
            type="text"
            placeholder="例如：https://api.example.com"
          />
        </label>
      </section>

      <button class="submit" :class="{ shake: shaking }" @click="onSubmit">前往体验</button>
    </main>

    <Transition name="toast">
      <div v-if="tip" class="toast">{{ tip }}</div>
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
  margin: 10px 0 24px;
  animation: riseIn 0.6s cubic-bezier(0.22, 0.9, 0.32, 1.15) both;
}

.mascot {
  width: 72px;
  height: 72px;
  margin: 0 auto 12px;
  font-size: 38px;
  line-height: 72px;
  background: linear-gradient(180deg, #eaf4ff, #d3e9ff);
  border-radius: 26px;
  box-shadow: inset 0 -3px 0 rgba(47, 127, 224, 0.12);
  animation: bob 3s ease-in-out infinite;
}

.title {
  font-size: 28px;
  color: var(--blue-dark);
  letter-spacing: 1px;
}

.subtitle {
  margin-top: 6px;
  font-size: 14px;
  color: var(--ink-soft);
}

/* ---------- 表单 ---------- */
.form {
  display: flex;
  flex-direction: column;
  gap: 18px;
  margin-bottom: 26px;
}

.field {
  display: block;
  animation: riseIn 0.6s cubic-bezier(0.22, 0.9, 0.32, 1.15) both;
}
.field:nth-of-type(1) { animation-delay: 0.12s; }
.field:nth-of-type(2) { animation-delay: 0.2s; }
.field:nth-of-type(3) { animation-delay: 0.28s; }

.field-label {
  display: block;
  font-size: 14px;
  font-weight: 800;
  color: var(--ink);
  margin-bottom: 8px;
}

.input {
  width: 100%;
  padding: 14px 16px;
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

/* APIkey 输入框 + 眼睛切换 */
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

/* ---------- 前往体验按钮 ---------- */
.submit {
  width: 100%;
  padding: 16px;
  font-size: 18px;
  font-weight: 900;
  letter-spacing: 4px;
  color: var(--white);
  background: linear-gradient(135deg, #6db5ff, #4d9fff 55%, #2f7fe0);
  border-radius: 999px;
  box-shadow: 0 10px 24px rgba(47, 127, 224, 0.32);
  transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
  animation: riseIn 0.6s cubic-bezier(0.22, 0.9, 0.32, 1.15) 0.36s both;
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

/* ---------- 提示浮层 ---------- */
.toast {
  position: fixed;
  top: 28px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 22px;
  font-size: 14px;
  font-weight: 700;
  color: var(--white);
  background: rgba(43, 58, 74, 0.92);
  border-radius: 999px;
  box-shadow: 0 10px 26px rgba(43, 58, 74, 0.28);
  z-index: 10;
}
.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-12px);
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
