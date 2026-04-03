<template>
  <div class="min-h-screen bg-paper">
    <SellerNavbar :seller="mockSeller" />

    <div class="pt-16">
      <div class="max-w-4xl mx-auto px-6 pt-8">
        <router-link to="/seller/disputes" class="section-label text-muted hover:text-accent transition-colors">← All Disputes</router-link>
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

        <!-- Timer -->
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
          <div class="lg:col-span-2 space-y-5">
            <!-- Parties -->
            <div class="bg-cream border border-ink/10 p-5">
              <p class="section-label text-muted mb-4">Involved Parties</p>
              <div class="grid grid-cols-2 gap-4">
                <div class="bg-cream p-4">
                  <p class="section-label text-muted mb-2">Buyer</p>
                  <div class="flex items-center gap-2">
                    <div class="w-8 h-8 bg-accent/20 text-accent font-display font-bold text-xs flex items-center justify-center">B</div>
                    <div><p class="font-display font-semibold text-sm">Buyer #{{ dispute.buyerID }}</p><p class="text-xs text-muted font-mono">Filed the dispute</p></div>
                  </div>
                </div>
                <div class="bg-cream p-4">
                  <p class="section-label text-muted mb-2">Seller (You)</p>
                  <div class="flex items-center gap-2">
                    <div class="w-8 h-8 bg-sage text-white font-display font-bold text-xs flex items-center justify-center">{{ mockSeller.name.charAt(0) }}</div>
                    <div><p class="font-display font-semibold text-sm">{{ mockSeller.name }}</p><p class="text-xs text-muted font-mono">Responding party</p></div>
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

            <!-- Evidence -->
            <div class="bg-cream border border-ink/10 p-5">
              <p class="section-label text-muted mb-4">Evidence ({{ evidenceFiles.length }} files)</p>
              <div v-if="evidenceFiles.length === 0" class="text-muted font-mono text-sm">No evidence.</div>
              <div v-else class="grid grid-cols-2 gap-3">
                <div v-for="(ev, i) in evidenceFiles" :key="ev.evidenceID"
                  class="bg-white border border-ink/10 overflow-hidden hover:border-accent/30 transition-colors cursor-pointer" @click="openLightbox(i)">
                  <div v-if="isImage(ev.fileType)" class="aspect-square bg-cream"><img :src="ev.fileURL" class="w-full h-full object-cover" /></div>
                  <div v-else class="aspect-square bg-cream flex items-center justify-center text-3xl">{{ fileIcon(ev.fileName) }}</div>
                  <div class="p-2"><p class="font-mono text-xs text-ink truncate">{{ ev.fileName || `Evidence #${ev.evidenceID}` }}</p></div>
                </div>
              </div>
            </div>

            <!-- Conversation thread -->
            <div class="bg-cream border border-ink/10 p-5">
              <p class="section-label text-muted mb-4">Dispute Conversation</p>
              <div class="max-h-64 overflow-y-auto space-y-3 mb-4" ref="threadContainer">
                <div v-if="threadMessages.length === 0" class="text-center text-muted font-mono text-sm py-4">No messages yet.</div>
                <div v-for="msg in threadMessages" :key="msg.messageID || msg.id" class="flex"
                  :class="msg.senderID === mockSeller.id ? 'justify-end' : 'justify-start'">
                  <div class="max-w-[80%] px-3 py-2 text-sm"
                    :class="msg.senderID === mockSeller.id ? 'bg-accent/10 border border-accent/20' : 'bg-white border border-ink/10'">
                    <p class="font-mono text-xs text-muted mb-1">{{ msg.senderID === mockSeller.id ? 'You' : `Buyer #${msg.senderID}` }}</p>
                    <p>{{ msg.content }}</p>
                    <p class="font-mono text-xs text-muted mt-1">{{ formatTime(msg.sentAt) }}</p>
                  </div>
                </div>
              </div>
              <!-- Send message -->
              <div v-if="!isResolved" class="flex gap-2">
                <input v-model="newThreadMsg" type="text" class="input-field flex-1" placeholder="Reply to buyer..." @keyup.enter="sendThreadMessage" />
                <button @click="sendThreadMessage" class="btn-primary px-4" :disabled="!newThreadMsg.trim()">Send</button>
              </div>
            </div>

            <!-- Your response form -->
            <div v-if="!isResolved" class="bg-cream border border-ink/10 p-5">
              <p class="section-label text-muted mb-3">Your Response</p>
              <div v-if="dispute.sellerResponse" class="mb-4">
                <p class="text-ink text-sm leading-relaxed bg-sage/10 border border-sage/20 p-3">{{ dispute.sellerResponse }}</p>
                <p class="text-xs text-sage font-mono mt-2">✓ Response submitted</p>
              </div>
              <div v-else>
                <textarea v-model="responseText" class="input-field resize-none" rows="4" placeholder="Explain your side of the story..."></textarea>
                <button @click="submitResponse" class="btn-primary mt-3" :disabled="!responseText.trim() || submittingResponse">
                  {{ submittingResponse ? 'Submitting...' : 'Submit Response' }}
                </button>
              </div>
            </div>
          </div>

          <!-- Sidebar -->
          <div class="lg:col-span-1">
            <div class="bg-cream border border-ink/10 p-5 sticky top-24">
              <p class="section-label text-muted mb-4">Dispute Summary</p>
              <div class="bg-cream p-3 text-xs font-mono space-y-1.5 mb-4">
                <div class="flex justify-between"><span class="text-muted">Status</span><span :class="statusBadgeClass">{{ dispute.disputeStatus }}</span></div>
                <div class="flex justify-between"><span class="text-muted">Amount at stake</span><span class="text-accent font-medium">${{ dispute.amount }}</span></div>
                <div class="flex justify-between"><span class="text-muted">Evidence files</span><span class="text-ink">{{ evidenceFiles.length }}</span></div>
                <div class="flex justify-between"><span class="text-muted">Your response</span><span :class="dispute.sellerResponse ? 'text-sage' : 'text-amber-400'">{{ dispute.sellerResponse ? 'Submitted' : 'Pending' }}</span></div>
                <div class="flex justify-between"><span class="text-muted">Deadline</span><span class="text-ink">{{ formatDate(dispute.deadlineAt) }}</span></div>
              </div>

              <!-- Agreement button -->
              <div v-if="dispute.sellerResponse && dispute.disputeStatus === 'RESPONSE' && !isResolved">
                <button @click="handleSellerAgree" class="w-full bg-sage text-white font-display font-bold px-4 py-3 hover:bg-sage/80 transition-colors text-sm tracking-wide uppercase"
                  :disabled="agreeing">
                  {{ agreeing ? 'Processing...' : '🤝 Agreement Received' }}
                </button>
                <p class="text-xs text-muted font-mono text-center mt-2">This will notify the admin to make a final decision.</p>
              </div>

              <div v-if="isResolved" class="p-4 text-center"
                :class="dispute.disputeStatus === 'APPROVED' ? 'bg-sage/10 border border-sage/20' : 'bg-red-500/10 border border-red-500/20'">
                <span class="text-2xl">{{ dispute.disputeStatus === 'APPROVED' ? '✓' : '✕' }}</span>
                <p class="font-display font-bold text-sm mt-2" :class="dispute.disputeStatus === 'APPROVED' ? 'text-sage' : 'text-red-400'">
                  Dispute {{ dispute.disputeStatus }}
                </p>
              </div>

              <div v-if="!isResolved" class="mt-4 border border-amber-200 bg-amber-50 p-3">
                <p class="text-xs text-amber-700 leading-relaxed">⏱ This dispute is under review. Submit your response before the deadline to present your side.</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="text-center py-20 text-muted font-mono text-sm">Dispute not found.</div>
    </div>
  </div>

  <!-- Lightbox -->
  <div v-if="lightboxOpen" class="fixed inset-0 bg-ink/90 flex items-center justify-center z-50 p-6" @click.self="lightboxOpen = false">
    <button @click="lightboxOpen = false" class="absolute top-6 right-6 text-white text-2xl hover:text-accent">✕</button>
    <button v-if="lightboxIndex > 0" @click="lightboxIndex--" class="absolute left-6 text-white text-3xl hover:text-accent">‹</button>
    <button v-if="lightboxIndex < evidenceFiles.length - 1" @click="lightboxIndex++" class="absolute right-6 text-white text-3xl hover:text-accent">›</button>
    <div class="max-w-4xl max-h-[80vh]">
      <img v-if="isImage(currentLightboxFile?.fileType)" :src="currentLightboxFile?.fileURL" class="max-w-full max-h-[70vh] object-contain" />
      <div v-else class="bg-paper p-12 text-center"><p class="text-5xl mb-4">{{ fileIcon(currentLightboxFile?.fileName) }}</p><p class="font-display font-semibold">{{ currentLightboxFile?.fileName }}</p></div>
      <p class="text-white font-mono text-sm mt-4 text-center">{{ currentLightboxFile?.fileName }} · {{ lightboxIndex + 1 }}/{{ evidenceFiles.length }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import SellerNavbar from '../../components/SellerNavbar.vue'
import { mockSeller } from '../../data/mockData.js'
import {
  getDispute, getEvidenceByDispute, getMessagesByOrder, sendMessage,
  submitSellerResponse, sellerAgreeDispute,
} from '../../services/api.js'

const route = useRoute()
const disputeID = parseInt(route.params.id)

const dispute = ref(null)
const evidenceFiles = ref([])
const threadMessages = ref([])
const loading = ref(true)
const responseText = ref('')
const submittingResponse = ref(false)
const agreeing = ref(false)
const newThreadMsg = ref('')

// Lightbox
const lightboxOpen = ref(false)
const lightboxIndex = ref(0)
const currentLightboxFile = computed(() => evidenceFiles.value[lightboxIndex.value])

// Timer
const timerDisplay = ref('--:--:--')
const timerExpired = ref(false)
let timerHandle = null
let pollHandle = null

const isResolved = computed(() => ['APPROVED', 'REJECTED'].includes(dispute.value?.disputeStatus))
const statusBadgeClass = computed(() => ({
  OPEN: 'text-amber-400', RESPONSE: 'text-blue-400', AWAITING_DECISION: 'text-purple-400',
  APPROVED: 'text-sage', REJECTED: 'text-red-400',
}[dispute.value?.disputeStatus] || 'text-slate'))

onMounted(async () => {
  try {
    const [dRes, eRes] = await Promise.all([
      getDispute(disputeID),
      getEvidenceByDispute(disputeID).catch(() => ({ data: [] })),
    ])
    dispute.value = dRes?.data ?? null
    evidenceFiles.value = eRes?.data ?? []

    await loadThread()
    startTimer()
    pollHandle = setInterval(loadThread, 3000)
  } catch (err) { console.error('Failed to load dispute:', err) }
  finally { loading.value = false }
})

onUnmounted(() => { clearInterval(timerHandle); clearInterval(pollHandle) })

async function loadThread() {
  try {
    const msgs = await getMessagesByOrder(-disputeID)
    threadMessages.value = Array.isArray(msgs) ? msgs : []
  } catch { /* silent */ }
}

function startTimer() {
  if (!dispute.value?.deadlineAt) return
  const update = () => {
    const diff = new Date(dispute.value.deadlineAt) - new Date()
    if (diff <= 0) { timerExpired.value = true; timerDisplay.value = '00:00:00'; clearInterval(timerHandle) }
    else {
      const h = Math.floor(diff / 3600000), m = Math.floor((diff % 3600000) / 60000), s = Math.floor((diff % 60000) / 1000)
      timerDisplay.value = `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`
    }
  }
  update(); timerHandle = setInterval(update, 1000)
}

async function submitResponse() {
  if (!responseText.value.trim()) return
  submittingResponse.value = true
  try {
    const res = await submitSellerResponse(disputeID, responseText.value)
    dispute.value = res?.data ?? { ...dispute.value, sellerResponse: responseText.value, disputeStatus: 'RESPONSE' }
    // Also send as a thread message
    await sendMessage({ orderID: -disputeID, senderID: mockSeller.id, receiverID: dispute.value.buyerID, content: responseText.value, messageType: 'text' }).catch(() => {})
    await loadThread()
  } catch (err) { alert('Failed: ' + err.message) }
  finally { submittingResponse.value = false }
}

async function handleSellerAgree() {
  agreeing.value = true
  try {
    const res = await sellerAgreeDispute(disputeID)
    dispute.value = res?.data ?? { ...dispute.value, disputeStatus: 'AWAITING_DECISION' }
  } catch (err) { alert('Failed: ' + err.message) }
  finally { agreeing.value = false }
}

async function sendThreadMessage() {
  if (!newThreadMsg.value.trim()) return
  const content = newThreadMsg.value
  newThreadMsg.value = ''
  try {
    await sendMessage({ orderID: -disputeID, senderID: mockSeller.id, receiverID: dispute.value?.buyerID || 0, content, messageType: 'text' })
    await loadThread()
  } catch (err) { console.warn('Send failed:', err) }
}

function openLightbox(i) { lightboxIndex.value = i; lightboxOpen.value = true }
function isImage(t) { return t && (t.startsWith('image/') || /\.(jpg|jpeg|png|gif|webp)$/i.test(t)) }
function fileIcon(n) { if (!n) return '📎'; if (n.match(/\.(jpg|jpeg|png|gif|webp)$/i)) return '🖼'; if (n.match(/\.(mp4|mov|avi)$/i)) return '🎥'; if (n.match(/\.pdf$/i)) return '📄'; return '📎' }
function formatDate(iso) { if (!iso) return '—'; return new Date(iso).toLocaleDateString('en-SG', { day: 'numeric', month: 'short', year: 'numeric' }) }
function formatTime(t) { if (!t) return ''; return new Date(t).toLocaleTimeString('en-SG', { hour: '2-digit', minute: '2-digit' }) }
</script>
