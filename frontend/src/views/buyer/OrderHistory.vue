<template>
  <div class="min-h-screen bg-paper">
    <Navbar :user="mockUser" />

    <div class="pt-16">
      <div class="bg-ink text-paper py-10 px-6">
        <div class="max-w-4xl mx-auto">
          <p class="section-label text-white/40 mb-2">{{ mockOrders.length }} orders</p>
          <h1 class="font-display font-extrabold text-4xl">My Orders</h1>
        </div>
      </div>

      <div class="max-w-4xl mx-auto px-6 py-8">
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
            :key="order.id"
            class="bg-white border border-ink/10 p-6 hover:border-ink/30 transition-colors"
          >
            <div class="flex gap-4">
              <!-- Thumbnail -->
              <div class="w-20 h-20 bg-cream overflow-hidden flex-shrink-0">
                <img :src="order.image" :alt="order.listing" class="w-full h-full object-cover" />
              </div>

              <!-- Main content -->
              <div class="flex-1 min-w-0">
                <div class="flex items-start justify-between gap-4 flex-wrap">
                  <div>
                    <div class="flex items-center gap-2 mb-1">
                      <span class="font-mono text-xs text-muted">{{ order.id }}</span>
                      <StatusBadge :status="order.paymentStatus" />
                    </div>
                    <h3 class="font-display font-semibold text-base leading-tight">{{ order.listing }}</h3>
                    <p class="text-xs text-muted font-mono mt-1">Seller: {{ order.seller }} · {{ order.createdAt }}</p>
                  </div>
                  <div class="text-right flex-shrink-0">
                    <p class="font-display font-bold text-xl text-accent">${{ order.amount }}</p>
                    <StatusBadge :status="order.orderStatus" class="mt-1" />
                  </div>
                </div>

                <!-- Payment info -->
                <div class="mt-4 bg-cream p-3">
                  <p class="section-label mb-1">Payment Status</p>
                  <div class="flex items-center gap-2">
                    <span class="font-mono text-xs text-slate">{{ paymentStatusText(order.paymentStatus) }}</span>
                  </div>
                  <p class="font-mono text-xs text-muted mt-1 truncate">Intent: {{ order.stripePaymentIntentID }}</p>
                </div>

                <!-- Actions -->
                <div class="mt-4 flex gap-2 flex-wrap">
                  <button
                    v-if="order.paymentStatus === 'HELD' && order.orderStatus !== 'Dispute Raised'"
                    @click="confirmReceipt(order)"
                    class="btn-secondary text-xs px-4 py-2"
                  >Confirm Receipt</button>

                  <button
                    v-if="order.paymentStatus === 'HELD' && order.orderStatus !== 'Dispute Raised'"
                    @click="$router.push(`/orders/${order.id}/dispute`)"
                    class="btn-ghost text-xs px-4 py-2 text-red-600 hover:text-red-700"
                  >Raise Dispute</button>

                  <span
                    v-if="order.orderStatus === 'Dispute Raised'"
                    class="text-xs font-mono text-red-600 flex items-center gap-1"
                  >⚠ Dispute in progress — payment frozen</span>

                  <span
                    v-if="order.paymentStatus === 'RELEASED'"
                    class="text-xs font-mono text-sage flex items-center gap-1"
                  >✓ Funds released to seller</span>

                  <span
                    v-if="order.paymentStatus === 'REFUNDED'"
                    class="text-xs font-mono text-purple-600 flex items-center gap-1"
                  >↩ Refunded to your card</span>
                </div>
              </div>
            </div>
          </div>

          <div v-if="filteredOrders.length === 0" class="text-center py-16">
            <p class="font-display font-semibold text-2xl text-ink/30">No orders yet</p>
            <router-link to="/listings" class="btn-primary inline-block mt-4">Browse Listings</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import Navbar from '../../components/Navbar.vue'
import StatusBadge from '../../components/StatusBadge.vue'
import { mockOrders, mockUser } from '../../data/mockData.js'

const orders = ref([...mockOrders])
const activeTab = ref('all')

const tabs = [
  { label: 'All Orders', value: 'all' },
  { label: 'In Escrow', value: 'HELD' },
  { label: 'Completed', value: 'RELEASED' },
  { label: 'Disputes', value: 'FROZEN' },
]

const filteredOrders = computed(() => {
  if (activeTab.value === 'all') return orders.value
  return orders.value.filter(o => o.paymentStatus === activeTab.value)
})

function paymentStatusText(status) {
  const map = {
    HELD: 'Funds held in escrow — awaiting your confirmation',
    RELEASED: 'Funds released to seller',
    FROZEN: 'Funds frozen — dispute under review',
    REFUNDED: 'Refunded to your original payment method',
  }
  return map[status] || status
}

function confirmReceipt(order) {
  const idx = orders.value.findIndex(o => o.id === order.id)
  if (idx !== -1) {
    orders.value[idx] = {
      ...orders.value[idx],
      paymentStatus: 'RELEASED',
      orderStatus: 'Completed',
    }
  }
}
</script>
