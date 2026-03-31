<template>
  <div class="min-h-screen bg-paper">
    <Navbar :user="mockUser" />

    <div class="pt-16">
      <div class="bg-ink text-paper py-10 px-6">
        <div class="max-w-3xl mx-auto">
          <p class="section-label text-white/40 mb-2">Account</p>
          <h1 class="font-display font-extrabold text-4xl">My Profile</h1>
        </div>
      </div>

      <div class="max-w-3xl mx-auto px-6 py-10 space-y-6">

        <!-- Avatar + name -->
        <div class="bg-white border border-ink/10 p-6 flex items-center gap-6">
          <div class="w-16 h-16 bg-ink text-paper font-display font-extrabold text-2xl flex items-center justify-center flex-shrink-0">
            {{ mockUser.name.charAt(0) }}
          </div>
          <div>
            <h2 class="font-display font-bold text-xl">{{ mockUser.name }}</h2>
            <p class="text-xs font-mono text-muted mt-1">{{ roleLabel }}</p>
          </div>
        </div>

        <!-- Account details -->
        <div class="bg-white border border-ink/10 p-6">
          <p class="section-label mb-5">Account Details</p>
          <div class="space-y-4">
            <div class="flex justify-between items-center py-3 border-b border-ink/5">
              <span class="text-xs font-mono text-muted uppercase tracking-wider">Full Name</span>
              <span class="font-display font-medium text-sm">{{ mockUser.name }}</span>
            </div>
            <div class="flex justify-between items-center py-3 border-b border-ink/5">
              <span class="text-xs font-mono text-muted uppercase tracking-wider">Email</span>
              <span class="font-mono text-sm">{{ mockUser.email }}</span>
            </div>
            <div class="flex justify-between items-center py-3 border-b border-ink/5">
              <span class="text-xs font-mono text-muted uppercase tracking-wider">User ID</span>
              <span class="font-mono text-sm text-muted">#{{ mockUser.id }}</span>
            </div>
            <div class="flex justify-between items-center py-3">
              <span class="text-xs font-mono text-muted uppercase tracking-wider">Role</span>
              <span class="status-badge bg-cream text-ink font-mono text-xs">{{ roleLabel }}</span>
            </div>
          </div>
        </div>

        <!-- Quick links -->
        <div class="bg-white border border-ink/10 p-6">
          <p class="section-label mb-5">Quick Links</p>
          <div class="space-y-2">
            <router-link
              to="/listings"
              class="flex items-center justify-between p-3 hover:bg-cream transition-colors group"
            >
              <span class="text-sm font-display font-medium group-hover:text-accent transition-colors">Browse Listings</span>
              <span class="text-muted text-xs font-mono">→</span>
            </router-link>
            <router-link
              to="/orders"
              class="flex items-center justify-between p-3 hover:bg-cream transition-colors group"
            >
              <span class="text-sm font-display font-medium group-hover:text-accent transition-colors">My Orders</span>
              <span class="text-muted text-xs font-mono">→</span>
            </router-link>
          </div>
        </div>

        <!-- Sign out -->
        <div class="pt-2">
          <button @click="handleSignOut" class="btn-ghost w-full py-3 text-sm text-red-500 hover:text-red-600 border border-red-200 hover:border-red-300 transition-colors">
            Sign Out
          </button>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import Navbar from '../../components/Navbar.vue'
import { mockUser } from '../../data/mockData.js'

const router = useRouter()

const roleLabel = computed(() => {
  return mockUser.role === 'admin' ? 'Administrator' : 'Buyer'
})

function handleSignOut() {
  router.push('/login')
}
</script>
