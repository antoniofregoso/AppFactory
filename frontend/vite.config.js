import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'
import preact from '@preact/preset-vite'

export default defineConfig({
  appType: 'spa',

  server: {
    middlewareMode: false,
    port: 3000, 
    strictPort: true, 
    
    // Configuración de Proxy (Opcional pero muy útil para desarrollo)
    // Te permite redirigir peticiones de la API a FastAPI evitando problemas de CORS
    proxy: {
      '/graphql': {
        target: 'http://localhost:8000', // La URL de tu FastAPI en desarrollo
        changeOrigin: true,
      },
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  },
  plugins: [
    tailwindcss(),
    preact(),
  ],
  // Si en Vitest usas selectores del DOM nativos, esto asegura que corran bien
  test: {
    environment: 'jsdom', 
  }
})
