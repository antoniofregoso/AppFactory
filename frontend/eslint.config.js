import js from '@eslint/js';
import globals from 'globals';
import eslintConfigPrettier from 'eslint-config-prettier';

export default [
  // 1. Usa las reglas recomendadas por defecto para JavaScript
  js.configs.recommended,

  {
    files: ['**/*.js', '**/*.jsx'],
    languageOptions: {
      ecmaVersion: 2026,          // Soporte para el JavaScript de este año
      sourceType: 'module',       // Permite usar import/export de Vite
      parserOptions: {
        ecmaFeatures: { jsx: true }, // Permite parsear sintaxis JSX (Preact)
      },
      globals: {
        ...globals.browser,       // Reconoce objetos del navegador como window, document, fetch
        ...globals.node,          // Reconoce variables de Node si las necesitas
      },
    },
    rules: {
      // Aquí puedes personalizar tus reglas de calidad de código
      'no-unused-vars': 'warn',   // Te avisa con un warning si creas una variable y no la usas
      'no-console': 'off',        // Te permite usar console.log sin que marque error
    },
  },

  // 2. Desactiva todas las reglas de formato de ESLint que choquen con Prettier
  eslintConfigPrettier,
];