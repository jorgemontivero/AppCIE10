import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    // En modo desarrollo, reenvía las peticiones /api al backend FastAPI
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
