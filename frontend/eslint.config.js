// Análise estática do frontend Esporte+ (ESLint 9, configuração "flat").
// Conjuntos recomendados pela comunidade React:
//   * @eslint/js recommended       — erros comuns de JavaScript (variáveis não usadas, etc.)
//   * eslint-plugin-react           — boas práticas de componentes e JSX
//   * eslint-plugin-react-hooks     — regras dos Hooks (dependências de useEffect, etc.)
//   * eslint-plugin-react-refresh   — compatibilidade com o hot-reload do Vite
import js from '@eslint/js'
import react from 'eslint-plugin-react'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import globals from 'globals'

export default [
  { ignores: ['dist', 'node_modules', 'coverage'] },
  js.configs.recommended,
  react.configs.flat.recommended,
  react.configs.flat['jsx-runtime'],
  reactHooks.configs.flat.recommended,
  reactRefresh.configs.vite,
  {
    files: ['**/*.{js,jsx}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: { ...globals.browser },
    },
    settings: { react: { version: 'detect' } },
    rules: {
      // O projeto não usa PropTypes (validação de dados é feita pela API).
      'react/prop-types': 'off',
    },
  },
  {
    files: ['**/*.test.{js,jsx}', 'vite.config.js', 'eslint.config.js'],
    languageOptions: { globals: { ...globals.node } },
  },
]
