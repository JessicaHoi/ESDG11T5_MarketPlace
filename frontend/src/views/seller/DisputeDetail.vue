<template>
  <div class="min-h-screen bg-paper text-ink">
    <SellerNavbar :seller="mockSeller" />

    <div class="pt-16">
      <!-- Back -->
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
                  <p class="section-label text-muted mb-2">Seller (You)</p>
                  <div class="flex items-center gap-2">
                    <div class="w-8 h-8 bg-accent text-paper font-display font-bold text-xs flex items-center justify-center">
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

            <!-- Your response -->
            <div class="bg-cream border border-ink/10 p-5">
              <p class="section-label text-muted mb-3">Your Response</p>
              <div v-if="dispute.sellerResponse && !editing">
                <p class="text-ink text-sm leading-relaxed mb-3">{{ dispute.sellerResponse }}</p>
                <button
                  v-if="dispute.status === 'PENDING'"
                  @click="editing = true"
                  class="text-xs font-mono text-accent hover:underline"
                >Edit response</button>
              </div>
              <div v-else-if="dispute.status === 'PENDING'">
                <textarea
                  v-model="responseText"
                  class="input-field resize-none text-sm"
                  rows="4"
                  placeholder="Explain your side of the dispute. Provide details about the transaction, item condition, and any relevant context..."
                ></textarea>
                <div class="flex items-center justify-between mt-3">
                  <p class="text-xs text-muted font-mono">{{ responseText.length }}/500</p>
                  <div class="flex gap-2">
                    <button
                      v-if="dispute.sellerResponse"
                      @click="editing = false"
                      class="btn-ghost text-xs px-3 py-1.5"
                    >Cancel</button>
                    <button
                      @click="submitResponse"
                      :disabled="!responseText.trim() || submitting"
                      class="bg-ink text-paper font-display font-semibold px-4 py-2 text-xs hover:bg-slate transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >{{ submitting ? 'Submitting...' : 'Submit Response' }}</button>
                  </div>
                </div>
              </div>
              <div v-else class="flex items-center gap-2 text-muted">
                <span class="text-sm">—</span>
                <p class="text-sm font-mono">No response was submitted</p>
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

          <!-- Sidebar -->
          <div class="lg:col-span-1">
            <div class="bg-cream border border-ink/10 p-5 sticky top-24">
              <p class="section-label text-muted mb-4">Dispute Summary</p>

              <div class="space-y-3 mb-5">
                <div class="bg-cream p-3 text-xs font-mono space-y-1.5">
                  <div class="flex justify-between">
                    <span class="text-muted">Status</span>
                    <span :class="{
                      'text-amber-400': dispute.status === 'PENDING',
                      'text-sage': dispute.status === 'APPROVED',
                      'text-red-400': dispute.status === 'REJECTED',
                    }">{{ dispute.status }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-muted">Amount at stake</span>
                    <span class="text-accent font-medium">${{ dispute.amount }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-muted">Evidence files</span>
                    <span class="text-ink">{{ dispute.evidence.length }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-muted">Your response</span>
                    <span :class="dispute.sellerResponse ? 'text-sage' : 'text-amber-400'">
                      {{ dispute.sellerResponse ? 'Submitted' : 'Pending' }}
                    </span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-muted">Deadline</span>
                    <span class="text-ink">{{ dispute.deadline }}</span>
                  </div>
                </div>
              </div>

              <!-- Status-specific info -->
              <div v-if="dispute.status === 'PENDING'" class="bg-amber-50 border border-amber-200 p-3 text-xs text-amber-700 font-mono leading-relaxed">
                ⏳ This dispute is under review. Submit your response before the deadline to present your side.
              </div>
              <div v-else-if="dispute.status === 'APPROVED'" class="bg-sage/10 border border-sage/20 p-3 text-xs text-sage font-mono leading-relaxed">
                ✓ Dispute approved — buyer will be refunded ${{ dispute.amount }}.
              </div>
              <div v-else-if="dispute.status === 'REJECTED'" class="bg-red-50 border border-red-200 p-3 text-xs text-red-600 font-mono leading-relaxed">
                ✕ Dispute rejected — funds will be released to you.
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="text-center py-32">
        <p class="font-display text-2xl text-muted">Dispute not found.</p>
        <router-link to="/seller/disputes" class="btn-ghost mt-4 inline-block">Back to disputes</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import SellerNavbar from '../../components/SellerNavbar.vue'
import { mockDisputes, mockSeller } from '../../data/mockData.js'
import { getMergedDisputes, updateSellerResponse } from '../../data/disputeStore.js'

const route = useRoute()

const disputes = ref([])
const editing = ref(false)
const responseText = ref('')
const submitting = ref(false)

onMounted(() => {
  disputes.value = getMergedDisputes(mockDisputes)
})

const dispute = computed(() => disputes.value.find(d => d.id === route.params.id))

// Pre-fill response text if one exists
onMounted(() => {
  if (dispute.value?.sellerResponse) {
    responseText.value = dispute.value.sellerResponse
  }
})

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

async function submitResponse() {
  if (!responseText.value.trim()) return
  submitting.value = true
  await new Promise(r => setTimeout(r, 800))

  // Persist to localStorage via disputeStore
  updateSellerResponse(route.params.id, responseText.value.trim(), mockDisputes)

  // Update reactive state
  const idx = disputes.value.findIndex(d => d.id === route.params.id)
  if (idx !== -1) {
    disputes.value[idx] = { ...disputes.value[idx], sellerResponse: responseText.value.trim() }
  }

  editing.value = false
  submitting.value = false
}
</script>
