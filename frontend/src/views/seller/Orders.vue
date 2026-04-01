<template>
  <div class="min-h-screen bg-paper">
    <SellerNavbar :seller="mockSeller" />

    <div class="pt-16">
      <div class="bg-ink text-paper py-10 px-6">
        <div class="max-w-5xl mx-auto">
          <p class="section-label text-white/40 mb-2">{{ orders.length }} orders</p>
          <h1 class="font-display font-extrabold text-4xl">My Orders</h1>
        </div>
      </div>

      <div class="max-w-5xl mx-auto px-6 py-8">
        <!-- Tabs -->
        <div class="flex gap-1 mb-8 border-b border-ink/10">
          <button
            v-for="tab in tabs" :key="tab.value"
            @click="activeTab = tab.value"
            class="section-label px-4 py-3 border-b-2 transition-colors -mb-px"
            :class="activeTab === tab.value ? 'border-accent text-accent' : 'border-transparent text-muted hover:text-ink'"
          >{{ tab.label }}</button>
        </div>

        <div v-if="loading" class="text-center py-20 text-muted font-mono text-sm">Loading orders...</div>

        <div v-else class="space-y-4">
          <div
            v-for="order in filteredOrders" :key="order.order_id"
            class="bg-white border border-ink/10 p-6 hover:border-ink/30 transition-all cursor-pointer group"
            @click="$router.push(`/seller/orders/${order.order_id}`)"
          >
            <div class="flex gap-4">
              <div class="w-16 h-16 bg-cream overflow-hidden flex-shrink-0 flex items-center justify-center">
                <img v-if="listingImages[order.listing_id]" :src="listingImages[order.listing_id]" class="w-full h-full object-cover" />
                <span v-else class="text-2xl">🛍</span>
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-start justify-between gap-4 flex-wrap">
                  <div>
                    <div class="flex items-center gap-2 mb-1">
                      <span class="font-mono text-xs text-muted">Order #{{ order.order_id }}</span>
                      <span class="status-badge text-xs font-mono" :class="badgeClass(order.status)">{{ order.status }}</span>
                    </div>
                    <h3 class="font-display font-semibold text-base group-hover:text-accent transition-colors">
                      {{ order.order_details || `Listing #${order.listing_id}` }}
                    </h3>
                    <p class="text-xs text-muted font-mono mt-1">Buyer ID: {{ order.buyer_id }} · {{ formatDate(order.created_at) }}</p>
                  </div>
                  <p class="font-display font-bold text-xl text-accent">${{ order.agreed_price }}</p>
                </div>
                <div class="mt-3 bg-cream p-3">
                  <p class="font-mono text-xs text-slate">{{ statusText(order.status) }}</p>
                </div>
              </div>
            </div>
          </div>

          <div v-if="filteredOrders.length === 0" class="text-center py-16">
            <p class="font-display font-semibold text-2xl text-ink/30">No orders found</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import SellerNavbar from '../../components/SellerNavbar.vue'
import { mockSeller } from '../../data/mockData.js'
import { getOrdersBySeller } from '../../services/api.js'

const orders     = ref([])
const loading    = ref(true)
const activeTab  = ref('all')
const listingImages = ref({})

const tabs = [
  { label: 'All',       value: 'all' },
  { label: 'Pending',   value: 'RESERVED' },
  { label: 'Completed', value: 'COMPLETED' },
  { label: 'Disputed',  value: 'DISPUTED' },
]

const filteredOrders = computed(() =>
  activeTab.value === 'all' ? orders.value : orders.value.filter(o => o.status === activeTab.value)
)

onMounted(async () => {
  try {
    const [ordersData, listingsData] = await Promise.all([
      getOrdersBySeller(mockSeller.id),
      fetch('/tmp.json').then(r => r.json()).catch(() => null),
    ])
    orders.value = Array.isArray(ordersData) ? ordersData : (ordersData.orders ?? [])
    const listings = listingsData?.data?.listings ?? []
    listings.forEach(l => {
      if (l.listingImgUrl && l.listingImgUrl.length > 5) {
        listingImages.value[l.listingID] = l.listingImgUrl
      }
    })
  } catch (err) {
    console.error('Failed to load orders:', err)
  } finally {
    loading.value = false
  }
})

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
    RESERVED:  'Payment held in escrow — awaiting buyer confirmation of receipt',
    COMPLETED: 'Funds released to you — transaction complete',
    DISPUTED:  'Buyer has raised a dispute — funds frozen pending review',
    REFUNDED:  'Buyer was refunded — transaction closed',
  }[status] || status
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-SG', { day: 'numeric', month: 'short', year: 'numeric' })
}
</script>
