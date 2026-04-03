<template>
  <nav class="fixed top-0 left-0 right-0 bg-paper/80 backdrop-blur-md border-b border-ink/10 z-50">
    <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
      <div class="flex items-center gap-8">
        <router-link to="/seller/dashboard" class="font-display font-extrabold text-xl tracking-tight">
          TradeNest
          <span class="ml-2 text-xs font-mono text-accent border border-accent/30 px-1.5 py-0.5 align-middle">Seller</span>
        </router-link>
        <div class="hidden md:flex gap-6">
          <router-link to="/seller/dashboard" class="text-sm font-semibold hover:text-accent transition-colors">Dashboard</router-link>
          <router-link to="/seller/orders" class="text-sm font-semibold hover:text-accent transition-colors">My Orders</router-link>
          <router-link to="/seller/disputes" class="text-sm font-semibold hover:text-accent transition-colors">Disputes</router-link>
          <router-link to="/seller/inbox" class="text-sm font-semibold hover:text-accent transition-colors">Inbox</router-link>
        </div>
      </div>
      <div class="flex items-center gap-4">
        <span class="text-sm font-mono text-slate border border-ink/10 px-3 py-1 bg-white">{{ seller.name }}</span>
        <button
          @click="$router.push('/seller')"
          class="text-sm font-mono text-red-400 border border-red-200 px-3 py-1 hover:bg-red-50 hover:text-red-600 transition-colors"
        >Logout</button>
      </div>
    </div>
  </nav>
</template>

<script setup>
defineProps({ seller: { type: Object, required: true } })
</script>
