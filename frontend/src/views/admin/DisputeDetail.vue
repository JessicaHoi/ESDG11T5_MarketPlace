<template>
  <div class="min-h-screen bg-paper text-ink">
    <AdminNavbar />

    <div class="pt-16">
      <div class="max-w-4xl mx-auto px-6 pt-8">
        <button @click="$router.push('/admin/disputes')" class="section-label text-muted hover:text-accent transition-colors">← All Disputes</button>
      </div>

      <div v-if="loading" class="text-center py-20 text-muted font-mono text-sm">Loading dispute...</div>

      <div v-else-if="dispute" class="max-w-4xl mx-auto px-6 py-6">

        <!-- Header -->
        <div class="flex items-start justify-between flex-wrap gap-4 mb-8">
          <div>
            <div class="flex items-center gap-3 mb-2">
              <span class="font-mono font-medium text-sm text-slate">DIS-{{ dispute.disputeID }}</span>
              <span class="inline-flex items-center px-2.5 py-0.5 text-xs font-mono font-medium uppercase tracking-wider" :class="statusBadgeClass">{{ dispute.disputeStatus }}</span>
            </div>
            <h1 class="font-display font-extrabold text-3xl">{{ dispute.listingTitle || 'Dispute' }}</h1>
            <p class="text-muted font-mono text-sm mt-1">Order #{{ dispute.orderID }} · Filed {{ formatDate(dispute.createdAt) }}</p>
          </div>
          <div class="text-right">
            <p class="font-display font-extrabold text-3xl text-accent">${{ dispute.amount || 0 }}</p>
            <p class="text-muted font-mono text-xs mt-1">Funds currently frozen</p>
          </div>
        </div>

        <!-- Countdown timer -->
        <div v-if="dispute.deadlineAt && !isResolved" class="mb-6 border p-4 flex items-center gap-3"
          :class="timerExpired ? 'border-red-300 bg-red-50' : 'border-amber-200 bg-amber-50'">
          <span class="text-xl">⏱</span>
          <div class="flex-1">
            <p class="font-display font-semibold text-sm" :class="timerExpired ? 'text-red-800' : 'text-amber-800'">
              {{ timerExpired ? 'Deadline expired' : 'Time remaining' }}
            </p>
            <p class="font-mono text-lg font-bold" :class="timerExpired ? 'text-red-600' : 'text-amber-600'">{{ timerDisplay }}</p>
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
                    <div class="w-8 h-8 bg-accent/20 text-accent font-display font-bold text-xs flex items-center justify-center">B</div>
                    <div>
                      <p class="font-display font-semibold text-sm">Buyer #{{ dispute.buyerID }}</p>
                      <p class="text-xs text-muted font-mono">Filed the dispute</p>
                    </div>
                  </div>
                </div>
                <div class="bg-cream p-4">
                  <p class="section-label text-muted mb-2">Seller</p>
                  <div class="flex items-center gap-2">
                    <div class="w-8 h-8 bg-ink text-paper font-display font-bold text-xs flex items-center justify-center">S</div>
                    <div>
                      <p class="font-display font-semibold text-sm">Seller #{{ dispute.sellerID }}</p>
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
                <p class="text-xs font-mono text-accent uppercase tracking-wider">{{ (dispute.disputeReason || '').replace(/_/g, ' ') }}</p>
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
                <p class="text-sm font-mono">Awaiting response — deadline {{ formatDate(dispute.deadlineAt) }}</p>
              </div>
            </div>

            <!-- Evidence files -->
            <div class="bg-cream border border-ink/10 p-5">
              <p class="section-label text-muted mb-4">Evidence Submitted ({{ evidenceFiles.length }} files)</p>
              <div v-if="evidenceFiles.length === 0" class="text-muted font-mono text-sm">No evidence files found.</div>
              <div v-else class="grid grid-cols-2 gap-3">
                <div
                  v-for="(ev, i) in evidenceFiles"
                  :key="ev.evidenceID"
                  class="bg-white border border-ink/10 overflow-hidden hover:border-accent/30 transition-colors cursor-pointer"
                  @click="openLightbox(i)"
                >
                  <div v-if="isImage(ev.fileType)" class="aspect-square bg-cream">
                    <img :src="ev.fileURL" :alt="ev.fileName" class="w-full h-full object-cover" />
                  </div>
                  <div v-else class="aspect-square bg-cream flex items-center justify-center text-3xl">
                    {{ fileIcon(ev.fileName || ev.fileType) }}
                  </div>
                  <div class="p-2">
                    <p class="font-mono text-xs text-ink truncate">{{ ev.fileName || `Evidence #${ev.evidenceID}` }}</p>
                    <p class="font-mono text-xs text-muted">{{ ev.fileType }}</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Conversation thread -->
            <div class="bg-cream border border-ink/10 p-5">
              <p class="section-label text-muted mb-4">Dispute Conversation</p>
              <div class="max-h-64 overflow-y-auto space-y-3 mb-4" ref="threadContainer">
                <div v-if="threadMessages.length === 0" class="text-center text-muted font-mono text-sm py-4">No messages yet.</div>
                <div v-for="msg in threadMessages" :key="msg.messageID || msg.id" class="flex" :class="getThreadAlign(msg)">
                  <div class="max-w-[80%] px-3 py-2 text-sm" :class="getThreadBubble(msg)">
                    <p class="font-mono text-xs text-muted mb-1">{{ getThreadSender(msg) }}</p>
                    <p>{{ msg.content }}</p>
                    <p class="font-mono text-xs text-muted mt-1">{{ formatTime(msg.sentAt) }}</p>
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
              <div v-if="isResolved">
                <div class="p-4 text-center mb-4"
                  :class="dispute.disputeStatus === 'APPROVED' ? 'bg-sage/10 border border-sage/20' : 'bg-red-500/10 border border-red-500/20'">
                  <span class="text-2xl">{{ dispute.disputeStatus === 'APPROVED' ? '✓' : '✕' }}</span>
                  <p class="font-display font-bold text-sm mt-2"
                    :class="dispute.disputeStatus === 'APPROVED' ? 'text-sage' : 'text-red-400'">
                    Dispute {{ dispute.disputeStatus }}
                  </p>
                  <p class="text-xs text-muted font-mono mt-1">
                    {{ dispute.disputeStatus === 'APPROVED' ? 'Buyer has been refunded' : 'Funds released to seller' }}
                  </p>
                </div>
              </div>

              <!-- Waiting for seller agreement -->
              <div v-else-if="dispute.disputeStatus !== 'AWAITING_DECISION' && dispute.disputeStatus !== 'OPEN'">
                <div class="bg-amber-50 border border-amber-200 p-4 mb-4">
                  <p class="text-amber-800 text-sm font-display font-semibold">⏳ Waiting for seller agreement</p>
                  <p class="text-amber-700 text-xs mt-1">Decision buttons will appear after the seller submits agreement.</p>
                </div>
                <div class="bg-cream p-3 text-xs font-mono space-y-1.5">
                  <div class="flex justify-between">
                    <span class="text-muted">Amount at stake</span>
                    <span class="text-accent font-medium">${{ dispute.amount }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-muted">Evidence files</span>
                    <span class="text-ink">{{ evidenceFiles.length }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-muted">Seller responded</span>
                    <span :class="dispute.sellerResponse ? 'text-sage' : 'text-amber-400'">{{ dispute.sellerResponse ? 'Yes' : 'No' }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-muted">Deadline</span>
                    <span class="text-ink">{{ formatDate(dispute.deadlineAt) }}</span>
                  </div>
                </div>
              </div>

              <!-- Decision form (AWAITING_DECISION or OPEN) -->
              <div v-else>
                <div class="space-y-3 mb-5">
                  <div class="bg-cream p-3 text-xs font-mono space-y-1.5">
                    <div class="flex justify-between">
                      <span class="text-muted">Amount at stake</span>
                      <span class="text-accent font-medium">${{ dispute.amount }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-muted">Evidence files</span>
                      <span class="text-ink">{{ evidenceFiles.length }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-muted">Seller responded</span>
                      <span :class="dispute.sellerResponse ? 'text-sage' : 'text-amber-400'">{{ dispute.sellerResponse ? 'Yes' : 'No' }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-muted">Deadline</span>
                      <span class="text-ink">{{ formatDate(dispute.deadlineAt) }}</span>
                    </div>
                  </div>
                </div>

                <div class="mb-4">
                  <label class="section-label text-muted block mb-2">Admin Notes (optional)</label>
                  <textarea v-model="adminNotes" class="input-field resize-none text-sm" rows="3" placeholder="Reason for decision..."></textarea>
                </div>

                <button
                  @click="decide('APPROVED')"
                  class="w-full bg-sage text-ink font-display font-bold px-4 py-3 hover:bg-sage/80 transition-colors text-sm tracking-wide uppercase mb-2"
                  :disabled="deciding"
                >
                  <span v-if="deciding && decision === 'APPROVED'">Processing...</span>
                  <span v-else>✓ Approve — Refund Buyer</span>
                </button>

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

      <div v-else class="text-center py-20 text-muted font-mono text-sm">Dispute not found.</div>
    </div>
  </div>

  <!-- Evidence lightbox -->
  <div v-if="lightboxOpen" class="fixed inset-0 bg-ink/90 flex items-center justify-center z-50 p-6" @click.self="lightboxOpen = false">
    <button @click="lightboxOpen = false" class="absolute top-6 right-6 text-white text-2xl hover:text-accent">✕</button>
    <button v-if="lightboxIndex > 0" @click="lightboxIndex--" class="absolute left-6 text-white text-3xl hover:text-accent">‹</button>
    <button v-if="lightboxIndex < evidenceFiles.length - 1" @click="lightboxIndex++" class="absolute right-6 text-white text-3xl hover:text-accent">›</button>
    <div class="max-w-4xl max-h-[80vh] flex flex-col items-center">
      <img v-if="isImage(currentLightboxFile?.fileType)" :src="currentLightboxFile?.fileURL" class="max-w-full max-h-[70vh] object-contain" />
      <div v-else class="bg-paper p-12 text-center">
        <p class="text-5xl mb-4">{{ fileIcon(currentLightboxFile?.fileName) }}</p>
        <p class="font-display font-semibold">{{ currentLightboxFile?.fileName }}</p>
      </div>
      <p class="text-white font-mono text-sm mt-4">{{ currentLightboxFile?.fileName }} · {{ lightboxIndex + 1 }}/{{ evidenceFiles.length }}</p>
    </div>
  </div>

  <!-- Decision confirmation modal -->
  <div v-if="confirmed" class="fixed inset-0 bg-ink/80 flex items-center justify-center z-50 p-6">
    <div class="bg-paper max-w-sm w-full p-8 text-center">
      <div class="w-16 h-16 flex items-center justify-center mx-auto mb-4 text-3xl"
        :class="lastDecision === 'APPROVED' ? 'bg-sage/20' : 'bg-red-100'">{{ lastDecision === 'APPROVED' ? '✓' : '✕' }}</div>
      <h2 class="font-display font-extrabold text-2xl mb-2 text-ink">
        Dispute {{ lastDecision === 'APPROVED' ? 'Approved' : 'Rejected' }}
      </h2>
      <p class="text-slate text-sm mb-6 leading-relaxed">
        <span v-if="lastDecision === 'APPROVED'">The buyer will be refunded ${{ dispute?.amount }}. The escrow funds have been released back.</span>
        <span v-else>The dispute has been rejected. ${{ dispute?.amount }} will be released to the seller.</span>
      </p>
      <button @click="$router.push('/admin/disputes')" class="btn-primary w-full">Back to Disputes</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import AdminNavbar from '../../components/AdminNavbar.vue'
import {
  getDispute, getEvidenceByDispute, getDisputeMessages,
  resolveDispute, rejectDispute,
} from '../../services/api.js'

const route = useRoute()
const disputeID = parseInt(route.params.id)

const dispute       = ref(null)
const evidenceFiles = ref([])
const threadMessages = ref([])
const loading       = ref(true)
const adminNotes    = ref('')
const deciding      = ref(false)
const decision      = ref('')
const confirmed     = ref(false)
const lastDecision  = ref('')

// Lightbox
const lightboxOpen  = ref(false)
const lightboxIndex = ref(0)
const currentLightboxFile = computed(() => evidenceFiles.value[lightboxIndex.value])

// Timer
const timerDisplay = ref('--:--:--')
const timerExpired = ref(false)
let timerHandle = null

const isResolved = computed(() => ['APPROVED', 'REJECTED'].includes(dispute.value?.disputeStatus))

const statusBadgeClass = computed(() => ({
  OPEN: 'bg-amber-100 text-amber-700', RESPONSE: 'bg-blue-100 text-blue-700',
  AWAITING_DECISION: 'bg-purple-100 text-purple-700',
  APPROVED: 'bg-sage/20 text-sage', REJECTED: 'bg-red-100 text-red-600',
}[dispute.value?.disputeStatus] || 'bg-cream text-slate'))

onMounted(async () => {
  try {
    const [disputeRes, evidenceRes] = await Promise.all([
      getDispute(disputeID),
      getEvidenceByDispute(disputeID).catch(() => ({ data: [] })),
    ])

    dispute.value = disputeRes?.data ?? null
    evidenceFiles.value = evidenceRes?.data ?? []

    // Load conversation thread via RaiseDispute composite
    try {
      const msgs = await getDisputeMessages(disputeID)
      threadMessages.value = Array.isArray(msgs) ? msgs : []
    } catch { threadMessages.value = [] }

    startTimer()
  } catch (err) {
    console.error('Failed to load dispute:', err)
  } finally {
    loading.value = false
  }
})

onUnmounted(() => { if (timerHandle) clearInterval(timerHandle) })

function startTimer() {
  if (!dispute.value?.deadlineAt) return
  const update = () => {
    // Append 'Z' if missing so JS parses it as UTC, not local time
    const deadlineStr = dispute.value.deadlineAt.includes('T')
      ? dispute.value.deadlineAt.endsWith('Z') ? dispute.value.deadlineAt : dispute.value.deadlineAt + 'Z'
      : dispute.value.deadlineAt.replace(' ', 'T') + 'Z'
    const diff = new Date(deadlineStr) - new Date()
    if (diff <= 0) {
      timerExpired.value = true
      timerDisplay.value = '00:00:00'
      clearInterval(timerHandle)
    } else {
      const h = Math.floor(diff / 3600000)
      const m = Math.floor((diff % 3600000) / 60000)
      const s = Math.floor((diff % 60000) / 1000)
      timerDisplay.value = `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`
    }
  }
  update()
  timerHandle = setInterval(update, 1000)
}

function openLightbox(index) {
  lightboxIndex.value = index
  lightboxOpen.value = true
}

function isImage(type) {
  return type && (type.startsWith('image/') || /\.(jpg|jpeg|png|gif|webp)$/i.test(type))
}

function fileIcon(name) {
  if (!name) return '📎'
  if (name.match(/\.(jpg|jpeg|png|gif|webp)$/i) || name.startsWith('image/')) return '🖼'
  if (name.match(/\.(mp4|mov|avi)$/i) || name.startsWith('video/')) return '🎥'
  if (name.match(/\.pdf$/i) || name === 'application/pdf') return '📄'
  return '📎'
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-SG', { day: 'numeric', month: 'short', year: 'numeric' })
}

function formatTime(t) {
  if (!t) return ''
  return new Date(t).toLocaleTimeString('en-SG', { hour: '2-digit', minute: '2-digit' })
}

function getThreadAlign(msg) {
  if (msg.senderID === dispute.value?.buyerID) return 'justify-start'
  if (msg.senderID === dispute.value?.sellerID) return 'justify-end'
  return 'justify-center'
}

function getThreadBubble(msg) {
  if (msg.senderID === dispute.value?.buyerID) return 'bg-white border border-ink/10'
  if (msg.senderID === dispute.value?.sellerID) return 'bg-accent/10 border border-accent/20'
  return 'bg-cream border border-ink/10'
}

function getThreadSender(msg) {
  if (msg.senderID === dispute.value?.buyerID) return `Buyer #${msg.senderID}`
  if (msg.senderID === dispute.value?.sellerID) return `Seller #${msg.senderID}`
  return `User #${msg.senderID}`
}

async function decide(outcome) {
  decision.value = outcome
  deciding.value = true
  try {
    if (outcome === 'APPROVED') {
      await resolveDispute(disputeID, dispute.value.orderID)
    } else {
      await rejectDispute(disputeID, dispute.value.orderID)
    }
    dispute.value.disputeStatus = outcome
    lastDecision.value = outcome
    confirmed.value = true
  } catch (err) {
    console.error('Decision failed:', err)
    alert('Decision failed: ' + err.message)
  } finally {
    deciding.value = false
  }
}
</script>