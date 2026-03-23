<template>
  <div class="min-h-screen bg-paper">
    <Navbar :user="mockUser" />

    <div class="pt-16">
      <div class="max-w-3xl mx-auto px-6 py-10">
        <!-- Back -->
        <div class="flex items-center gap-2 mb-8">
          <router-link to="/orders" class="section-label text-muted hover:text-accent transition-colors">← My Orders</router-link>
        </div>

        <!-- Header -->
        <div class="mb-8">
          <div class="flex items-center gap-3 mb-2">
            <span class="text-red-500 text-2xl">⚠</span>
            <p class="section-label text-red-500">Raise a Dispute</p>
          </div>
          <h1 class="font-display font-extrabold text-3xl">What went wrong?</h1>
          <p class="text-slate text-sm mt-2 leading-relaxed">
            Filing a dispute will freeze the escrow funds. The seller will have
            <strong class="font-display">48 hours</strong> to respond before an automatic refund is issued.
          </p>
        </div>

        <!-- Order summary -->
        <div class="bg-white border border-ink/10 p-5 mb-6 flex gap-4 items-center">
          <div class="w-14 h-14 bg-cream overflow-hidden flex-shrink-0">
            <img :src="order.image" :alt="order.listing" class="w-full h-full object-cover" />
          </div>
          <div class="flex-1">
            <p class="font-mono text-xs text-muted mb-0.5">{{ order.id }}</p>
            <p class="font-display font-semibold">{{ order.listing }}</p>
            <p class="text-xs text-muted font-mono">Seller: {{ order.seller }}</p>
          </div>
          <div class="text-right">
            <p class="font-display font-bold text-xl text-accent">${{ order.amount }}</p>
            <p class="text-xs text-muted font-mono">In escrow</p>
          </div>
        </div>

        <!-- Dispute form -->
        <form @submit.prevent="submitDispute" class="space-y-6">
          <!-- Reason -->
          <div class="bg-white border border-ink/10 p-6">
            <p class="section-label mb-4">Reason for Dispute</p>
            <div class="space-y-2">
              <label
                v-for="reason in reasons"
                :key="reason.value"
                class="flex items-start gap-3 p-3 border cursor-pointer transition-colors"
                :class="form.reason === reason.value
                  ? 'border-accent bg-accent/5'
                  : 'border-ink/10 hover:border-ink/30'"
              >
                <input type="radio" v-model="form.reason" :value="reason.value" class="accent-accent mt-0.5" />
                <div>
                  <p class="font-display font-semibold text-sm">{{ reason.label }}</p>
                  <p class="text-xs text-muted font-mono mt-0.5">{{ reason.desc }}</p>
                </div>
              </label>
            </div>
          </div>

          <!-- Description -->
          <div class="bg-white border border-ink/10 p-6">
            <p class="section-label mb-4">Describe the Issue</p>
            <textarea
              v-model="form.description"
              class="input-field resize-none"
              rows="5"
              placeholder="Please describe what happened in detail. Include any relevant dates, communications with the seller, and the specific problem with the item..."
              required
            ></textarea>
            <p class="text-xs text-muted font-mono mt-2 text-right">{{ form.description.length }}/500</p>
          </div>

          <!-- Evidence upload -->
          <div class="bg-white border border-ink/10 p-6">
            <p class="section-label mb-1">Upload Evidence</p>
            <p class="text-xs text-muted font-mono mb-4">Photos, videos, screenshots (max 5 files, 10MB each)</p>

            <!-- Drop zone -->
            <div
              class="border-2 border-dashed border-ink/20 p-8 text-center cursor-pointer hover:border-accent/40 transition-colors"
              :class="{ 'border-accent bg-accent/5': isDragging }"
              @dragover.prevent="isDragging = true"
              @dragleave="isDragging = false"
              @drop.prevent="handleDrop"
              @click="$refs.fileInput.click()"
            >
              <div class="text-3xl mb-2">📎</div>
              <p class="font-display font-semibold text-sm mb-1">Drop files here or click to browse</p>
              <p class="text-xs text-muted font-mono">JPG, PNG, MP4, PDF supported</p>
              <input ref="fileInput" type="file" class="hidden" multiple accept="image/*,video/*,.pdf" @change="handleFileSelect" />
            </div>

            <!-- File list -->
            <div v-if="form.files.length > 0" class="mt-4 space-y-2">
              <div
                v-for="(file, i) in form.files"
                :key="i"
                class="flex items-center justify-between bg-cream px-4 py-2"
              >
                <div class="flex items-center gap-2">
                  <span class="text-sm">{{ fileIcon(file.name) }}</span>
                  <span class="font-mono text-xs text-slate">{{ file.name }}</span>
                </div>
                <div class="flex items-center gap-3">
                  <span class="font-mono text-xs text-muted">{{ formatSize(file.size) }}</span>
                  <button type="button" @click="removeFile(i)" class="text-red-400 hover:text-red-600 text-xs">✕</button>
                </div>
              </div>
            </div>

            <!-- Mock pre-filled files for demo -->
            <div v-if="form.files.length === 0" class="mt-4 space-y-2">
              <div
                v-for="mockFile in mockFiles"
                :key="mockFile"
                class="flex items-center justify-between bg-cream px-4 py-2"
              >
                <div class="flex items-center gap-2">
                  <span class="text-sm">🖼</span>
                  <span class="font-mono text-xs text-slate">{{ mockFile }}</span>
                </div>
                <span class="font-mono text-xs text-muted">Demo file</span>
              </div>
            </div>
          </div>

          <!-- Warning -->
          <div class="border border-amber-200 bg-amber-50 p-4 flex gap-3">
            <span class="text-amber-500 text-lg flex-shrink-0">⏱</span>
            <div>
              <p class="font-display font-semibold text-sm text-amber-800 mb-1">48-Hour Seller Response Window</p>
              <p class="text-xs text-amber-700 leading-relaxed">
                Once submitted, the seller will be notified and has 48 hours to respond.
                If no response is received by <strong>{{ deadline }}</strong>, you will be automatically refunded.
              </p>
            </div>
          </div>

          <!-- Submit -->
          <div class="flex gap-3">
            <router-link to="/orders" class="btn-secondary flex-1 text-center">Cancel</router-link>
            <button
              type="submit"
              class="flex-1 bg-red-600 text-white font-display font-semibold px-6 py-3 hover:bg-red-700 transition-colors text-sm tracking-wide uppercase"
              :disabled="!form.reason || !form.description || submitting"
            >
              {{ submitting ? 'Submitting...' : 'Submit Dispute' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>

  <!-- Success modal -->
  <div v-if="success" class="fixed inset-0 bg-ink/60 flex items-center justify-center z-50 p-6">
    <div class="bg-paper max-w-sm w-full p-8 text-center">
      <div class="w-16 h-16 bg-red-100 flex items-center justify-center mx-auto mb-4 text-3xl">⚠</div>
      <h2 class="font-display font-extrabold text-2xl mb-2">Dispute Filed</h2>
      <p class="text-slate text-sm mb-6 leading-relaxed">
        Your dispute has been submitted. The escrow funds are now frozen.
        The seller has 48 hours to respond.
      </p>
      <div class="bg-cream p-3 mb-6 text-left space-y-2">
        <div class="flex justify-between text-xs font-mono">
          <span class="text-muted">Dispute ID</span>
          <span class="text-ink">DIS-{{ Math.floor(Math.random() * 900 + 100) }}</span>
        </div>
        <div class="flex justify-between text-xs font-mono">
          <span class="text-muted">Deadline</span>
          <span class="text-red-600">{{ deadline }}</span>
        </div>
        <div class="flex justify-between text-xs font-mono">
          <span class="text-muted">Amount frozen</span>
          <span class="text-ink">${{ order.amount }}</span>
        </div>
      </div>
      <button @click="$router.push('/orders')" class="btn-primary w-full">Back to Orders</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watchEffect } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Navbar from '../../components/Navbar.vue'
import { mockOrders, mockUser } from '../../data/mockData.js'

const route = useRoute()
const router = useRouter()

const order = ref(null)

watchEffect(() => {
  order.value = mockOrders.find(o => o.id === route.params.id) || mockOrders[0]
})

const form = ref({ reason: '', description: '', files: [] })
const isDragging = ref(false)
const submitting = ref(false)
const success = ref(false)
const fileInput = ref(null)

const mockFiles = ['damage_photo_1.jpg', 'chat_screenshot.png']

const reasons = [
  { value: 'not_as_described', label: 'Item Not as Described', desc: 'Item condition or details differ significantly from listing' },
  { value: 'not_received', label: 'Item Not Received', desc: 'Seller did not show up or deliver the item' },
  { value: 'damaged', label: 'Item Damaged', desc: 'Item was damaged during handover or shipping' },
  { value: 'counterfeit', label: 'Counterfeit / Fake Item', desc: 'Item is not authentic as claimed' },
  { value: 'other', label: 'Other Issue', desc: 'Another problem not listed above' },
]

const deadline = computed(() => {
  const d = new Date()
  d.setDate(d.getDate() + 2)
  return d.toLocaleDateString('en-SG', { day: 'numeric', month: 'short', year: 'numeric' })
})

function handleDrop(e) {
  isDragging.value = false
  const files = Array.from(e.dataTransfer.files)
  form.value.files.push(...files.slice(0, 5 - form.value.files.length))
}

function handleFileSelect(e) {
  const files = Array.from(e.target.files)
  form.value.files.push(...files.slice(0, 5 - form.value.files.length))
}

function removeFile(i) { form.value.files.splice(i, 1) }

function fileIcon(name) {
  if (name.match(/\.(jpg|jpeg|png|gif|webp)$/i)) return '🖼'
  if (name.match(/\.(mp4|mov|avi)$/i)) return '🎥'
  if (name.match(/\.pdf$/i)) return '📄'
  return '📎'
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + 'B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + 'KB'
  return (bytes / (1024 * 1024)).toFixed(1) + 'MB'
}

async function submitDispute() {
  submitting.value = true
  await new Promise(r => setTimeout(r, 1500))
  submitting.value = false
  success.value = true
}
</script>
