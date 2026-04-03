<template>
  <div class="min-h-screen bg-paper">
    <Navbar :user="mockUser" />

    <div class="pt-16">
      <!-- Back -->
      <div class="max-w-6xl mx-auto px-6 pt-8">
        <button @click="$router.back()" class="section-label text-muted hover:text-accent transition-colors">← Browse</button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="max-w-6xl mx-auto px-6 py-16 text-center">
        <p class="font-mono text-sm text-muted">Loading listing...</p>
      </div>

      <!-- Error / not found -->
      <div v-else-if="apiError || !listing" class="text-center py-32">
        <p class="font-display text-2xl text-muted">{{ apiError || 'Listing not found.' }}</p>
        <router-link to="/listings" class="btn-ghost mt-4 inline-block">Back to listings</router-link>
      </div>

      <!-- Listing content -->
      <div v-else class="max-w-6xl mx-auto px-6 py-6">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-12">

          <!-- Image -->
          <div>
            <div class="aspect-[4/3] bg-cream overflow-hidden flex items-center justify-center">
              <img
                v-if="listing.listingImgUrl && listing.listingImgUrl.length > 5"
                :src="listing.listingImgUrl"
                :alt="listing.listingName"
                class="w-full h-full object-cover"
                @error="onImageError"
              />
              <span v-else class="text-8xl text-ink/10">🛍</span>
            </div>
          </div>

          <!-- Details -->
          <div class="flex flex-col">
            <!-- Category + status/order badge -->
            <div class="flex items-start justify-between mb-2">
              <span class="section-label text-accent">{{ listing.listingCategory || 'General' }}</span>
              <!-- Order status badge takes priority over listing status -->
              <span
                v-if="orderBadge"
                class="status-badge font-mono text-xs px-3 py-1"
                :class="orderBadge.class"
              >
                {{ orderBadge.label }}
              </span>
              <span v-else class="status-badge bg-cream text-ink font-mono text-xs">
                {{ listing.listingStatus || 'ACTIVE' }}
              </span>
            </div>

            <!-- Title -->
            <h1 class="font-display font-extrabold text-3xl leading-tight mb-4">
              {{ listing.listingName }}
            </h1>

            <!-- Price -->
            <div class="flex items-baseline gap-3 mb-6">
              <span v-if="negotiatedPrice" class="font-display font-extrabold text-4xl text-accent">
                ${{ parseFloat(negotiatedPrice).toFixed(2) }}
              </span>
              <span
                class="font-display font-extrabold text-4xl"
                :class="negotiatedPrice ? 'line-through text-ink/30 text-2xl' : 'text-accent'"
              >
                ${{ parseFloat(listing.listingPrice).toFixed(2) }}
              </span>
            </div>
            <div v-if="negotiatedPrice" class="bg-sage/10 border border-sage/20 px-3 py-2 mb-6 flex items-center gap-2">
              <span class="text-sage text-sm">🤝</span>
              <p class="text-xs text-sage font-mono">Negotiated price agreed — this is the amount you'll pay at checkout</p>
            </div>

            <!-- Stock -->
            <div class="flex items-center gap-2 mb-6">
              <span
                v-if="listing.listingStockQty > 1"
                class="text-xs font-mono text-sage bg-sage/10 px-3 py-1"
              >
                {{ listing.listingStockQty }} available
              </span>
              <span
                v-else-if="listing.listingStockQty === 1"
                class="text-xs font-mono text-amber-600 bg-amber-50 px-3 py-1"
              >
                Only 1 left
              </span>
              <span
                v-else
                class="text-xs font-mono text-red-600 bg-red-50 px-3 py-1"
              >
                Out of stock
              </span>
            </div>

            <!-- Description -->
            <div class="mb-6">
              <p class="section-label mb-3">Description</p>
              <p class="text-slate text-sm leading-relaxed">
                {{ listing.listingDescription || 'No description provided.' }}
              </p>
            </div>

            <!-- Meta -->
            <div class="grid grid-cols-2 gap-4 mb-8 text-xs font-mono">
              <div class="bg-cream p-3">
                <p class="text-muted mb-1">Listed</p>
                <p class="text-ink font-medium">{{ formatDate(listing.listingCreated) }}</p>
              </div>
              <div class="bg-cream p-3">
                <p class="text-muted mb-1">Listing ID</p>
                <p class="text-ink font-medium">#{{ listing.listingID }}</p>
              </div>
            </div>

            <!-- Escrow notice -->
            <div class="border border-sage/30 bg-sage/5 p-4 mb-6 flex gap-3">
              <span class="text-sage text-lg">🔒</span>
              <div>
                <p class="font-display font-semibold text-sm text-sage mb-1">Escrow Protected</p>
                <p class="text-xs text-slate leading-relaxed">
                  Your payment is held securely until you confirm receipt of the item.
                </p>
              </div>
            </div>

            <!-- Actions -->
            <div class="flex gap-3 mt-auto">
              <button
                @click="negotiate"
                :disabled="listing.listingStockQty <= 0"
                class="btn-secondary flex-1"
                :class="{ 'opacity-50 cursor-not-allowed': listing.listingStockQty <= 0 }"
              >
                Negotiate
              </button>
              <button
                @click="buyNow"
                :disabled="listing.listingStockQty <= 0"
                class="btn-primary flex-1"
                :class="{ 'opacity-50 cursor-not-allowed': listing.listingStockQty <= 0 }"
              >
                {{ listing.listingStockQty > 0 ? 'Buy Now' : 'Out of Stock' }}
              </button>
            </div>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Navbar from '../../components/Navbar.vue'
