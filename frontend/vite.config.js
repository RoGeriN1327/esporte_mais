import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig, loadEnv } from 'vite'

// Os testes de data/hora assumem o fuso da Secretaria (Rio Verde - GO).
process.env.TZ = 'America/Sao_Paulo'

export default defineConfig(({ command, mode }) => {
  // VITE_API_URL é embutida no bundle: um build de produção sem ela chamaria
  // localhost no navegador do usuário. Melhor falhar o build com uma mensagem clara.
  const { VITE_API_URL } = loadEnv(mode, process.cwd(), 'VITE_')
  if (command === 'build' && !VITE_API_URL) {
    throw new Error(
      'VITE_API_URL não definida. Informe a URL pública da API no build, ' +
        'ex.: VITE_API_URL=https://api.seudominio.com npm run build',
    )
  }

  return {
    plugins: [react(), tailwindcss()],
    server: {
      host: true,
      port: 5173,
      strictPort: true,
      // Polling: no Docker Desktop (Windows/macOS) os eventos de arquivo do bind
      // mount não chegam ao container, e sem isso o hot-reload não funciona.
      watch: {
        usePolling: true,
        interval: 300,
      },
    },
    test: {
      environment: 'jsdom',
      include: ['src/**/*.test.{js,jsx}'],
      coverage: {
        include: ['src/utils/**', 'src/api/client.js'],
        reporter: ['text', 'html'],
        reportsDirectory: 'relatorios/cobertura',
      },
    },
  }
})
