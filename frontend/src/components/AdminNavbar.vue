<template>
  <nav class="fixed top-0 left-0 right-0 bg-ink border-b border-white/10 z-50">
    <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
      <div class="flex items-center gap-8">
        <router-link to="/admin/disputes" class="font-display font-extrabold text-xl tracking-tight text-paper">
          Trade<span class="text-accent">Nest</span>
          <span class="ml-2 text-xs font-mono text-white/40 border border-white/20 px-1.5 py-0.5 align-middle">Admin</span>
        </router-link>
        <div class="hidden md:flex gap-6">
          <router-link to="/admin/disputes" class="text-sm font-semibold text-white/60 hover:text-accent transition-colors">Disputes</router-link>
        </div>
      </div>
      <div class="flex items-center gap-4">
        <span class="text-sm font-mono text-white/40 border border-white/10 px-3 py-1">admin@tradenest.sg</span>
        <button
          @click="$router.push('/admin')"
          class="text-sm font-mono text-red-400 border border-red-400/30 px-3 py-1 hover:bg-red-400/10 transition-colors"
        >Logout</button>
      </div>
    </div>
  </nav>
</template>

<script setup>
</script>
