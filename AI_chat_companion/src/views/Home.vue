<script setup>
import { ref, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import Watermark from '../components/Watermark.vue'

const router = useRouter()

// 性别：'male' | 'female'（默认未选）
const gender = ref(null)
// 大模型：'manual' | 'default'（默认未选）
const model = ref(null)

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

function pickGender(val) {
  gender.value = val
  sessionStorage.setItem('gender', val)
}

function onSubmit() {
  // 校验 1：性别必选
  if (!gender.value) {
    showTip('请先选择性别哦～')
    return
  }
  // 校验 2：大模型方式必选
  if (!model.value) {
    showTip('请先选择大模型方式～')
    return
  }

  // 严格执行跳转逻辑，不得自行修改：
  // 手动添加 + 性别 -> 页面一（模型配置页）
  // 默认设置 + 性别 -> 页面二（登录 / 注册页）
  if (model.value === 'manual') {
    router.push({ path: '/model-config', query: { gender: gender.value, model: model.value } })
  } else {
    // 默认设置：仅标记模型类型，具体配置由后端使用智谱默认
    sessionStorage.setItem('model_type', 'default')
    router.push('/login')
  }
}

// ---------- 清空用户数据 ----------
const clearOpen = ref(false)
const clearId = ref('')

function openClear() {
  clearId.value = ''
  clearOpen.value = true
}

function confirmClear() {
  const id = clearId.value.trim()
  if (!id) {
    showTip('请输入用户 ID～')
    return
  }

  // 1) 从已注册 ID 列表移除
  let ids = []
  try {
    ids = JSON.parse(sessionStorage.getItem('registered_ids') || '[]')
  } catch {
    ids = []
  }
  const foundId = ids.includes(id)
  sessionStorage.setItem('registered_ids', JSON.stringify(ids.filter((x) => x !== id)))

  // 2) 依据 ID -> 伴侣名字 关联，清理对应性格配置
  let idMap = {}
  try {
    idMap = JSON.parse(sessionStorage.getItem('id_to_companion') || '{}')
  } catch {
    idMap = {}
  }
  const companion = idMap[id]
  if (companion) {
    let personaMap = {}
    try {
      personaMap = JSON.parse(sessionStorage.getItem('persona_map') || '{}')
    } catch {
      personaMap = {}
    }
    delete personaMap[companion]
    sessionStorage.setItem('persona_map', JSON.stringify(personaMap))
    delete idMap[id]
    sessionStorage.setItem('id_to_companion', JSON.stringify(idMap))
  }

  clearOpen.value = false
  if (foundId || companion) {
    showTip('已清空该用户数据～')
  } else {
    showTip('未找到该用户 ID～')
  }
}

onUnmounted(() => clearTimeout(tipTimer))
</script>

<template>
  <div class="page">
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
      <span class="bubble bubble-5"></span>
    </div>

    <main class="card">
      <header class="hero">
        <div class="mascot">🤖</div>
        <h1 class="title">AI 智能伴侣</h1>
        <p class="subtitle">选好你的专属伴侣，马上开始吧～</p>
      </header>

      <!-- 板块 1：性别选择 -->
      <section class="block">
        <h2 class="block-title"><span class="badge">1</span>您的性别是</h2>
        <div class="gender-group">
          <button
            class="gender"
            :class="{ active: gender === 'male' }"
            @click="pickGender('male')"
          >
            <span class="gender-emoji">👦</span>
            <span class="gender-name">男</span>
            <span class="check">✓</span>
          </button>
          <button
            class="gender"
            :class="{ active: gender === 'female' }"
            @click="pickGender('female')"
          >
            <span class="gender-emoji">👧</span>
            <span class="gender-name">女</span>
            <span class="check">✓</span>
          </button>
        </div>
      </section>

      <!-- 板块 2：大模型选择 -->
      <section class="block">
        <h2 class="block-title"><span class="badge">2</span>选择大模型</h2>
        <div class="model-group">
          <button
            class="model"
            :class="{ active: model === 'manual' }"
            @click="model = 'manual'"
          >
            <span class="model-emoji">⚙️</span>
            <span class="model-name">手动添加</span>
          </button>

          <div class="model-col">
            <button
              class="model"
              :class="{ active: model === 'default' }"
              @click="model = 'default'"
            >
              <span class="model-emoji">✨</span>
              <span class="model-name">默认设置</span>
            </button>
            <p class="model-note">智谱免费大模型，高峰期可能存在业务繁忙</p>
          </div>
        </div>
      </section>

      <!-- 板块 3：确定提交 -->
      <button class="submit" :class="{ shake: shaking }" @click="onSubmit">确定</button>

      <button class="clear-link" @click="openClear">🗑️ 清空用户数据</button>
    </main>

    <Transition name="toast">
      <div v-if="tip" class="toast">{{ tip }}</div>
    </Transition>

    <!-- 清空用户数据弹窗 -->
    <Transition name="modal">
      <div v-if="clearOpen" class="modal-mask" @click.self="clearOpen = false">
        <div class="modal-card">
          <div class="modal-icon">🗑️</div>
          <h3 class="modal-title">清空用户数据</h3>
          <p class="modal-desc">输入要清空的用户 ID（8 位数字）</p>
          <input v-model="clearId" class="modal-input" type="text" placeholder="请输入用户 ID" />
          <div class="modal-actions">
            <button class="modal-cancel" @click="clearOpen = false">取消</button>
            <button class="modal-ok" @click="confirmClear">确认清空</button>
          </div>
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
.bubble-4 { left: 80%; width: 10px; height: 10px; animation-duration: 12s; animation-delay: -5s; }
.bubble-5 { left: 90%; width: 26px; height: 26px; animation-duration: 18s; animation-delay: -9s; }

/* ---------- 主卡片 ---------- */
.card {
  position: relative;
  width: 100%;
  max-width: 440px;
  background: var(--white);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  padding: 36px 30px 32px;
}

.hero {
  text-align: center;
  margin-bottom: 26px;
  animation: riseIn 0.6s cubic-bezier(0.22, 0.9, 0.32, 1.15) both;
}

.mascot {
  width: 78px;
  height: 78px;
  margin: 0 auto 14px;
  font-size: 42px;
  line-height: 78px;
  background: linear-gradient(180deg, #eaf4ff, #d3e9ff);
  border-radius: 28px;
  box-shadow: inset 0 -3px 0 rgba(47, 127, 224, 0.12);
  animation: bob 3s ease-in-out infinite;
}

.title {
  font-size: 30px;
  color: var(--blue-dark);
  letter-spacing: 1px;
}

.subtitle {
  margin-top: 6px;
  font-size: 14px;
  color: var(--ink-soft);
}

/* ---------- 板块 ---------- */
.block {
  margin-bottom: 24px;
  animation: riseIn 0.6s cubic-bezier(0.22, 0.9, 0.32, 1.15) both;
}
.block:nth-of-type(1) { animation-delay: 0.12s; }
.block:nth-of-type(2) { animation-delay: 0.22s; }

.block-title {
  font-size: 17px;
  color: var(--ink);
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.badge {
  display: inline-grid;
  place-items: center;
  width: 24px;
  height: 24px;
  font-family: 'Nunito', sans-serif;
  font-size: 13px;
  font-weight: 800;
  color: var(--white);
  background: var(--blue);
  border-radius: 8px;
}

/* ---------- 性别选择 ---------- */
.gender-group {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.gender {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px;
  border-radius: var(--radius-lg);
  border: 2px solid var(--blue-mist);
  background: #fbfdff;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease, background 0.18s ease;
}
.gender:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-soft);
}
.gender-emoji { font-size: 26px; }
.gender-name { font-size: 16px; font-weight: 800; color: var(--ink); }

.check {
  position: absolute;
  top: 8px;
  right: 10px;
  width: 20px;
  height: 20px;
  font-size: 12px;
  line-height: 20px;
  text-align: center;
  color: var(--white);
  background: var(--blue);
  border-radius: 50%;
  opacity: 0;
  transform: scale(0.4);
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.gender.active {
  border-color: var(--blue);
  background: var(--blue-light);
  box-shadow: 0 8px 20px rgba(77, 159, 255, 0.22);
}
/* 女选项选中时用粉色点缀 */
.gender:nth-child(2).active {
  border-color: var(--pink);
  background: var(--pink-light);
  box-shadow: 0 8px 20px rgba(255, 143, 177, 0.22);
}
.gender.active .check {
  opacity: 1;
  transform: scale(1);
}
.gender:nth-child(2).active .check {
  background: var(--pink);
}

/* ---------- 大模型选择 ---------- */
.model-group {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.model {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 18px 10px;
  border-radius: var(--radius-lg);
  border: 2px solid var(--blue-mist);
  background: #fbfdff;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease, background 0.18s ease;
}
.model:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-soft);
}
.model-emoji { font-size: 26px; }
.model-name { font-size: 15px; font-weight: 800; color: var(--ink); }
.model.active {
  border-color: var(--blue);
  background: var(--blue-light);
  box-shadow: 0 8px 20px rgba(77, 159, 255, 0.22);
}

.model-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}
.model-col .model { width: 100%; }

.model-note {
  font-size: 11.5px;
  line-height: 1.5;
  color: var(--ink-soft);
  text-align: center;
}

/* ---------- 确定按钮 ---------- */
.submit {
  width: 100%;
  padding: 16px;
  font-size: 18px;
  font-weight: 900;
  letter-spacing: 6px;
  color: var(--white);
  background: linear-gradient(135deg, #6db5ff, #4d9fff 55%, #2f7fe0);
  border-radius: 999px;
  box-shadow: 0 10px 24px rgba(47, 127, 224, 0.32);
  transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
  animation: riseIn 0.6s cubic-bezier(0.22, 0.9, 0.32, 1.15) 0.32s both;
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

/* ---------- 清空用户数据入口 ---------- */
.clear-link {
  display: block;
  margin: 18px auto 0;
  font-size: 13px;
  font-weight: 700;
  color: var(--ink-soft);
  opacity: 0.85;
  transition: color 0.15s ease, opacity 0.15s ease;
}
.clear-link:hover {
  color: var(--blue-deep);
  opacity: 1;
}

/* ---------- 清空弹窗（居中） ---------- */
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
  padding: 26px 22px;
  text-align: center;
  box-shadow: var(--shadow-card);
}
.modal-icon {
  font-size: 40px;
  line-height: 1;
  margin-bottom: 10px;
}
.modal-title {
  font-size: 18px;
  color: var(--blue-dark);
  margin-bottom: 6px;
}
.modal-desc {
  font-size: 13px;
  color: var(--ink-soft);
  margin-bottom: 16px;
}
.modal-input {
  width: 100%;
  padding: 12px 14px;
  font-size: 15px;
  font-family: inherit;
  text-align: center;
  letter-spacing: 1px;
  color: var(--ink);
  background: #fbfdff;
  border: 2px solid var(--blue-mist);
  border-radius: var(--radius-md);
  outline: none;
  margin-bottom: 18px;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}
.modal-input:focus {
  border-color: var(--blue);
  box-shadow: 0 0 0 4px rgba(77, 159, 255, 0.12);
}
.modal-actions {
  display: flex;
  gap: 10px;
}
.modal-cancel,
.modal-ok {
  flex: 1;
  padding: 11px;
  font-size: 15px;
  font-weight: 800;
  border-radius: 999px;
  transition: transform 0.15s ease, filter 0.15s ease;
}
.modal-cancel {
  color: var(--ink-soft);
  background: #eef3f9;
}
.modal-cancel:hover {
  filter: brightness(0.98);
}
.modal-ok {
  color: var(--white);
  background: linear-gradient(135deg, #ff9a9a, #ff6b6b);
  box-shadow: 0 8px 18px rgba(255, 107, 107, 0.3);
}
.modal-ok:hover {
  filter: brightness(1.05);
  transform: translateY(-1px);
}
.modal-ok:active {
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

@media (max-width: 480px) {
  .card { padding: 28px 22px 26px; }
  .title { font-size: 26px; }
}
</style>