import { mockUser } from '../../data/mockData.js'
import { fetchListingById, getOrders } from '../../services/api.js'
import { getDeal } from '../../data/negotiationStore.js'

const route  = useRoute()
const router = useRouter()

const listing  = ref(null)
const loading  = ref(true)
const apiError = ref(null)
const orders   = ref([])
const negotiatedPrice = ref(null)

// Find an order matching this listing for the current user
const matchingOrder = computed(() => {
  if (!listing.value) return null
  return orders.value.find(
    o => String(o.listing_id) === String(listing.value.listingID)
  ) || null
})

const orderBadge = computed(() => {
  if (!matchingOrder.value) return null
  if (matchingOrder.value.status === 'RESERVED') {
    return { label: 'Ordered — Pending Delivery', class: 'bg-amber-100 text-amber-700' }
  }
  if (matchingOrder.value.status === 'COMPLETED') {
    return { label: 'Previously Purchased', class: 'bg-sage/20 text-sage' }
  }
  if (matchingOrder.value.status === 'DISPUTED') {
    return { label: 'Dispute In Progress', class: 'bg-red-100 text-red-600' }
  }
  return null
})

onMounted(async () => {
  try {
    const [listingRes, ordersData] = await Promise.all([
      fetchListingById(route.params.id),
      getOrders().catch(() => []),
    ])
    const data = listingRes?.data ?? null
    if (data && data.listingName) {
      listing.value = data
      // Check negotiation store for a previously agreed price
      const deal = getDeal(data.listingID)
      if (deal && deal.price && deal.price !== data.listingPrice) {
        negotiatedPrice.value = deal.price
      }
    } else {
      apiError.value = 'Listing not found.'
    }
    orders.value = Array.isArray(ordersData) ? ordersData : (ordersData.orders ?? [])
  } catch (err) {
    apiError.value = err.message || 'Failed to load listing.'
  } finally {
    loading.value = false
  }
})

function negotiate() {
  router.push(`/messages/${listing.value.listingID}`)
}

function buyNow() {
  const query = {}
  if (negotiatedPrice.value) {
    query.price = negotiatedPrice.value
  }
  router.push({ path: `/purchase/${listing.value.listingID}`, query })
}

function onImageError(e) {
  e.target.style.display = 'none'
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-SG', {
    day: 'numeric', month: 'short', year: 'numeric'
  })
}
</script>
