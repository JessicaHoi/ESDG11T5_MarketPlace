<template>
  <div class="min-h-screen bg-paper text-ink">
    <AdminNavbar />

    <div class="pt-16">
      <!-- Back always visible -->
      <div class="max-w-4xl mx-auto px-6 pt-8">
        <button @click="$router.back()" class="section-label text-muted hover:text-accent transition-colors">← All Disputes</button>
      </div>

      <div v-if="dispute" class="max-w-4xl mx-auto px-6 py-6">

        <!-- Header -->
        <div class="flex items-start justify-between flex-wrap gap-4 mb-8">
          <div>
            <div class="flex items-center gap-3 mb-2">
              <span class="font-mono font-medium text-sm text-slate">{{ dispute.id }}</span>
              <span
                class="inline-flex items-center px-2.5 py-0.5 text-xs font-mono font-medium uppercase tracking-wider"
                :class="statusBadgeClass"
              >{{ dispute.status }}</span>
            </div>
            <h1 class="font-display font-extrabold text-3xl">{{ dispute.listing }}</h1>
            <p class="text-muted font-mono text-sm mt-1">Order {{ dispute.orderID }} · Filed {{ dispute.raisedAt }}</p>
          </div>
          <div class="text-right">
            <p class="font-display font-extrabold text-3xl text-accent">${{ dispute.amount }}</p>
            <p class="text-muted font-mono text-xs mt-1">Funds currently frozen</p>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <!-- Main content -->
          <div class="lg:col-span-2 space-y-5">
            <!-- Parties -->
            <div class="bg-cream border border-ink/10 p-5">
              <p class="section-label text-muted mb-4">Involved Parties</p>
              <div class="grid grid-cols-2 gap-4">
                <div class="bg-cream p-4">
                  <p class="section-label text-muted mb-2">Buyer</p>
                  <div class="flex items-center gap-2">
                    <div class="w-8 h-8 bg-accent/20 text-accent font-display font-bold text-xs flex items-center justify-center">
                      {{ dispute.buyerName.charAt(0) }}
                    </div>
                    <div>
                      <p class="font-display font-semibold text-sm">{{ dispute.buyerName }}</p>
                      <p class="text-xs text-muted font-mono">Filed the dispute</p>
                    </div>
                  </div>
                </div>
                <div class="bg-cream p-4">
                  <p class="section-label text-muted mb-2">Seller</p>
                  <div class="flex items-center gap-2">
                    <div class="w-8 h-8 bg-cream text-white font-display font-bold text-xs flex items-center justify-center">
                      {{ dispute.sellerName.charAt(0) }}
                    </div>
                    <div>
                      <p class="font-display font-semibold text-sm">{{ dispute.sellerName }}</p>
                      <p class="text-xs text-muted font-mono">Responding party</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Buyer's claim -->
            <div class="bg-cream border border-ink/10 p-5">
              <p class="section-label text-muted mb-3">Buyer's Claim</p>
              <div class="bg-accent/10 border border-accent/20 px-3 py-1.5 inline-block mb-3">
                <p class="text-xs font-mono text-accent uppercase tracking-wider">{{ dispute.reason.replace(/_/g, ' ') }}</p>
              </div>
              <p class="text-ink text-sm leading-relaxed">{{ dispute.description }}</p>
            </div>

            <!-- Seller's response -->
            <div class="bg-cream border border-ink/10 p-5">
              <p class="section-label text-muted mb-3">Seller's Response</p>
              <div v-if="dispute.sellerResponse">
                <p class="text-ink text-sm leading-relaxed">{{ dispute.sellerResponse }}</p>
              </div>
              <div v-else class="flex items-center gap-2 text-amber-400">
                <span class="text-sm">⏱</span>
                <p class="text-sm font-mono">Awaiting response — deadline {{ dispute.deadline }}</p>
              </div>
            </div>

            <!-- Evidence files -->
            <div class="bg-cream border border-ink/10 p-5">
              <p class="section-label text-muted mb-4">Evidence Submitted ({{ dispute.evidence.length }} files)</p>
              <div class="grid grid-cols-2 gap-3">
                <div
                  v-for="file in dispute.evidence"
                  :key="file"
                  class="bg-cream border border-ink/10 p-3 flex items-center gap-2 hover:border-accent/30 transition-colors cursor-pointer"
                >
                  <span class="text-lg">{{ fileIcon(file) }}</span>
                  <div class="min-w-0">
                    <p class="font-mono text-xs text-ink truncate">{{ file }}</p>
                    <p class="font-mono text-xs text-muted">Evidence file</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Sidebar: Decision panel -->
          <div class="lg:col-span-1">
            <div class="bg-cream border border-ink/10 p-5 sticky top-24">
              <p class="section-label text-muted mb-4">Admin Decision</p>

              <!-- Already decided -->
              <div v-if="dispute.status !== 'PENDING'">
                <div
                  class="p-4 text-center mb-4"
                  :class="dispute.status === 'APPROVED' ? 'bg-sage/10 border border-sage/20' : 'bg-red-500/10 border border-red-500/20'"
                >
                  <span class="text-2xl">{{ dispute.status === 'APPROVED' ? '✓' : '✕' }}</span>
                  <p class="font-display font-bold text-sm mt-2"
                    :class="dispute.status === 'APPROVED' ? 'text-sage' : 'text-red-400'"
                  >Dispute {{ dispute.status }}</p>
                  <p class="text-xs text-muted font-mono mt-1">
                    {{ dispute.status === 'APPROVED' ? 'Buyer will be refunded' : 'Funds released to seller' }}
                  </p>
                </div>
                <button @click="resetStatus" class="btn-ghost text-muted text-xs w-full">Reset for demo</button>
              </div>

              <!-- Decision form -->
              <div v-else>
                <div class="space-y-3 mb-5">
                  <div class="bg-cream p-3 text-xs font-mono space-y-1.5">
                    <div class="flex justify-between">
                      <span class="text-muted">Amount at stake</span>
                      <span class="text-accent font-medium">${{ dispute.amount }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-muted">Evidence files</span>
                      <span class="text-ink">{{ dispute.evidence.length }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-muted">Seller responded</span>
                      <span :class="dispute.sellerResponse ? 'text-sage' : 'text-amber-400'">
                        {{ dispute.sellerResponse ? 'Yes' : 'No' }}
                      </span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-muted">Deadline</span>
                      <span class="text-ink">{{ dispute.deadline }}</span>
                    </div>
                  </div>
                </div>

                <div class="mb-4">
                  <label class="section-label text-muted block mb-2">Admin Notes (optional)</label>
                  <textarea
                    v-model="adminNotes"
                    class="input-field bg-cream border-ink/10 text-paper placeholder:text-muted resize-none text-sm"
                    rows="3"
                    placeholder="Reason for decision..."
                  ></textarea>
                </div>

                <!-- Approve -->
                <button
                  @click="decide('APPROVED')"
                  class="w-full bg-sage text-ink font-display font-bold px-4 py-3 hover:bg-sage/80 transition-colors text-sm tracking-wide uppercase mb-2"
                  :disabled="deciding"
                >
                  <span v-if="deciding && decision === 'APPROVED'">Processing...</span>
                  <span v-else>✓ Approve — Refund Buyer</span>
                </button>

                <!-- Reject -->
                <button
                  @click="decide('REJECTED')"
                  class="w-full bg-red-600 text-white font-display font-bold px-4 py-3 hover:bg-red-700 transition-colors text-sm tracking-wide uppercase"
                  :disabled="deciding"
                >
                  <span v-if="deciding && decision === 'REJECTED'">Processing...</span>
                  <span v-else>✕ Reject — Release to Seller</span>
                </button>

                <p class="text-xs text-muted font-mono text-center mt-3 leading-relaxed">
                  Approving will trigger a full refund to the buyer.<br/>
                  Rejecting will release funds to the seller.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Decision confirmation modal -->
  <div v-if="confirmed" class="fixed inset-0 bg-ink/80 flex items-center justify-center z-50 p-6">
    <div class="bg-paper max-w-sm w-full p-8 text-center">
      <div
        class="w-16 h-16 flex items-center justify-center mx-auto mb-4 text-3xl"
        :class="lastDecision === 'APPROVED' ? 'bg-sage/20' : 'bg-red-100'"
      >{{ lastDecision === 'APPROVED' ? '✓' : '✕' }}</div>
      <h2 class="font-display font-extrabold text-2xl mb-2 text-ink">
        Dispute {{ lastDecision === 'APPROVED' ? 'Approved' : 'Rejected' }}
      </h2>
      <p class="text-slate text-sm mb-6 leading-relaxed">
        <span v-if="lastDecision === 'APPROVED'">
          The buyer will be refunded ${{ dispute?.amount }}. The escrow funds have been released back.
        </span>
        <span v-else>
          The dispute has been rejected. ${{ dispute?.amount }} will be released to the seller.
        </span>
      </p>
      <button @click="$router.push('/admin/disputes')" class="btn-primary w-full">Back to Disputes</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AdminNavbar from '../../components/AdminNavbar.vue'
import { mockDisputes } from '../../data/mockData.js'

const route = useRoute()
const router = useRouter()

const disputes = ref([...mockDisputes])
const dispute = computed(() => disputes.value.find(d => d.id === route.params.id))

const adminNotes = ref('')
const deciding = ref(false)
const decision = ref('')
const confirmed = ref(false)
const lastDecision = ref('')

const statusBadgeClass = computed(() => ({
  PENDING:  'bg-amber-400/20 text-amber-400',
  APPROVED: 'bg-sage/20 text-sage',
  REJECTED: 'bg-red-500/20 text-red-400',
}[dispute.value?.status] || 'bg-cream text-slate'))

function fileIcon(name) {
  if (name.match(/\.(jpg|jpeg|png|gif|webp)$/i)) return '🖼'
  if (name.match(/\.(mp4|mov|avi)$/i)) return '🎥'
  if (name.match(/\.pdf$/i)) return '📄'
  return '📎'
}

async function decide(outcome) {
  decision.value = outcome
  deciding.value = true
  await new Promise(r => setTimeout(r, 1200))

  const idx = disputes.value.findIndex(d => d.id === route.params.id)
  if (idx !== -1) disputes.value[idx] = { ...disputes.value[idx], status: outcome }

  deciding.value = false
  lastDecision.value = outcome
  confirmed.value = true
}

function resetStatus() {
  const idx = disputes.value.findIndex(d => d.id === route.params.id)
  if (idx !== -1) disputes.value[idx] = { ...disputes.value[idx], status: 'PENDING' }
}
</script>
