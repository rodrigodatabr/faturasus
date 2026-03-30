import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/transcricao': 'http://localhost:8001',
      '/busca': 'http://localhost:8001',
      '/health': 'http://localhost:8001',
    },
  },
})
