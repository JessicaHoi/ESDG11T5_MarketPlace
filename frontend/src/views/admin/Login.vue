<template>
  <div class="min-h-screen bg-ink flex items-center justify-center p-8">
    <!-- Background circles -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div v-for="i in 8" :key="i"
        class="absolute border border-white/5 rounded-full"
        :style="{
          width: `${i * 120}px`,
          height: `${i * 120}px`,
          top: '50%', left: '50%',
          transform: 'translate(-50%, -50%)'
        }"
      ></div>
    </div>

    <div class="relative z-10 w-full max-w-sm">
      <!-- Logo -->
      <div class="text-center mb-10">
        <span class="font-display font-extrabold text-2xl text-paper">
          Trade<span class="text-accent">Nest</span>
        </span>
        <div class="mt-2 inline-flex items-center gap-2">
          <span class="section-label text-white/40 border border-white/20 px-2 py-0.5">Admin Portal</span>
        </div>
      </div>

      <div class="bg-paper p-8">
        <h2 class="font-display font-bold text-2xl mb-6">Admin Sign In</h2>

        <form @submit.prevent="handleLogin" class="space-y-4">
          <div>
            <label class="section-label block mb-2">Admin Email</label>
            <input
              v-model="form.email"
              type="email"
              class="input-field"
              placeholder="admin@tradenest.sg"
              required
            />
          </div>
          <div>
            <label class="section-label block mb-2">Password</label>
            <input
              v-model="form.password"
              type="password"
              class="input-field"
              placeholder="••••••••"
              required
            />
          </div>

          <div v-if="error" class="text-red-600 text-xs font-mono py-2 flex items-center gap-2">
            <span>⚠</span>{{ error }}
          </div>

          <button type="submit" class="btn-primary w-full mt-2" :disabled="loading">
            {{ loading ? 'Signing in...' : 'Sign In as Admin' }}
          </button>
        </form>

        <div class="mt-6 pt-5 border-t border-ink/10">
          <p class="text-xs text-muted text-center mb-3 font-mono">Demo credentials</p>
          <button @click="fillDemo" class="w-full border border-ink/20 py-2 text-xs font-mono text-slate hover:border-accent hover:text-accent transition-colors">
            admin@tradenest.sg / admin123
          </button>
        </div>
      </div>

      <p class="text-center mt-6 text-xs text-white/30 font-mono">
        Buyer?
        <router-link to="/login" class="text-accent hover:underline ml-1">Buyer login →</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const form = ref({ email: '', password: '' })
const error = ref('')
const loading = ref(false)

function fillDemo() {
  form.value.email = 'admin@tradenest.sg'
  form.value.password = 'admin123'
}

async function handleLogin() {
  error.value = ''
  loading.value = true
  await new Promise(r => setTimeout(r, 800))
  if (form.value.email === 'admin@tradenest.sg' && form.value.password === 'admin123') {
    router.push('/admin/disputes')
  } else {
    error.value = 'Invalid admin credentials.'
  }
  loading.value = false
}
</script>
