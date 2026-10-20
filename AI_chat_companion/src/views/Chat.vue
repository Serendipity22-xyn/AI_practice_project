<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import HomeButton from '../components/HomeButton.vue'
import Watermark from '../components/Watermark.vue'
import { apiChat } from '../api.js'

const userId = sessionStorage.getItem('current_user_id') || '未知'
const companion = sessionStorage.getItem('current_companion') || '伴侣'

// 读取当前伴侣的人设（登录后写入 current_persona）
function getPersona() {
  try {
    return JSON.parse(sessionStorage.getItem('current_persona') || 'null')
  } catch {
    return null
  }
}
const persona = getPersona()

const STORAGE_KEY = `chat_${userId}`

const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const tip = ref('')
const deleteTarget = ref(null)
const bodyRef = ref(null)

function genId() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 6)
}

function loadMessages() {
  // 优先从后端登录返回的历史加载，否则用本地缓存
  const history = sessionStorage.getItem('chat_history')
  if (history) {
    try {
      messages.value = JSON.parse(history)
      return
    } catch {
      /* 忽略，回退到本地缓存 */
    }
  }
  try {
    messages.value = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
  } catch {
    messages.value = []
  }
}

function saveMessages() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(messages.value))
}

function scrollToBottom() {
  nextTick(() => {
    if (bodyRef.value) {
      bodyRef.value.scrollTop = bodyRef.value.scrollHeight
    }
  })
}

// 模型名不规范时，待用户确认的后端响应
const pendingConfirm = ref(null)

function sendMessage() {
  const text = inputText.value.trim()
  if (!text) {
    tip.value = '请输入消息内容～'
    return
  }
  messages.value.push({ id: genId(), role: 'user', content: text, time: Date.now() })
  inputText.value = ''
  saveMessages()
  scrollToBottom()
  doChat(null)
}

// 发起对话：resolveInvalidModel 为 null=首次；true=用户确认「是」自动匹配
async function doChat(resolveInvalidModel) {
  loading.value = true
  scrollToBottom()
  // 先插入 assistant 占位气泡，流式填充
  const msgId = genId()
  messages.value.push({ id: msgId, role: 'assistant', content: '', time: Date.now() })

  const removePlaceholder = () => {
    messages.value = messages.value.filter((m) => m.id !== msgId)
  }

  try {
    const res = await apiChat(userId, lastUserContent(), {
      resolveInvalidModel,
      onChunk: (chunk) => {
        const msg = messages.value.find((m) => m.id === msgId)
        if (msg) msg.content += chunk
        scrollToBottom()
      },
      onError: (err) => {
        tip.value = 'AI 回复失败：' + err
        removePlaceholder()
      },
      onDone: () => saveMessages(),
    })

    // 非流式响应：模型名不规范（4001）或其他错误
    if (res && res.code === 4001) {
      removePlaceholder()
      pendingConfirm.value = res
    } else if (res && res.code && res.code !== 0) {
      removePlaceholder()
      tip.value = res.message
    }
  } catch (e) {
    removePlaceholder()
    tip.value = 'AI 回复失败：网络错误'
  } finally {
    loading.value = false
    saveMessages()
    scrollToBottom()
  }
}

function lastUserContent() {
  for (let i = messages.value.length - 1; i >= 0; i--) {
    if (messages.value[i].role === 'user') return messages.value[i].content
  }
  return ''
}

function confirmYes() {
  pendingConfirm.value = null
  doChat(true)
}

function confirmNo() {
  pendingConfirm.value = null
  tip.value = '请填写正确的标准模型名称'
}

function askDelete(msg) {
  deleteTarget.value = msg
}

function confirmDelete() {
  if (deleteTarget.value) {
    messages.value = messages.value.filter((m) => m.id !== deleteTarget.value.id)
    saveMessages()
  }
  deleteTarget.value = null
}

onMounted(() => {
  loadMessages()
  scrollToBottom()
})

