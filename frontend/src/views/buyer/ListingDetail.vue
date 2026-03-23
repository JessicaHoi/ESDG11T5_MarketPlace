<template>
  <div class="min-h-screen bg-paper">
    <Navbar :user="mockUser" />

    <div class="pt-16">
      <!-- Back always visible -->
      <div class="max-w-6xl mx-auto px-6 pt-8">
        <button @click="$router.back()" class="section-label text-muted hover:text-accent transition-colors">← Browse</button>
      </div>

      <!-- Listing not found -->
      <div v-if="!listing" class="text-center py-32">
        <p class="font-display text-2xl text-muted">Listing not found.</p>
        <router-link to="/listings" class="btn-ghost mt-4 inline-block">Back to listings</router-link>
      </div>

      <!-- Listing content -->
      <div v-else class="max-w-6xl mx-auto px-6 py-6">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-12">
          <!-- Image -->
          <div>
            <div class="aspect-[4/3] bg-cream overflow-hidden">
              <img :src="listing.image" :alt="listing.title" class="w-full h-full object-cover" />
            </div>
            <div class="mt-4 grid grid-cols-3 gap-2">
              <div v-for="i in 3" :key="i" class="aspect-square bg-cream overflow-hidden opacity-60 hover:opacity-100 transition-opacity cursor-pointer">
                <img :src="listing.image" :alt="listing.title" class="w-full h-full object-cover" />
              </div>
            </div>
          </div>

          <!-- Details -->
          <div class="flex flex-col">
            <div class="flex items-start justify-between mb-2">
              <span class="section-label text-accent">{{ listing.category }}</span>
              <span class="status-badge bg-cream text-ink">{{ listing.condition }}</span>
            </div>

            <h1 class="font-display font-extrabold text-3xl leading-tight mb-4">{{ listing.title }}</h1>

            <div class="flex items-baseline gap-3 mb-6">
              <span class="font-display font-extrabold text-4xl text-accent">${{ listing.price }}</span>
              <span class="text-muted font-mono line-through text-sm">${{ listing.originalPrice }}</span>
              <span class="text-sage text-sm font-mono">{{ savingsPercent }}% off</span>
            </div>

            <!-- Seller card -->
            <div class="bg-cream p-4 mb-6 flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-ink text-paper font-display font-bold flex items-center justify-center text-sm">
                  {{ listing.seller.charAt(0) }}
                </div>
                <div>
                  <p class="font-display font-semibold text-sm">{{ listing.seller }}</p>
                  <p class="text-xs text-muted font-mono">{{ listing.location }}</p>
                </div>
              </div>
              <div class="text-right">
                <div class="flex items-center gap-1">
                  <span class="text-accent text-sm">★</span>
                  <span class="font-mono text-sm font-medium">{{ listing.sellerRating }}</span>
                </div>
                <p class="text-xs text-muted font-mono">Seller rating</p>
              </div>
            </div>

            <!-- Description -->
            <div class="mb-6">
              <p class="section-label mb-3">Description</p>
              <p class="text-slate text-sm leading-relaxed">{{ listing.description }}</p>
            </div>

            <!-- Meta -->
            <div class="grid grid-cols-2 gap-4 mb-8 text-xs font-mono">
              <div class="bg-cream p-3">
                <p class="text-muted mb-1">Listed</p>
                <p class="text-ink font-medium">{{ listing.listedAt }}</p>
              </div>
              <div class="bg-cream p-3">
                <p class="text-muted mb-1">Views</p>
                <p class="text-ink font-medium">{{ listing.views }}</p>
              </div>
            </div>

            <!-- Escrow notice -->
            <div class="border border-sage/30 bg-sage/5 p-4 mb-6 flex gap-3">
              <span class="text-sage text-lg">🔒</span>
              <div>
                <p class="font-display font-semibold text-sm text-sage mb-1">Escrow Protected</p>
                <p class="text-xs text-slate leading-relaxed">Your payment is held securely until you confirm receipt of the item.</p>
              </div>
            </div>

            <!-- Actions -->
            <div class="flex gap-3 mt-auto">
              <button @click="reserve" class="btn-secondary flex-1">Reserve Item</button>
              <button @click="buyNow" class="btn-primary flex-1">Buy Now</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watchEffect } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Navbar from '../../components/Navbar.vue'
import { mockListings, mockUser } from '../../data/mockData.js'

const route = useRoute()
const router = useRouter()

const listing = ref(null)
const savingsPercent = ref(0)

watchEffect(() => {
  const found = mockListings.find(l => l.id === parseInt(route.params.id))
  listing.value = found || null
  if (found) {
    savingsPercent.value = Math.round((1 - found.price / found.originalPrice) * 100)
  }
})

function reserve() {
  router.push(`/messages/${listing.value.id}`)
}

function buyNow() {
  router.push(`/purchase/${listing.value.id}`)
}
</script>
