<template>
  <nav class="fixed top-0 left-0 right-0 bg-paper/80 backdrop-blur-md border-b border-ink/10 z-50">
    <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
      <div class="flex items-center gap-8">
        <router-link to="/" class="font-display font-extrabold text-xl tracking-tight">TradeNest</router-link>
        <div class="hidden md:flex gap-6">
          <router-link to="/listings" class="text-sm font-semibold hover:text-accent transition-colors">Browse Products</router-link>
          <router-link to="/orders" class="text-sm font-semibold hover:text-accent transition-colors">My Orders</router-link>
        </div>
      </div>
      <div class="flex items-center gap-4">
        <span v-if="user" class="text-sm font-mono text-slate border border-ink/10 px-3 py-1 bg-white">{{ user.name }}</span>
      </div>
    </div>
  </nav>
</template>

<script setup>
defineProps({
  user: Object
})
</script>