onBeforeUnmount(() => {
  saveMessages()
})
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
      <span class="bg-bubble bg-bubble-1"></span>
      <span class="bg-bubble bg-bubble-2"></span>
      <span class="bg-bubble bg-bubble-3"></span>
      <span class="bg-bubble bg-bubble-4"></span>
    </div>

    <main class="chat-card">
      <!-- 头部：伴侣信息 -->
      <header class="chat-header">
        <div class="chat-avatar">{{ persona ? '💬' : '🤖' }}</div>
        <div class="chat-info">
          <div class="chat-name">{{ companion }}</div>
          <div class="chat-persona">{{ persona ? persona.label : '未选择性格' }}</div>
        </div>
      </header>

      <!-- 消息列表 -->
      <div class="chat-body" ref="bodyRef">
        <div v-if="messages.length === 0" class="chat-empty">和 {{ companion }} 打个招呼吧～</div>
        <div v-for="msg in messages" :key="msg.id" class="msg" :class="msg.role" @click="askDelete(msg)">
          <div class="bubble">{{ msg.content }}</div>
        </div>
        <div v-if="loading" class="msg assistant">
          <div class="bubble typing">{{ companion }} 输入中<span>…</span></div>
        </div>
      </div>

      <!-- 底部：用户 ID + 输入框 + 发送 -->
      <footer class="chat-footer">
        <div class="chat-uid">ID：{{ userId }}</div>
        <div class="input-row">
          <input
            v-model="inputText"
            class="chat-input"
            type="text"
            placeholder="输入消息…"
            @keyup.enter="sendMessage"
          />
          <button class="send-btn" @click="sendMessage">发送</button>
        </div>
      </footer>
    </main>

    <!-- 删除确认弹窗 -->
    <Transition name="modal">
      <div v-if="deleteTarget" class="modal-mask" @click.self="deleteTarget = null">
        <div class="modal-card">
          <div class="modal-icon">🗑️</div>
          <p class="modal-text">删除这条消息？</p>
          <div class="modal-actions">
            <button class="modal-cancel" @click="deleteTarget = null">取消</button>
            <button class="modal-ok" @click="confirmDelete">删除</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 模型名确认弹窗 -->
    <Transition name="modal">
      <div v-if="pendingConfirm" class="modal-mask" @click.self="pendingConfirm = null">
        <div class="modal-card">
          <div class="modal-icon">🤔</div>
          <p class="modal-text">{{ pendingConfirm.message }}</p>
          <div class="modal-actions">
            <button class="modal-cancel" @click="confirmNo">否</button>
            <button class="modal-btn" @click="confirmYes">是</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 提示弹窗 -->
    <Transition name="modal">
      <div v-if="tip" class="modal-mask" @click.self="tip = ''">
        <div class="modal-card">
          <div class="modal-icon">😢</div>
          <p class="modal-text">{{ tip }}</p>
          <button class="modal-btn" @click="tip = ''">知道了</button>
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
  padding: 24px 20px;
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
.cloud-1 { top: 10%; left: -60px; opacity: 0.9; }
.cloud-2 { top: 22%; right: -50px; transform: scale(0.8); animation-delay: -6s; }
.cloud-3 { bottom: 12%; left: 8%; transform: scale(0.65); animation-delay: -12s; }
.bg-bubble {
  position: absolute;
  bottom: -40px;
  border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.9), rgba(77, 159, 255, 0.16));
  animation: rise 12s linear infinite;
}
.bg-bubble-1 { left: 12%; width: 22px; height: 22px; animation-duration: 14s; }
.bg-bubble-2 { left: 30%; width: 12px; height: 12px; animation-duration: 11s; animation-delay: -3s; }
.bg-bubble-3 { left: 62%; width: 18px; height: 18px; animation-duration: 16s; animation-delay: -7s; }
.bg-bubble-4 { left: 82%; width: 14px; height: 14px; animation-duration: 13s; animation-delay: -5s; }

