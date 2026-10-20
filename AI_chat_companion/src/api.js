// 后端服务地址
const BASE = 'http://127.0.0.1:8000'

async function request(url, options = {}) {
  const res = await fetch(BASE + url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  return res.json()
}

// 注册：返回 { code, message, data: { user_id, companion_name } }
export function apiRegister(username, password, companionName) {
  return request('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ username, password, companion_name: companionName }),
  })
}

// 登录：返回 { code, message, data: { user_id, companion_name, persona, model_config, chat_history } }
export function apiLogin(userId, password) {
  return request('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, password }),
  })
}

// 保存模型配置
export function apiSaveModelConfig(userId, modelType, manualConfig) {
  return request('/api/model/config', {
    method: 'POST',
    body: JSON.stringify({
      user_id: userId,
      model_type: modelType,
      manual_config: manualConfig || null,
    }),
  })
}

// 保存性格设定
export function apiSavePersona(userId, persona) {
  return request('/api/auth/persona', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, persona }),
  })
}

// 流式对话：onChunk 收到一段内容，onError 出错，onDone 完成
// 若后端返回 JSON（如模型名不规范 4001），则直接返回该 JSON 对象
export async function apiChat(userId, message, options = {}) {
  const { modelType, manualConfig, resolveInvalidModel, onChunk, onError, onDone } = options

  const body = { user_id: userId, message }
  if (modelType) body.model_type = modelType
  if (manualConfig) body.manual_config = manualConfig
  if (resolveInvalidModel !== undefined && resolveInvalidModel !== null) {
    body.resolve_invalid_model = resolveInvalidModel
  }

  const res = await fetch(BASE + '/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  const contentType = res.headers.get('content-type') || ''
  // 非流式：返回 JSON（模型名不规范 / 参数错误等）
  if (contentType.includes('application/json')) {
    return await res.json()
  }

  // 流式 SSE 读取
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      if (!line.startsWith('data:')) continue
      const data = line.slice(5).trim()
      if (data === '[DONE]') continue
      try {
        const obj = JSON.parse(data)
        if (obj.content) onChunk && onChunk(obj.content)
        if (obj.error) onError && onError(obj.error)
        if (obj.done) onDone && onDone()
      } catch {
        /* 忽略无法解析的帧 */
      }
    }
  }
  onDone && onDone()
  return { code: 0, message: 'done' }
}
