import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Proxy /api/* to the backend to avoid CORS in local development
      '/api': {
        target: 'https://razorpay-backend-j4mc.onrender.com',
        changeOrigin: true,
        secure: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
