import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  cacheDir: 'node_modules/.vite_cache',
  plugins: [react()],

  resolve: {
    dedupe: ['react', 'react-dom', 'three', '@react-three/fiber'],
  },

  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react/jsx-runtime',
      'three',
      '@react-three/fiber',
      '@react-three/drei',
      'three-stdlib',
      'troika-three-text',
    ],
  },

  server: {
    host: true,
    port: 5173,
    strictPort: false,
    fs: {
      strict: true,
    },
    hmr: {
      overlay: true,
    },
  },
})