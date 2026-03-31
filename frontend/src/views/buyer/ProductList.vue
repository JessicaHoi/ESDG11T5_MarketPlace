<template>
  <div class="min-h-screen bg-paper">
    <Navbar :user="mockUser" />

    <div class="pt-16">
      <div class="bg-ink text-paper py-10 px-6">
        <div class="max-w-6xl mx-auto">
          <p class="section-label text-white/40 mb-2">Marketplace</p>
          <h1 class="font-display font-extrabold text-4xl">Browse Products</h1>
        </div>
      </div>

      <div class="max-w-6xl mx-auto px-6 py-10">
        <!-- Error State -->
        <div v-if="apiError" class="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm font-mono">
          ⚠ {{ apiError }}
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
          <div v-for="n in 8" :key="n" class="bg-white border border-ink/10 h-72 animate-pulse"></div>
        </div>

        <!-- Empty State -->
        <div v-else-if="validListings.length === 0" class="text-center py-20">
          <p class="font-display font-semibold text-2xl text-ink/40">No products available at the moment.</p>
        </div>

        <!-- Listings Grid -->
        <div v-else class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
          <div
            v-for="item in validListings"
            :key="item.listingID"
            @click="$router.push('/listings/' + item.listingID)"
            class="bg-white border border-ink/10 flex flex-col cursor-pointer transition-all hover:border-ink/30 hover:shadow-lg group"
          >
            <!-- Image Container -->
            <div class="aspect-square bg-cream w-full relative overflow-hidden flex items-center justify-center">
              <img 
                v-if="item.listingImgUrl && item.listingImgUrl.length > 5" 
                :src="item.listingImgUrl" 
                :alt="item.listingName"
                class="object-cover w-full h-full group-hover:scale-105 transition-transform duration-500"
                @error="onImageError"
              />
              <span v-else class="text-6xl text-ink/10 group-hover:scale-110 transition-transform duration-500">🛍</span>
              
              <!-- Category Badge -->
              <span class="absolute top-3 left-3 bg-white/90 backdrop-blur text-ink border border-ink/10 text-[10px] font-mono uppercase px-2 py-1 tracking-wider">
                {{ item.listingCategory || 'General' }}
              </span>
            </div>

            <!-- Content Container -->
            <div class="p-5 flex-1 flex flex-col">
              <h3 class="font-display font-bold text-lg leading-tight mb-1 text-ink group-hover:text-accent transition-colors">
                {{ item.listingName }}
              </h3>
              
              <p class="text-xs text-slate font-sans line-clamp-2 leading-relaxed flex-1 mb-4">
                {{ item.listingDescription || 'No description provided.' }}
              </p>

              <div class="flex items-end justify-between mt-auto pt-4 border-t border-ink/5">
                <div>
                  <p class="text-[10px] font-mono uppercase text-muted mb-0.5">Price</p>
                  <p class="font-display font-extrabold text-xl text-ink tracking-tight">
                    ${{ parseFloat(item.listingPrice).toFixed(2) }}
                  </p>
                </div>
                
                <span v-if="item.listingStockQty > 0" class="text-xs font-mono text-sage bg-sage/10 px-2 py-1">
                  Ready
                </span>
                <span v-else class="text-xs font-mono text-amber-600 bg-amber-50 px-2 py-1">
                  1 Left
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import Navbar from '../../components/Navbar.vue'
import { mockUser } from '../../data/mockData.js'
import { fetchListings } from '../../services/api.js'

const listings = ref([])
const loading = ref(true)
const apiError = ref(null)

const validListings = computed(() => {
  if (!listings.value || !Array.isArray(listings.value)) return []
  return listings.value.filter(item => {
    // Exclude empty shells and inactive listings
    return item.is_active === true && 
           item.listingName && 
           item.listingName.trim().length > 0
  })
})

onMounted(async () => {
  try {
    const response = await fetchListings()
    // Extract array from OutSystems structure
    listings.value = response?.data?.listings || []
  } catch (err) {
    apiError.value = "Failed to load marketplace listings from the server."
    console.error(err)
  } finally {
    loading.value = false
  }
})

// Fallback if the remote image hits a 404
function onImageError(e) {
  e.target.style.display = 'none'
  if (e.target.nextElementSibling) {
    e.target.nextElementSibling.style.display = 'block'
  }
}
</script>
