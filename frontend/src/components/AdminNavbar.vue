<template>
  <nav class="fixed top-0 left-0 right-0 z-50 bg-ink border-b border-white/10">
    <div class="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <span class="font-display font-extrabold text-xl tracking-tight text-paper">
          Trade<span class="text-accent">Nest</span>
        </span>
        <span class="section-label text-white/40 border border-white/20 px-2 py-0.5">Admin</span>
      </div>

      <div class="flex items-center gap-6">
        <router-link
          to="/admin/disputes"
          class="section-label text-white/60 hover:text-accent transition-colors"
          :class="{ 'text-accent': $route.path.startsWith('/admin/disputes') }"
        >Disputes</router-link>
        <button
          @click="handleLogout"
          class="w-20 h-10 bg-accent text-white font-display font-bold text-xs flex items-center justify-center hover:bg-white hover:text-ink transition-colors"
        >Logout</button>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
function handleLogout() { router.push('/admin/login') }
</script>
