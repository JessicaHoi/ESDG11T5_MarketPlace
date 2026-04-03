<template>
  <div class="min-h-screen bg-paper text-ink">
    <Navbar :user="mockUser" />

    <div class="pt-16">
      <!-- Header -->
      <div class="bg-ink text-paper py-10 px-6">
        <div class="max-w-5xl mx-auto">
          <div class="flex gap-6 mb-6">
            <div v-for="stat in stats" :key="stat.label" class="text-center">
              <p class="font-display font-extrabold text-2xl" :class="stat.color">{{ stat.value }}</p>
              <p class="section-label text-white/40">{{ stat.label }}</p>
            </div>
          </div>
          <h1 class="font-display font-extrabold text-4xl">My Disputes</h1>
        </div>
      </div>

      <div class="max-w-5xl mx-auto px-6 py-8">
        <!-- Filter tabs -->
        <div class="flex gap-1 mb-6 border-b border-ink/10">
          <button
            v-for="tab in tabs"
            :key="tab.value"
            @click="activeTab = tab.value"
            class="section-label px-4 py-3 border-b-2 transition-colors -mb-px"
            :class="activeTab === tab.value
              ? 'border-accent text-accent'
              : 'border-transparent text-muted hover:text-ink'"
          >
            {{ tab.label }}
            <span class="ml-1.5 font-mono text-xs">{{ tabCount(tab.value) }}</span>
          </button>
        </div>

        <!-- Search -->
        <div class="mb-6">
          <input
            v-model="search"
            type="text"
            class="input-field max-w-xs"
            placeholder="Search dispute ID, seller, listing..."
          />
        </div>

        <!-- Disputes list -->
        <div class="space-y-3">
          <div
            v-for="dispute in filteredDisputes"
            :key="dispute.id"
            class="bg-white border border-ink/10 hover:border-accent/40 transition-all cursor-pointer group"
            @click="$router.push(`/disputes/${dispute.id}`)"
          >
            <div class="p-5 flex items-center gap-4">
              <!-- Status indicator -->
              <div class="w-1.5 self-stretch flex-shrink-0 rounded-full" :class="statusBar(dispute.status)"></div>

              <!-- Main info -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-3 mb-2 flex-wrap">
                  <span class="font-mono font-medium text-sm text-ink">{{ dispute.id }}</span>
                  <StatusBadge :status="dispute.status" />
                  <span class="font-mono text-xs text-muted">{{ dispute.orderID }}</span>
                </div>
                <p class="font-display font-semibold text-base text-ink leading-tight mb-1 group-hover:text-accent transition-colors">
                  {{ dispute.listing }}
                </p>
                <div class="flex items-center gap-4 flex-wrap">
                  <span class="text-xs text-slate font-mono">Seller: {{ dispute.sellerName }}</span>
                  <span class="text-xs text-muted font-mono">{{ dispute.raisedAt }}</span>
                </div>
              </div>

              <!-- Right side -->
              <div class="text-right flex-shrink-0">
                <p class="font-display font-bold text-lg text-accent">${{ dispute.amount }}</p>
                <p class="text-xs text-muted font-mono mt-1">{{ dispute.reason.replace(/_/g, ' ') }}</p>
                <div class="flex items-center gap-1 justify-end mt-2">
                  <span class="text-xs text-muted font-mono">{{ dispute.evidence.length }} files</span>
                  <span class="text-muted">·</span>
                  <span class="text-xs text-muted font-mono">Deadline: {{ dispute.deadline }}</span>
                </div>
              </div>

              <span class="text-muted group-hover:text-accent transition-colors ml-2">→</span>
            </div>
          </div>

          <div v-if="filteredDisputes.length === 0" class="text-center py-16">
            <p class="font-display font-semibold text-2xl text-ink/30">No disputes found</p>
            <p class="text-sm text-muted font-mono mt-2">Disputes you've filed will appear here</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import Navbar from '../../components/Navbar.vue'
import { mockDisputes, mockUser } from '../../data/mockData.js'
import { getMergedDisputes } from '../../data/disputeStore.js'

const disputes = ref([])

onMounted(() => {
  const all = getMergedDisputes(mockDisputes)
  // Filter to disputes filed by this buyer
  disputes.value = all.filter(d =>
    d.buyerName === mockUser.name ||
    d.buyerName === `Buyer #${mockUser.id}`
  )
})

const activeTab = ref('all')
const search = ref('')

const tabs = [
  { label: 'All', value: 'all' },
  { label: 'Pending', value: 'PENDING' },
  { label: 'Approved', value: 'APPROVED' },
  { label: 'Rejected', value: 'REJECTED' },
]

const stats = computed(() => [
  { label: 'Total', value: disputes.value.length, color: 'text-paper' },
  { label: 'Pending', value: disputes.value.filter(d => d.status === 'PENDING').length, color: 'text-amber-400' },
  { label: 'Approved', value: disputes.value.filter(d => d.status === 'APPROVED').length, color: 'text-sage' },
  { label: 'Rejected', value: disputes.value.filter(d => d.status === 'REJECTED').length, color: 'text-red-400' },
])

const filteredDisputes = computed(() => {
  return disputes.value.filter(d => {
    const matchTab = activeTab.value === 'all' || d.status === activeTab.value
    const matchSearch = !search.value ||
      d.id.toLowerCase().includes(search.value.toLowerCase()) ||
      d.sellerName.toLowerCase().includes(search.value.toLowerCase()) ||
      d.listing.toLowerCase().includes(search.value.toLowerCase())
    return matchTab && matchSearch
  })
})

function tabCount(tab) {
  if (tab === 'all') return disputes.value.length
  return disputes.value.filter(d => d.status === tab).length
}

function statusBar(status) {
  return {
    PENDING:  'bg-amber-400',
    APPROVED: 'bg-sage',
    REJECTED: 'bg-red-500',
  }[status] || 'bg-ink/20'
}

const StatusBadge = {
  props: ['status'],
  template: `
    <span class="inline-flex items-center px-2 py-0.5 text-xs font-mono font-medium uppercase tracking-wider" :class="cls">{{ label }}</span>
  `,
  computed: {
    cls() {
      return {
        PENDING:  'bg-amber-100 text-amber-700',
        APPROVED: 'bg-sage/20 text-sage',
        REJECTED: 'bg-red-100 text-red-600',
      }[this.status] || 'bg-ink/10 text-slate'
    },
    label() { return this.status }
  }
}
</script>