/* ---------- 聊天卡片 ---------- */
.chat-card {
  position: relative;
  width: 100%;
  max-width: 760px;
  height: calc(100vh - 72px);
  min-height: 520px;
  display: flex;
  flex-direction: column;
  background: var(--white);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

/* ---------- 头部 ---------- */
.chat-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: linear-gradient(135deg, #eaf4ff, #d3e9ff);
  border-bottom: 1px solid var(--blue-mist);
}
.chat-avatar {
  width: 46px;
  height: 46px;
  font-size: 24px;
  line-height: 46px;
  text-align: center;
  background: var(--white);
  border-radius: 16px;
  box-shadow: var(--shadow-soft);
}
.chat-name {
  font-size: 17px;
  font-weight: 800;
  color: var(--blue-dark);
}
.chat-persona {
  font-size: 12px;
  color: var(--ink-soft);
  margin-top: 2px;
}

/* ---------- 消息区 ---------- */
.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 18px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.chat-empty {
  margin: auto;
  font-size: 14px;
  color: var(--ink-soft);
}
.msg {
  display: flex;
  max-width: 78%;
}
.msg.user {
  align-self: flex-end;
}
.msg.assistant {
  align-self: flex-start;
}
.bubble {
  padding: 10px 14px;
  border-radius: 16px;
  font-size: 15px;
  line-height: 1.6;
  word-break: break-word;
  white-space: pre-wrap;
  cursor: pointer;
}
.msg.user .bubble {
  background: linear-gradient(135deg, #6db5ff, #4d9fff);
  color: #fff;
  border-bottom-right-radius: 6px;
}
.msg.assistant .bubble {
  background: #f2f7ff;
  color: var(--ink);
  border: 1px solid var(--blue-mist);
  border-bottom-left-radius: 6px;
}

.typing span {
  animation: blink 1.2s infinite;
}
@keyframes blink {
  0%, 100% { opacity: 0.2; }
  50% { opacity: 1; }
}

/* ---------- 底部 ---------- */
.chat-footer {
  padding: 10px 16px 14px;
  border-top: 1px solid var(--blue-mist);
  background: #fbfdff;
}
.chat-uid {
  font-size: 12px;
  color: var(--ink-soft);
  margin-bottom: 8px;
}
.input-row {
  display: flex;
  gap: 10px;
}
.chat-input {
  flex: 1;
  padding: 11px 16px;
  font-size: 15px;
  font-family: inherit;
  color: var(--ink);
  background: #fff;
  border: 2px solid var(--blue-mist);
  border-radius: 999px;
  outline: none;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}
.chat-input::placeholder {
  color: #b6c6d6;
}
.chat-input:focus {
  border-color: var(--blue);
  box-shadow: 0 0 0 4px rgba(77, 159, 255, 0.12);
}
.send-btn {
  padding: 0 22px;
  font-size: 15px;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(135deg, #6db5ff, #4d9fff);
  border-radius: 999px;
  box-shadow: 0 6px 16px rgba(47, 127, 224, 0.28);
  transition: transform 0.15s ease, filter 0.15s ease;
}
.send-btn:hover {
  filter: brightness(1.05);
  transform: translateY(-1px);
}
.send-btn:active {
  transform: translateY(1px) scale(0.97);
}

/* ---------- 弹窗 ---------- */
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
.modal-text {
  font-size: 15px;
  font-weight: 700;
  color: var(--ink);
  line-height: 1.6;
  margin-bottom: 18px;
  word-break: break-word;
}
.modal-actions {
  display: flex;
  gap: 10px;
}
.modal-cancel,
.modal-ok,
.modal-btn {
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
.modal-ok {
  color: #fff;
  background: linear-gradient(135deg, #ff9a9a, #ff6b6b);
  box-shadow: 0 8px 18px rgba(255, 107, 107, 0.3);
}
.modal-btn {
  color: #fff;
  background: linear-gradient(135deg, #6db5ff, #4d9fff);
  box-shadow: 0 8px 18px rgba(47, 127, 224, 0.3);
}
.modal-cancel:hover,
.modal-ok:hover,
.modal-btn:hover {
  filter: brightness(1.03);
  transform: translateY(-1px);
}
.modal-ok:active,
.modal-cancel:active,
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
@keyframes drift {
  0%, 100% { transform: translateX(0); }
  50% { transform: translateX(30px); }
}
@keyframes rise {
  0% { transform: translateY(0); opacity: 0; }
  15% { opacity: 1; }
  100% { transform: translateY(-110vh); opacity: 0; }
}

@media (max-width: 480px) {
  .chat-card { height: calc(100vh - 90px); min-height: 400px; }
}
</style>
