<template>
  <div class="min-h-screen bg-paper">
    <Navbar :user="mockUser" />

    <div class="pt-16">
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
        <div v-if="loading" class="text-center py-20 text-muted font-mono text-sm">Loading disputes...</div>

        <template v-else>
          <div class="flex gap-1 mb-6 border-b border-ink/10">
            <button v-for="tab in tabs" :key="tab.value" @click="activeTab = tab.value"
              class="section-label px-4 py-3 border-b-2 transition-colors -mb-px"
              :class="activeTab === tab.value ? 'border-accent text-accent' : 'border-transparent text-muted hover:text-ink'">
              {{ tab.label }} <span class="ml-1.5 font-mono text-xs">{{ tabCount(tab.value) }}</span>
            </button>
          </div>

          <div class="mb-6">
            <input v-model="search" type="text" class="input-field max-w-xs" placeholder="Search dispute ID, listing..." />
          </div>

          <div class="space-y-3">
            <div v-for="d in filteredDisputes" :key="d.disputeID"
              class="bg-white border border-ink/10 hover:border-accent/40 transition-all cursor-pointer group"
              @click="$router.push(`/disputes/${d.disputeID}`)">
              <div class="p-5 flex items-center gap-4">
                <div class="w-1.5 self-stretch flex-shrink-0 rounded-full" :class="statusBar(d.disputeStatus)"></div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-3 mb-2 flex-wrap">
                    <span class="font-mono font-medium text-sm text-ink">DIS-{{ d.disputeID }}</span>
                    <span class="inline-flex items-center px-2 py-0.5 text-xs font-mono font-medium uppercase tracking-wider" :class="statusBadge(d.disputeStatus)">{{ d.disputeStatus }}</span>
                    <span class="font-mono text-xs text-muted">ORD-{{ d.orderID }}</span>
                  </div>
                  <p class="font-display font-semibold text-base text-ink leading-tight mb-1 group-hover:text-accent transition-colors">{{ d.listingTitle || 'Dispute' }}</p>
                  <div class="flex items-center gap-4 flex-wrap">
                    <span class="text-xs text-slate font-mono">Seller #{{ d.sellerID }}</span>
                    <span class="text-xs text-muted font-mono">{{ formatDate(d.createdAt) }}</span>
                  </div>
                </div>
                <div class="text-right flex-shrink-0">
                  <p class="font-display font-bold text-lg text-accent">${{ d.amount || 0 }}</p>
                  <p class="text-xs text-muted font-mono mt-1">{{ (d.disputeReason || '').replace(/_/g, ' ') }}</p>
                </div>
                <span class="text-muted group-hover:text-accent transition-colors ml-2">→</span>
              </div>
            </div>

            <div v-if="filteredDisputes.length === 0" class="text-center py-16">
              <p class="font-display font-semibold text-2xl text-ink/30">No disputes found</p>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import Navbar from '../../components/Navbar.vue'
import { mockUser } from '../../data/mockData.js'
import { getDisputesByBuyer } from '../../services/api.js'

const disputes = ref([])
const loading = ref(true)
const activeTab = ref('all')
const search = ref('')

onMounted(async () => {
  try {
    const res = await getDisputesByBuyer(mockUser.id)
    disputes.value = res?.data?.disputes ?? []
  } catch (err) { console.error('Failed to load disputes:', err) }
  finally { loading.value = false }
})

const tabs = [
  { label: 'All', value: 'all' }, { label: 'Open', value: 'OPEN' },
  { label: 'Response', value: 'RESPONSE' }, { label: 'Approved', value: 'APPROVED' }, { label: 'Rejected', value: 'REJECTED' },
]

const stats = computed(() => [
  { label: 'Total', value: disputes.value.length, color: 'text-paper' },
  { label: 'Open', value: disputes.value.filter(d => d.disputeStatus === 'OPEN').length, color: 'text-amber-400' },
  { label: 'Approved', value: disputes.value.filter(d => d.disputeStatus === 'APPROVED').length, color: 'text-sage' },
  { label: 'Rejected', value: disputes.value.filter(d => d.disputeStatus === 'REJECTED').length, color: 'text-red-400' },
])

const filteredDisputes = computed(() => {
  return disputes.value.filter(d => {
    const matchTab = activeTab.value === 'all' || d.disputeStatus === activeTab.value
    const q = search.value.toLowerCase()
    const matchSearch = !q || String(d.disputeID).includes(q) || (d.listingTitle || '').toLowerCase().includes(q)
    return matchTab && matchSearch
  })
})

function tabCount(tab) { return tab === 'all' ? disputes.value.length : disputes.value.filter(d => d.disputeStatus === tab).length }
function statusBar(s) { return { OPEN: 'bg-amber-400', RESPONSE: 'bg-blue-400', AWAITING_DECISION: 'bg-purple-400', APPROVED: 'bg-sage', REJECTED: 'bg-red-500' }[s] || 'bg-ink/20' }
function statusBadge(s) { return { OPEN: 'bg-amber-100 text-amber-700', RESPONSE: 'bg-blue-100 text-blue-700', AWAITING_DECISION: 'bg-purple-100 text-purple-700', APPROVED: 'bg-sage/20 text-sage', REJECTED: 'bg-red-100 text-red-600' }[s] || 'bg-ink/10 text-slate' }
function formatDate(iso) { if (!iso) return '—'; return new Date(iso).toLocaleDateString('en-SG', { day: 'numeric', month: 'short', year: 'numeric' }) }
</script>
