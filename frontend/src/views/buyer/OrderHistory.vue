<template>
  <div class="min-h-screen bg-paper">
    <Navbar :user="mockUser" />

    <div class="pt-16">
      <div class="bg-ink text-paper py-10 px-6">
        <div class="max-w-4xl mx-auto">
          <p class="section-label text-white/40 mb-2">{{ orders.length }} orders</p>
          <h1 class="font-display font-extrabold text-4xl">My Orders</h1>
        </div>
      </div>

      <div class="max-w-4xl mx-auto px-6 py-8">

        <!-- API error banner -->
        <div v-if="apiError" class="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm font-mono">
          ⚠ {{ apiError }} — showing cached data where available.
        </div>

        <!-- Loading -->
        <div v-if="loading" class="text-center py-20 text-muted font-mono text-sm">
          Loading orders...
        </div>

        <template v-else>
          <!-- Tab filters -->
          <div class="flex gap-1 mb-8 border-b border-ink/10">
            <button
              v-for="tab in tabs"
              :key="tab.value"
              @click="activeTab = tab.value"
              class="section-label px-4 py-3 border-b-2 transition-colors -mb-px"
              :class="activeTab === tab.value
                ? 'border-accent text-accent'
                : 'border-transparent text-muted hover:text-ink'"
            >{{ tab.label }}</button>
          </div>

          <!-- Orders list -->
          <div class="space-y-4">
            <div
              v-for="order in filteredOrders"
              :key="order.order_id"
              class="bg-white border border-ink/10 p-6 hover:border-ink/30 hover:shadow-sm transition-all cursor-pointer group"
              @click="$router.push(`/orders/${order.order_id}`)"
            >
              <div class="flex gap-4">
                <div class="w-20 h-20 bg-cream overflow-hidden flex-shrink-0 flex items-center justify-center">
                  <img
                    v-if="listingImages[order.listing_id]"
                    :src="listingImages[order.listing_id]"
                    :alt="order.order_details"
                    class="w-full h-full object-cover"
                  />
                  <span v-else class="text-3xl">🛍</span>
                </div>

                <div class="flex-1 min-w-0">
                  <div class="flex items-start justify-between gap-4 flex-wrap">
                    <div>
                      <div class="flex items-center gap-2 mb-1">
                        <span class="font-mono text-xs text-muted">Order #{{ order.order_id }}</span>
                        <span class="status-badge" :class="paymentBadgeClass(order.status)">{{ order.status }}</span>
                      </div>
                      <h3 class="font-display font-semibold text-base leading-tight">
                        {{ order.order_details || `Listing #${order.listing_id}` }}
                      </h3>
                      <p class="text-xs text-muted font-mono mt-1">
                        Seller ID: {{ order.seller_id }} · {{ formatDate(order.created_at) }}
                      </p>
                    </div>
                    <div class="text-right flex-shrink-0">
                      <p class="font-display font-bold text-xl text-accent">${{ order.agreed_price }}</p>
                    </div>
                  </div>

                  <!-- Status info -->
                  <div class="mt-4 bg-cream p-3">
                    <p class="section-label mb-1">Order Status</p>
                    <p class="font-mono text-xs text-slate">{{ statusText(order.status) }}</p>
                  </div>

                  <!-- Actions -->
                  <div class="mt-4 flex gap-2 flex-wrap items-center">
                    <!-- Confirm receipt (only when RESERVED) -->
                    <button
                      v-if="order.status === 'RESERVED'"
                      @click.stop="handleConfirmReceipt(order)"
                      :disabled="confirmingID === order.order_id"
                      class="btn-secondary text-xs px-4 py-2"
                    >
                      {{ confirmingID === order.order_id ? 'Confirming...' : 'Confirm Receipt' }}
                    </button>

                    <!-- Raise dispute (only when RESERVED) -->
                    <button
                      v-if="order.status === 'RESERVED'"
                      @click.stop="$router.push(`/orders/${order.order_id}/dispute`)"
                      class="btn-ghost text-xs px-4 py-2 text-red-600 hover:text-red-700"
                    >
                      Raise Dispute
                    </button>

                    <span v-if="order.status === 'COMPLETED'" class="text-xs font-mono text-sage flex items-center gap-1">
                      ✓ Completed — funds released to seller
                    </span>
                    <span v-if="order.status === 'DISPUTED'" class="text-xs font-mono text-red-600 flex items-center gap-1">
                      ⚠ Dispute in progress — payment frozen
                    </span>
                    <span v-if="order.status === 'REFUNDED'" class="text-xs font-mono text-purple-600 flex items-center gap-1">
                      ↩ Refunded to your original payment method
                    </span>
                  </div>

                  <!-- Per-order error -->
                  <p v-if="confirmError[order.order_id]" class="mt-2 text-xs text-red-600 font-mono">
                    {{ confirmError[order.order_id] }}
                  </p>
                </div>
              </div>
            </div>

            <div v-if="filteredOrders.length === 0" class="text-center py-16">
              <p class="font-display font-semibold text-2xl text-ink/30">No orders yet</p>
              <router-link to="/listings" class="btn-primary inline-block mt-4">Browse Listings</router-link>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated } from 'vue'
