import { defineStore } from 'pinia'
import { ref } from 'vue'

type Theme = 'dark' | 'light' | 'system'

const STORAGE_KEY = 'clarifi-theme'

function getSystemPreference(): 'dark' | 'light' {
  if (typeof window === 'undefined') return 'dark'
  return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
}

function resolveTheme(mode: Theme): 'dark' | 'light' {
  return mode === 'system' ? getSystemPreference() : mode
}

function applyTheme(resolved: 'dark' | 'light') {
  const html = document.documentElement
  if (resolved === 'dark') {
    html.classList.add('dark')
  } else {
    html.classList.remove('dark')
  }
}

export const useThemeStore = defineStore('theme', () => {
  const mode = ref<Theme>(
    (localStorage.getItem(STORAGE_KEY) as Theme) || 'dark'
  )
  const resolved = ref<'dark' | 'light'>(resolveTheme(mode.value))

  function apply() {
    resolved.value = resolveTheme(mode.value)
    applyTheme(resolved.value)
    localStorage.setItem(STORAGE_KEY, mode.value)
  }

  function toggle() {
    if (mode.value === 'dark') {
      mode.value = 'light'
    } else {
      mode.value = 'dark'
    }
    apply()
  }

  function setTheme(newMode: Theme) {
    mode.value = newMode
    apply()
  }

  // Listen for system preference changes when in 'system' mode
  if (typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      if (mode.value === 'system') {
        apply()
      }
    })
  }

  // Initial apply
  apply()

  return { mode, resolved, toggle, setTheme }
})
