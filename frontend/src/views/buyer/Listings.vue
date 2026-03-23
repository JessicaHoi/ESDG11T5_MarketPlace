<template>
  <div class="min-h-screen bg-paper">
    <Navbar :user="mockUser" />

    <div class="pt-16">
      <!-- Hero bar -->
      <div class="bg-ink text-paper py-10 px-6">
        <div class="max-w-6xl mx-auto">
          <p class="section-label text-white/40 mb-2">{{ filteredListings.length }} listings available</p>
          <h1 class="font-display font-extrabold text-4xl">Browse Listings</h1>
        </div>
      </div>

      <div class="max-w-6xl mx-auto px-6 py-8">
        <!-- Filters row -->
        <div class="flex flex-wrap gap-3 mb-8 items-center">
          <input
            v-model="search"
            type="text"
            placeholder="Search listings..."
            class="input-field max-w-xs"
          />
          <select v-model="selectedCategory" class="input-field max-w-[160px]">
            <option value="">All Categories</option>
            <option v-for="cat in categories" :key="cat">{{ cat }}</option>
          </select>
          <select v-model="selectedCondition" class="input-field max-w-[160px]">
            <option value="">All Conditions</option>
            <option>Like New</option>
            <option>Good</option>
            <option>Fair</option>
          </select>
          <button @click="clearFilters" class="btn-ghost text-slate">Clear</button>
        </div>

        <!-- Grid -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <div
            v-for="listing in filteredListings"
            :key="listing.id"
            class="card group cursor-pointer"
            @click="$router.push(`/listings/${listing.id}`)"
          >
            <!-- Image -->
            <div class="relative overflow-hidden aspect-[4/3] bg-cream">
              <img
                :src="listing.image"
                :alt="listing.title"
                class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
              />
              <div class="absolute top-3 left-3">
                <span class="status-badge bg-paper/90 text-ink">{{ listing.condition }}</span>
              </div>
              <div class="absolute top-3 right-3">
                <span class="section-label bg-ink/80 text-paper px-2 py-1">{{ listing.category }}</span>
              </div>
            </div>

            <!-- Content -->
            <div class="p-4">
              <h3 class="font-display font-semibold text-base leading-tight mb-1 group-hover:text-accent transition-colors">
                {{ listing.title }}
              </h3>
              <div class="flex items-center justify-between mt-3">
                <div>
                  <span class="font-display font-bold text-xl text-ink">${{ listing.price }}</span>
                  <span class="text-muted text-xs font-mono line-through ml-2">${{ listing.originalPrice }}</span>
                </div>
                <span class="text-xs text-muted font-mono">{{ listing.location }}</span>
              </div>
              <div class="mt-3 pt-3 border-t border-ink/5 flex items-center justify-between">
                <span class="text-xs text-slate">{{ listing.seller }}</span>
                <span class="text-xs text-muted font-mono">{{ listing.views }} views</span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="filteredListings.length === 0" class="text-center py-20">
          <p class="font-display font-semibold text-2xl text-ink/30">No listings found</p>
          <button @click="clearFilters" class="btn-ghost mt-4">Clear filters</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import Navbar from '../../components/Navbar.vue'
import { mockListings, mockUser } from '../../data/mockData.js'

const search = ref('')
const selectedCategory = ref('')
const selectedCondition = ref('')

const categories = [...new Set(mockListings.map(l => l.category))]

const filteredListings = computed(() => {
  return mockListings.filter(l => {
    const matchSearch = !search.value || l.title.toLowerCase().includes(search.value.toLowerCase())
    const matchCat = !selectedCategory.value || l.category === selectedCategory.value
    const matchCond = !selectedCondition.value || l.condition === selectedCondition.value
    return matchSearch && matchCat && matchCond
  })
})

function clearFilters() {
  search.value = ''
  selectedCategory.value = ''
  selectedCondition.value = ''
}
</script>
