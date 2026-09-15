import { ref, computed } from 'vue'

import en from '../locales/en'
import th from '../locales/th'


const currentLanguage = ref(
  localStorage.getItem('language') || 'EN'
)


export function useLanguage() {

  const t = computed(() => {
    return currentLanguage.value === 'TH'
      ? th
      : en
  })


  const setLanguage = (language) => {
    currentLanguage.value = language

    localStorage.setItem(
      'language',
      language
    )
  }


  const toggleLanguage = () => {
    if (currentLanguage.value === 'EN') {
      setLanguage('TH')
    } else {
      setLanguage('EN')
    }
  }


  return {
    currentLanguage,
    t,
    setLanguage,
    toggleLanguage
  }
}