import Navbar from '../../components/Navbar.vue'
import { mockUser } from '../../data/mockData.js'
import { getOrders, confirmOrder } from '../../services/api.js'
import { getOrderStatusFromDispute } from '../../data/disputeStore.js'

const orders      = ref([])
const loading     = ref(true)
const apiError    = ref(null)
const activeTab   = ref('all')
const confirmingID = ref(null)
const confirmError = ref({})
const listingImages = ref({}) // listingID → listingImgUrl

const tabs = [
  { label: 'All Orders',  value: 'all' },
  { label: 'In Escrow',   value: 'RESERVED' },
  { label: 'Completed',   value: 'COMPLETED' },
  { label: 'Disputes',    value: 'DISPUTED' },
]

const filteredOrders = computed(() => {
  if (activeTab.value === 'all') return orders.value
  return orders.value.filter(o => o.status === activeTab.value)
})

onMounted(async () => {
  try {
    const [ordersData, listingsData] = await Promise.all([
      getOrders(),
      fetch('/tmp.json').then(r => r.json()).catch(() => null),
    ])
    const rawOrders = Array.isArray(ordersData) ? ordersData : (ordersData.orders ?? [])
    orders.value = applyDisputeOverrides(rawOrders)
    // Build lookup map: listingID → listingImgUrl
    const listings = listingsData?.data?.listings ?? []
    listings.forEach(l => {
      if (l.listingImgUrl && l.listingImgUrl.length > 5) {
        listingImages.value[l.listingID] = l.listingImgUrl
      }
    })
  } catch (err) {
    apiError.value = err.message || 'Could not load orders.'
  } finally {
    loading.value = false
  }
})

// Re-apply dispute overrides every time the user navigates back to this page
// (handles the case where admin resolved a dispute while user was elsewhere)
onActivated(() => {
  if (orders.value.length > 0) {
    orders.value = applyDisputeOverrides(orders.value)
  }
})

function applyDisputeOverrides(rawOrders) {
  return rawOrders.map(order => {
    if (order.status !== 'DISPUTED') return order
    const overrideStatus = getOrderStatusFromDispute(order.order_id)
    if (!overrideStatus) return order
    return { ...order, status: overrideStatus }
  })
}

async function handleConfirmReceipt(order) {
  confirmingID.value = order.order_id
  confirmError.value[order.order_id] = null
  try {
    const updated = await confirmOrder(order.order_id)
    // Update in-place so UI reflects change immediately
    const idx = orders.value.findIndex(o => o.order_id === order.order_id)
    if (idx !== -1) orders.value[idx] = updated
  } catch (err) {
    confirmError.value[order.order_id] = err.message || 'Failed to confirm receipt.'
  } finally {
    confirmingID.value = null
  }
}

function statusText(status) {
  const map = {
    RESERVED:  'Payment held in escrow — awaiting your confirmation of receipt',
    COMPLETED: 'Funds released to seller — transaction complete',
    DISPUTED:  'Funds frozen — dispute under review',
    REFUNDED:  'Refunded to your original payment method',
  }
  return map[status] || status
}

function paymentBadgeClass(status) {
  return {
    RESERVED:  'bg-amber-100 text-amber-700',
    COMPLETED: 'bg-sage/20 text-sage',
    DISPUTED:  'bg-red-100 text-red-700',
    REFUNDED:  'bg-purple-100 text-purple-700',
  }[status] || 'bg-cream text-ink'
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-SG', { day: 'numeric', month: 'short', year: 'numeric' })
}
</script>
