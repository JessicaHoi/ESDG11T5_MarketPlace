<template>
  <div class="min-h-screen bg-paper flex">
    <!-- Left panel -->
    <div class="hidden lg:flex lg:w-1/2 bg-ink flex-col justify-between p-12 relative overflow-hidden">
      <!-- Background texture -->
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
          Trade<span class="text-accent">Nest</span>
        </span>
      </div>

      <div class="relative z-10">
        <p class="section-label text-white/40 mb-4">The marketplace</p>
        <h1 class="font-display font-extrabold text-5xl text-paper leading-tight mb-6">
          Buy & sell<br/>with<br/>confidence.
        </h1>
        <p class="text-white/50 font-body text-sm leading-relaxed max-w-xs">
          Every transaction is protected by our escrow system. Your payment is only released when you're happy.
        </p>
      </div>

      <div class="relative z-10 flex items-center gap-4">
        <div class="flex -space-x-2">
          <div v-for="(color, i) in ['bg-accent', 'bg-sage', 'bg-amber-400', 'bg-purple-400']" :key="i"
            :class="[color, 'w-8 h-8 rounded-full border-2 border-ink flex items-center justify-center text-xs font-bold text-ink']"
          >{{ ['A','B','C','D'][i] }}</div>
        </div>
        <p class="text-white/40 text-xs font-mono">2,400+ active listings</p>
      </div>
    </div>

    <!-- Right panel -->
    <div class="w-full lg:w-1/2 flex items-center justify-center p-8">
      <div class="w-full max-w-sm">
        <div class="lg:hidden mb-10">
          <span class="font-display font-extrabold text-2xl">Trade<span class="text-accent">Nest</span></span>
        </div>

        <p class="section-label mb-2">Welcome back</p>
        <h2 class="font-display font-bold text-3xl mb-8">Sign in</h2>

        <form @submit.prevent="handleLogin" class="space-y-4">
          <div>
            <label class="section-label block mb-2">Email</label>
            <input
              v-model="form.email"
              type="email"
              class="input-field"
              placeholder="you@example.com"
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
            {{ loading ? 'Signing in...' : 'Sign In' }}
          </button>
        </form>

        <div class="mt-8 pt-6 border-t border-ink/10">
          <p class="text-xs text-muted text-center mb-3 font-mono">Demo credentials</p>
          <button @click="fillDemo" class="w-full border border-ink/20 py-2 text-xs font-mono text-slate hover:border-accent hover:text-accent transition-colors">
            anjali@smu.edu.sg / password123
          </button>
        </div>

        <p class="mt-6 text-center text-xs text-muted">
          Admin?
          <router-link to="/admin/login" class="text-accent hover:underline ml-1">Admin login →</router-link>
        </p>
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
  form.value.email = 'anjali@smu.edu.sg'
  form.value.password = 'password123'
}

async function handleLogin() {
  error.value = ''
  loading.value = true
  await new Promise(r => setTimeout(r, 800))

  if (form.value.email === 'anjali@smu.edu.sg' && form.value.password === 'password123') {
    router.push('/listings')
  } else {
    error.value = 'Invalid email or password.'
  }
  loading.value = false
}
</script>
