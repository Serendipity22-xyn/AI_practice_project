import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { spawn } from 'child_process'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// 后端自动启动插件：Vite dev server 启动时，自动拉起 FastAPI 后端（端口 8000）
function backendAutoStart() {
  let backend = null
  return {
    name: 'backend-auto-start',
    configureServer() {
      if (backend) return
      const backendDir = path.join(__dirname, 'backend')
      console.log('[backend] 正在启动 FastAPI 服务...')
      backend = spawn('python -m uvicorn main:app --port 8000', {
        cwd: backendDir,
        stdio: 'inherit',
        shell: true,
      })
      backend.on('error', (err) => console.error('[backend] 启动失败:', err.message))
      backend.on('exit', (code) => console.log('[backend] 已退出，code =', code))
    },
  }
}

export default defineConfig({
  plugins: [vue(), backendAutoStart()],
})
