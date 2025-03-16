import pluginJs from '@eslint/js'
import eslintPluginPrettier from 'eslint-plugin-prettier/recommended'
import pluginVue from 'eslint-plugin-vue'
import { defineConfig, globalIgnores } from 'eslint/config'
import globals from 'globals'
import tseslint from 'typescript-eslint'

/** @type {import('eslint').Linter.Config[]} */
export default defineConfig([
  globalIgnores(['dist/*']),
  { files: ['**/*.{js,mjs,cjs,ts,vue}'] },
  { languageOptions: { globals: globals.browser } },
  pluginJs.configs.recommended,
  ...tseslint.configs.recommended,
  ...pluginVue.configs['flat/essential'],
  eslintPluginPrettier,
  { files: ['**/*.vue'], languageOptions: { parserOptions: { parser: tseslint.parser } } },
  {
    files: ['**/*.{js,mjs,cjs,ts,vue}'],
    rules: {
      'vue/multi-word-component-names': 'warn',
      '@typescript-eslint/no-explicit-any': 'warn'
    }
  }
])
