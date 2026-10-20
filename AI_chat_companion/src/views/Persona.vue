<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import HomeButton from '../components/HomeButton.vue'
import Watermark from '../components/Watermark.vue'
import { apiSavePersona } from '../api.js'

const router = useRouter()

const gender = sessionStorage.getItem('gender')
const isFemale = gender === 'female'

// 性格数据：label 展示，style 仅作后台对话风格标记（UI 不渲染）
const personas = {
  female: [
    { key: 'gentle-sister', label: '温柔姐姐', style: '温柔知心' },
    { key: 'cute-sister', label: '可爱妹妹', style: '可爱俏皮' },
    { key: 'tsundere', label: '傲娇女主', style: '傲娇' },
    { key: 'sexy-sister', label: '性感辣妹', style: '直爽' },
  ],
  male: [
    { key: 'ceo', label: '年上霸总', style: '成熟霸总' },
    { key: 'gentle-brother', label: '温柔哥哥', style: '温柔体贴' },
    { key: 'younger', label: '青春年下', style: '富有活力,少年感' },
    { key: 'same-age', label: '细心同龄', style: '细心的同龄人' },
  ],
}

// 性别与伴侣性别相反：选「女」→男伴侣性格，选「男」→女伴侣性格
const list = isFemale ? personas.male : personas.female

const selected = ref(null)
const modalMsg = ref('')
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

async function onConfirm() {
  if (!selected.value) {
    showModal('请先选择一个性格～')
    return
  }
  const userId = sessionStorage.getItem('current_user_id')
  if (!userId) {
    showModal('请先登录～')
    return
  }
  const item = list.find((p) => p.key === selected.value)
  const persona = { key: item.key, label: item.label, style: item.style }
  // 保存性格到后端 + 会话缓存
  const res = await apiSavePersona(userId, persona)
  if (res.code !== 0) {
    showModal(res.message)
    return
  }
  sessionStorage.setItem('current_persona', JSON.stringify(persona))
  // 跳转页面五（对话主页面）
  router.push('/chat')
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
        <div class="mascot">{{ isFemale ? '👦' : '👧' }}</div>
        <h1 class="title">选择性格</h1>
        <p class="subtitle">为你的专属伴侣选一个人设吧～</p>
      </header>

      <section class="list">
        <button
          v-for="item in list"
          :key="item.key"
          class="option"
          :class="{ active: selected === item.key }"
          @click="selected = item.key"
        >
          <span class="option-label">{{ item.label }}</span>
          <span class="check">✓</span>
        </button>
      </section>

      <button class="submit" :class="{ shake: shaking }" @click="onConfirm">确认</button>
    </main>

    <!-- 居中模态弹窗（校验提示） -->
    <Transition name="modal">
      <div v-if="modalMsg" class="modal-mask" @click.self="modalMsg = ''">
        <div class="modal-card">
          <div class="modal-icon">😢</div>
          <p class="modal-text">{{ modalMsg }}</p>
          <button class="modal-btn" @click="modalMsg = ''">知道了</button>
        </div>
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
  margin: 8px 0 22px;
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

/* ---------- 性格选项列表 ---------- */
.list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 26px;
}

.option {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 18px;
  border-radius: var(--radius-lg);
  border: 2px solid var(--blue-mist);
  background: #fbfdff;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease, background 0.18s ease;
  animation: riseIn 0.6s cubic-bezier(0.22, 0.9, 0.32, 1.15) both;
}
.option:nth-of-type(1) { animation-delay: 0.12s; }
.option:nth-of-type(2) { animation-delay: 0.18s; }
.option:nth-of-type(3) { animation-delay: 0.24s; }
.option:nth-of-type(4) { animation-delay: 0.3s; }

.option:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-soft);
}
.option-label {
  font-size: 17px;
  font-weight: 800;
  color: var(--ink);
}

.check {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  font-size: 13px;
  color: var(--white);
  background: var(--blue);
  border-radius: 50%;
  opacity: 0;
  transform: scale(0.4);
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.option.active {
  border-color: var(--blue);
  background: var(--blue-light);
  box-shadow: 0 8px 20px rgba(77, 159, 255, 0.22);
}
.option.active .check {
  opacity: 1;
  transform: scale(1);
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

/* ---------- 居中模态弹窗 ---------- */
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
