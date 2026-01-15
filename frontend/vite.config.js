import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [react()],

    // Development server configuration
    server: {
      port: parseInt(env.VITE_DEV_PORT || '5173'),
      host: '0.0.0.0',
      proxy: {
        '/api': {
          target: env.VITE_BACKEND_URL || 'http://localhost:5000',
          changeOrigin: true,
        },
      },
    },

    // Build configuration
    build: {
      // Production optimizations
      minify: mode === 'production' ? 'esbuild' : false,
      sourcemap: mode !== 'production',

      // Chunk splitting for better caching
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom', 'react-router-dom'],
            ui: ['@mantine/core', '@mantine/hooks', '@mantine/notifications'],
            charts: ['recharts'],
          },
        },
      },

      // Target modern browsers
      target: 'es2020',
    },

    // Environment variable prefix
    envPrefix: 'VITE_',

    // Define global constants
    define: {
      __APP_VERSION__: JSON.stringify(process.env.npm_package_version || '0.0.0'),
    },
  }
})
