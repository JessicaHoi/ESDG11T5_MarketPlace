<template>
  <div class="min-h-screen bg-paper flex">
    <!-- Left panel -->
    <div class="hidden lg:flex lg:w-1/2 bg-ink flex-col justify-between p-12 relative overflow-hidden">
      <div class="absolute inset-0 opacity-5">
        <div v-for="i in 20" :key="i"
          class="absolute border border-white rounded-full"
          :style="{
            width: `${(i * 47) % 300 + 100}px`,
            height: `${(i * 47) % 300 + 100}px`,
            top: `${(i * 73) % 100}%`,
            left: `${(i * 31) % 100}%`,
            transform: 'translate(-50%, -50%)'
          }"
        ></div>
      </div>
      <div class="relative z-10">
        <span class="font-display font-extrabold text-2xl text-paper">
          Ouimarché
        </span>
      </div>
      <div class="relative z-10">
        <p class="section-label text-white/40 mb-4">Admin Portal</p>
        <h1 class="font-display font-extrabold text-5xl text-paper leading-tight mb-6">
          Manage<br/>disputes &<br/>oversight.
        </h1>
        <p class="text-white/50 font-body text-sm leading-relaxed max-w-xs">
          Review disputes, approve evidence, and ensure fair resolutions across the marketplace.
        </p>
      </div>
      <div class="relative z-10">
        <p class="text-white/30 text-xs font-mono">Admin access only</p>
      </div>
    </div>

    <!-- Right panel -->
    <div class="w-full lg:w-1/2 flex items-center justify-center p-8">
      <div class="w-full max-w-sm">
        <div class="lg:hidden mb-10">
          <span class="font-display font-extrabold text-2xl">Ouimarché</span>
        </div>
        <p class="section-label mb-2">Admin Portal</p>
        <h2 class="font-display font-bold text-3xl mb-8">Sign in</h2>

        <form @submit.prevent="handleLogin" class="space-y-4">
          <div>
            <label class="section-label block mb-2">Admin Email</label>
            <input
              v-model="form.email"
              type="email"
              class="input-field"
              placeholder="admin@ouimarche.sg"
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

          <div v-if="error" class="text-red-600 text-xs font-mono py-2">{{ error }}</div>

          <button type="submit" class="btn-primary w-full mt-2" :disabled="loading">
            {{ loading ? 'Signing in...' : 'Sign In as Admin' }}
          </button>
        </form>

        <div class="mt-8 pt-6 border-t border-ink/10">
          <p class="text-xs text-muted text-center mb-3 font-mono">Demo credentials</p>
          <button @click="fillDemo" class="w-full border border-ink/20 py-2 text-xs font-mono text-slate hover:border-accent hover:text-accent transition-colors">
            admin@ouimarche.sg / admin123
          </button>
        </div>

        <div class="mt-6 flex justify-center gap-4 text-xs text-muted">
          <span>Buyer? <router-link to="/login" class="text-accent hover:underline">Buyer login →</router-link></span>
          <span class="text-ink/20">|</span>
          <span>Seller? <router-link to="/seller" class="text-accent hover:underline">Seller login →</router-link></span>
        </div>
      </div>
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
  form.value.email = 'admin@ouimarche.sg'
  form.value.password = 'admin123'
}

async function handleLogin() {
  error.value = ''
  loading.value = true
  await new Promise(r => setTimeout(r, 800))
  if (form.value.email === 'admin@ouimarche.sg' && form.value.password === 'admin123') {
    router.push('/admin/disputes')
  } else {
    error.value = 'Invalid admin credentials.'
  }
  loading.value = false
}
</script>
