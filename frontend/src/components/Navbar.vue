<template>
  <nav class="fixed top-0 left-0 right-0 z-50 bg-paper border-b border-ink/10">
    <div class="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
      <!-- Logo -->
      <router-link to="/listings" class="font-display font-extrabold text-xl tracking-tight">
        Trade<span class="text-accent">Nest</span>
      </router-link>

      <!-- Nav links -->
      <div class="flex items-center gap-6">
        <router-link
          to="/listings"
          class="section-label hover:text-accent transition-colors"
          :class="{ 'text-accent': $route.path === '/listings' }"
        >Browse</router-link>
        <router-link
          to="/orders"
          class="section-label hover:text-accent transition-colors"
          :class="{ 'text-accent': $route.path === '/orders' }"
        >My Orders</router-link>

        <!-- Avatar -->
        <button
          @click="handleLogout"
          class="w-20 h-10 bg-ink text-paper font-display font-bold text-xs flex items-center justify-center hover:bg-accent transition-colors"
          title="Logout"
        >Logout </button>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  user: { type: Object, default: () => ({ name: 'Anjali R.' }) }
})

const router = useRouter()

const initials = computed(() => {
  return props.user.name.split(' ').map(n => n[0]).join('').toUpperCase()
})

function handleLogout() {
  router.push('/login')
}
</script>
