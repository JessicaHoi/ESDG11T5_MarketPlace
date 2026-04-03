<template>
  <div class="min-h-screen bg-paper">
    <SellerNavbar :seller="mockSeller" />

    <div class="pt-16">
      <div class="max-w-4xl mx-auto px-6 pt-8">
        <button @click="$router.back()" class="section-label text-muted hover:text-accent transition-colors">← My Orders</button>
      </div>

      <div v-if="loading" class="max-w-4xl mx-auto px-6 py-16 text-center">
        <p class="font-mono text-sm text-muted">Loading order...</p>
      </div>

      <div v-else-if="!order" class="text-center py-32">
        <p class="font-display text-2xl text-muted">Order not found.</p>
        <router-link to="/seller/orders" class="btn-ghost mt-4 inline-block">Back to orders</router-link>
      </div>

      <div v-else class="max-w-4xl mx-auto px-6 py-6">
        <div class="grid grid-cols-1 lg:grid-cols-5 gap-8">

          <!-- Left: order details -->
          <div class="lg:col-span-3 space-y-5">
            <!-- Product -->
            <div class="bg-white border border-ink/10 p-6 flex gap-5 items-start">
              <div class="w-24 h-24 bg-cream overflow-hidden flex-shrink-0 flex items-center justify-center">
                <img v-if="listingImage" :src="listingImage" :alt="order.order_details" class="w-full h-full object-cover" />
                <span v-else class="text-4xl text-ink/10">🛍</span>
              </div>
              <div class="flex-1">
                <div class="flex items-center gap-2 mb-1">
                  <span class="status-badge text-xs font-mono" :class="badgeClass(order.status)">{{ order.status }}</span>
                </div>
                <h1 class="font-display font-extrabold text-xl leading-tight mb-1">
                  {{ order.order_details || `Listing #${order.listing_id}` }}
                </h1>
                <p class="text-xs text-muted font-mono">Buyer ID: {{ order.buyer_id }}</p>
              </div>
            </div>

            <!-- Order details -->
            <div class="bg-white border border-ink/10 p-6">
              <p class="section-label mb-4">Order Details</p>
              <div class="space-y-3 text-sm">
                <div class="flex justify-between py-2 border-b border-ink/5">
                  <span class="text-muted font-mono text-xs uppercase tracking-wider">Order ID</span>
                  <span class="font-mono">#{{ order.order_id }}</span>
                </div>
                <div class="flex justify-between py-2 border-b border-ink/5">
                  <span class="text-muted font-mono text-xs uppercase tracking-wider">Date</span>
                  <span class="font-mono">{{ formatDate(order.created_at) }}</span>
                </div>
                <div class="flex justify-between py-2 border-b border-ink/5">
                  <span class="text-muted font-mono text-xs uppercase tracking-wider">Amount</span>
                  <span class="font-display font-bold text-accent">${{ order.agreed_price }}</span>
                </div>
                <div class="flex justify-between py-2">
                  <span class="text-muted font-mono text-xs uppercase tracking-wider">Listing ID</span>
                  <span class="font-mono">#{{ order.listing_id }}</span>
                </div>
              </div>
            </div>

            <!-- Status -->
            <div class="bg-cream border border-ink/10 p-5">
              <p class="section-label mb-2">Status</p>
              <p class="font-mono text-sm text-slate">{{ statusText(order.status) }}</p>
            </div>
          </div>

          <!-- Right: actions -->
          <div class="lg:col-span-2">
            <div class="bg-white border border-ink/10 p-6 sticky top-24 space-y-3">
              <p class="section-label mb-2">Actions</p>

              <!-- Message buyer -->
              <button
                @click="$router.push(`/seller/messages/${order.order_id}`)"
                class="btn-primary w-full py-3 text-sm"
              >
                💬 Message Buyer
              </button>

              <!-- Mark as shipped / completed — only for RESERVED -->
              <button
                v-if="order.status === 'RESERVED'"
                @click="handleMarkShipped"
                :disabled="marking"
                class="btn-secondary w-full py-3 text-sm"
              >
                {{ marking ? 'Updating...' : 'Mark as Delivered' }}
              </button>

              <div v-if="order.status === 'DISPUTED'" class="bg-red-50 border border-red-200 p-3 text-xs text-red-700 font-mono">
                ⚠ A dispute has been raised for this order. Contact admin if needed.
              </div>

              <div v-if="order.status === 'COMPLETED'" class="bg-sage/5 border border-sage/20 p-3 text-xs text-sage font-mono">
                ✓ Funds have been released to you.
              </div>

              <p v-if="actionError" class="text-xs text-red-600 font-mono">{{ actionError }}</p>
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
import SellerNavbar from '../../components/SellerNavbar.vue'
import { mockSeller } from '../../data/mockData.js'
import { getOrdersBySeller, updateOrder, fetchListings } from '../../services/api.js'

const route   = useRoute()
const router  = useRouter()
const orderID = parseInt(route.params.id)

const order       = ref(null)
const loading     = ref(true)
const marking     = ref(false)
const actionError = ref(null)
const listingImages = ref({})

const listingImage = computed(() =>
  order.value ? listingImages.value[order.value.listing_id] || null : null
)

onMounted(async () => {
  try {
    const [ordersData, listingsData] = await Promise.all([
      getOrdersBySeller(mockSeller.id),
      fetchListings().catch(() => null),
    ])
    const all = Array.isArray(ordersData) ? ordersData : (ordersData.orders ?? [])
    order.value = all.find(o => o.order_id === orderID) || null
    const listings = listingsData?.data?.listings ?? listingsData?.listings ?? []
    listings.forEach(l => {
      if (l.listingImgUrl && l.listingImgUrl.length > 5) {
        listingImages.value[l.listingID] = l.listingImgUrl
      }
    })
  } catch (err) {
    console.error('Failed to load order:', err)
  } finally {
    loading.value = false
  }
})

async function handleMarkShipped() {
  marking.value     = true
  actionError.value = null
  try {
    // Seller marks delivered — buyer still needs to confirm receipt to release funds
    // We update order_details to note delivery, status stays RESERVED until buyer confirms
    const updated = await updateOrder(orderID, { order_details: order.value.order_details + ' [Delivered]' })
    order.value = updated
  } catch (err) {
    actionError.value = err.message || 'Failed to update order.'
  } finally {
    marking.value = false
  }
}

function badgeClass(status) {
  return {
    RESERVED:  'bg-amber-100 text-amber-700',
    COMPLETED: 'bg-sage/20 text-sage',
    DISPUTED:  'bg-red-100 text-red-700',
    REFUNDED:  'bg-purple-100 text-purple-700',
  }[status] || 'bg-cream text-ink'
}

function statusText(status) {
  return {
    RESERVED:  'Payment held in escrow. Deliver the item and wait for buyer to confirm receipt.',
    COMPLETED: 'Buyer confirmed receipt. Funds have been released to you.',
    DISPUTED:  'Buyer has raised a dispute. Funds are frozen pending admin review.',
    REFUNDED:  'Buyer was refunded. This order is now closed.',
  }[status] || status
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-SG', { day: 'numeric', month: 'short', year: 'numeric' })
}
</script>
