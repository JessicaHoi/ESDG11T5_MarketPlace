<template>
  <div class="min-h-screen bg-paper">
    <Navbar :user="mockUser" />

    <div class="pt-16">
      <div class="max-w-4xl mx-auto px-6 pt-8">
        <button @click="$router.back()" class="section-label text-muted hover:text-accent transition-colors">← My Orders</button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="max-w-4xl mx-auto px-6 py-16 text-center">
        <p class="font-mono text-sm text-muted">Loading order details...</p>
      </div>

      <!-- Not found -->
      <div v-else-if="!order" class="text-center py-32">
        <p class="font-display text-2xl text-muted">Order not found.</p>
        <router-link to="/orders" class="btn-ghost mt-4 inline-block">Back to orders</router-link>
      </div>

      <!-- Content -->
      <div v-else class="max-w-4xl mx-auto px-6 py-6">
        <div class="grid grid-cols-1 lg:grid-cols-5 gap-8">

          <!-- Left: product info -->
          <div class="lg:col-span-3 space-y-5">

            <!-- Product image + name -->
            <div class="bg-white border border-ink/10 p-6 flex gap-5 items-start">
              <div class="w-24 h-24 bg-cream overflow-hidden flex-shrink-0 flex items-center justify-center">
                <img
                  v-if="listingImage"
                  :src="listingImage"
                  :alt="order.order_details"
                  class="w-full h-full object-cover"
                />
                <span v-else class="text-4xl text-ink/10">🛍</span>
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <span class="status-badge font-mono text-xs" :class="paymentBadgeClass(order.status)">
                    {{ order.status }}
                  </span>
                  <span v-if="order.status === 'DISPUTED' && disputeStatus" class="status-badge font-mono text-xs bg-red-100 text-red-700">
                    {{ disputeStatus }}
                  </span>
                </div>
                <h1 class="font-display font-extrabold text-xl leading-tight mb-1">
                  {{ order.order_details || `Listing #${order.listing_id}` }}
                </h1>
                <p class="text-xs text-muted font-mono">Seller ID: {{ order.seller_id }}</p>
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
                  <span class="text-muted font-mono text-xs uppercase tracking-wider">Date Placed</span>
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

            <!-- Status explanation -->
            <div class="bg-cream border border-ink/10 p-5">
              <p class="section-label mb-2">Status</p>
              <p class="font-mono text-sm text-slate">{{ statusText(order.status) }}</p>
            </div>

          </div>

          <!-- Right: action panel -->
          <div class="lg:col-span-2">
            <div class="bg-white border border-ink/10 p-6 sticky top-24 space-y-4">
              <p class="section-label mb-2">Actions</p>

              <!-- Message Seller -->
              <button
                @click="$router.push(`/messages/${order.listing_id}`)"
                class="btn-primary w-full py-3 text-sm mb-2"
              >
                💬 Message Seller
              </button>

              <!-- RESERVED: waiting for seller to deliver -->
              <template v-if="order.status === 'RESERVED'">
                <div class="bg-amber-50 border border-amber-200 p-3 text-xs text-amber-700 font-mono leading-relaxed mb-2">
                  ⏳ Your payment is held in escrow. Waiting for seller to mark the item as delivered.
                </div>
                <button
                  @click="$router.push(`/orders/${order.order_id}/dispute`)"
                  class="w-full py-3 text-sm font-display font-semibold border border-red-200 text-red-500 hover:bg-red-50 transition-colors"
                >
                  Raise Dispute
                </button>
              </template>

              <!-- DELIVERED: seller marked delivered, buyer can confirm -->
              <template v-if="order.status === 'DELIVERED'">
                <div class="bg-blue-50 border border-blue-200 p-3 text-xs text-blue-700 font-mono leading-relaxed mb-2">
                  📦 Seller has marked this item as delivered. Please confirm once you receive it.
                </div>
                <button
                  @click="handleConfirmReceipt"
                  :disabled="confirming"
                  class="btn-secondary w-full py-3 text-sm"
                >
                  {{ confirming ? 'Confirming...' : 'Confirm Receipt' }}
                </button>
                <button
                  @click="$router.push(`/orders/${order.order_id}/dispute`)"
                  class="w-full py-3 text-sm font-display font-semibold border border-red-200 text-red-500 hover:bg-red-50 transition-colors"
                >
                  Raise Dispute
                </button>
              </template>

              <!-- COMPLETED / REFUNDED / DISPUTED: Buy Again -->
              <template v-else>
                <div
                  class="p-3 text-xs font-mono leading-relaxed mb-2"
                  :class="order.status === 'REFUNDED'
                    ? 'bg-purple-50 border border-purple-200 text-purple-700'
                    : order.status === 'DISPUTED'
                    ? 'bg-red-50 border border-red-200 text-red-700'
                    : 'bg-sage/5 border border-sage/20 text-sage'"
                >
                  {{ statusNote(order.status) }}
                </div>
                <button
                  v-if="order.status === 'DISPUTED'"
                  @click="goToDispute"
                  class="btn-secondary w-full py-3 text-sm mb-2"
                >
                  View Dispute
                </button>
                <button
                  @click="$router.push(`/listings/${order.listing_id}`)"
                  class="btn-primary w-full py-3 text-sm"
                >
                  Buy Again
                </button>
              </template>

              <!-- Per-order error -->
              <p v-if="actionError" class="text-xs text-red-600 font-mono mt-2">{{ actionError }}</p>
            </div>
          </div>

        </div>
      </div>
    </div>
  </div>

  <!-- Cancel confirmation modal -->
  <div v-if="showCancelConfirm" class="fixed inset-0 bg-ink/60 flex items-center justify-center z-50 p-6">
    <div class="bg-paper max-w-sm w-full p-8 text-center">
      <div class="w-14 h-14 bg-red-100 flex items-center justify-center mx-auto mb-4 text-2xl">⚠</div>
      <h2 class="font-display font-extrabold text-xl mb-2">Cancel this order?</h2>
      <p class="text-slate text-sm mb-6 leading-relaxed">
        This will cancel order #{{ order?.order_id }} and initiate a refund. This action cannot be undone.
      </p>
      <div class="flex gap-3">
        <button @click="showCancelConfirm = false" class="btn-secondary flex-1">Keep Order</button>
        <button
          @click="handleCancel"
          :disabled="cancelling"
          class="flex-1 bg-red-600 text-white font-display font-semibold py-3 hover:bg-red-700 transition-colors text-sm"
        >
          {{ cancelling ? 'Cancelling...' : 'Yes, Cancel' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Navbar from '../../components/Navbar.vue'
import { mockUser } from '../../data/mockData.js'
import { getOrders, confirmOrder, updateOrder, fetchListings, getDisputes, getDisputesByOrder, releasePayment } from '../../services/api.js'

const route  = useRoute()
const router = useRouter()
const orderID = parseInt(route.params.id)

const order        = ref(null)
const loading      = ref(true)
const listingImages = ref({})
const confirming   = ref(false)
const cancelling   = ref(false)
const actionError  = ref(null)
const showCancelConfirm = ref(false)
const disputeStatus = ref(null)
let pollHandle = null

const listingImage = computed(() => {
  if (!order.value) return null
  return listingImages.value[order.value.listing_id] || null
})

onMounted(async () => {
  try {
    const [ordersData, listingsData] = await Promise.all([
      getOrders(),
      fetchListings().catch(() => null),
    ])
    const all = Array.isArray(ordersData) ? ordersData : (ordersData.orders ?? [])
    const found = all.find(o => o.order_id === orderID)
    if (found) {
      order.value = found
      if (found.status === 'DISPUTED') {
        getDisputesByOrder(orderID).then(res => {
          const disputes = res?.data?.disputes ?? res?.data ?? []
          const foundDispute = disputes.find(d => d.orderID === orderID)
          if (foundDispute) disputeStatus.value = foundDispute.disputeStatus
        }).catch(() => {})
      }
    }
    // Build image lookup
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

  // Poll for status updates
  pollHandle = setInterval(async () => {
    if (order.value && ['COMPLETED', 'REFUNDED'].includes(order.value.status)) {
      clearInterval(pollHandle)
      return
    }
    try {
      const ordersData = await getOrders()
      const all = Array.isArray(ordersData) ? ordersData : (ordersData.orders ?? [])
      const found = all.find(o => o.order_id === orderID)
      if (found && found.status !== order.value?.status) {
        order.value = found
      }
      if (order.value?.status === 'DISPUTED') {
        getDisputesByOrder(orderID).then(res => {
          const disputes = res?.data?.disputes ?? res?.data ?? []
          const foundDispute = disputes.find(d => d.orderID === orderID)
          if (foundDispute) disputeStatus.value = foundDispute.disputeStatus
        }).catch(() => {})
      }
    } catch (e) {
      // silently ignore polling errors
    }
  }, 5000)
})

onUnmounted(() => {
  if (pollHandle) clearInterval(pollHandle)
})

async function goToDispute() {
  try {
    const res = await getDisputes()
    const disputes = res?.data?.disputes ?? res?.data ?? []
    const found = disputes.find(d => d.orderID === order.value.order_id)
    if (found) {
      router.push(`/disputes/${found.disputeID}`)
    } else {
      actionError.value = "Dispute not found."
    }
  } catch (e) {
    actionError.value = "Error fetching dispute."
  }
}

async function handleConfirmReceipt() {
  confirming.value = true
  actionError.value = null
  try {
    // Step 1: Update order status to COMPLETED
    const updated = await confirmOrder(orderID)
    order.value = updated

    // Step 2: Release escrowed funds to seller via Payment Service
    await releasePayment(orderID).catch(err =>
      console.warn('[Payment] Release failed:', err.message)
    )

  } catch (err) {
    actionError.value = err.message || 'Failed to confirm receipt.'
  } finally {
    confirming.value = false
  }
}

async function handleCancel() {
  cancelling.value = true
  actionError.value = null
  try {
    const updated = await updateOrder(orderID, { status: 'REFUNDED' })
    order.value = updated
    showCancelConfirm.value = false
  } catch (err) {
    actionError.value = err.message || 'Failed to cancel order.'
    showCancelConfirm.value = false
  } finally {
    cancelling.value = false
  }
}

function statusText(status) {
  const map = {
    RESERVED:  'Payment held in escrow — waiting for seller to deliver the item.',
    DELIVERED: 'Seller has marked item as delivered — please confirm receipt.',
    COMPLETED: 'Funds released to seller — transaction complete',
    DISPUTED:  'Funds frozen — dispute under review',
    REFUNDED:  'Refunded to your original payment method',
  }
  return map[status] || status
}

function statusNote(status) {
  const map = {
    COMPLETED: '✓ This order was completed. You can buy this item again.',
    REFUNDED:  '↩ This order was refunded. You can buy this item again.',
    DISPUTED:  '⚠ This order is under dispute. You can buy this item again once resolved.',
  }
  return map[status] || ''
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
