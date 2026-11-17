import { defineStore } from 'pinia'
import { authApi } from '../api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('labcare_token') || '',
    user: JSON.parse(localStorage.getItem('labcare_user') || 'null')
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    isAdmin: (state) => state.user?.role === 'ADMIN',
    displayName: (state) => state.user?.displayName || ''
  },
  actions: {
    async login(form) {
      const res = await authApi.login(form)
      this.token = res.data.token
      this.user = res.data.user
      localStorage.setItem('labcare_token', this.token)
      localStorage.setItem('labcare_user', JSON.stringify(this.user))
      return this.user
    },
    async restore() {
      if (!this.token) return null
      try {
        const res = await authApi.me()
        this.user = res.data
        localStorage.setItem('labcare_user', JSON.stringify(this.user))
        return this.user
      } catch (e) {
        this.logout()
        return null
      }
    },
    logout() {
      authApi.logout().catch(() => {})
      this.token = ''
      this.user = null
      localStorage.removeItem('labcare_token')
      localStorage.removeItem('labcare_user')
    }
  }
})
