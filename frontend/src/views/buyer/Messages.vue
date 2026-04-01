<template>
  <div class="min-h-screen bg-paper flex flex-col">
    <Navbar :user="mockUser" />

    <div class="pt-16 flex-1 flex flex-col" v-if="listing">
      <!-- Header bar -->
      <div class="bg-ink text-paper px-6 py-4 flex items-center justify-between border-b border-white/10">
        <div class="flex items-center gap-4">
          <button @click="$router.back()" class="text-white/40 hover:text-accent transition-colors text-sm font-mono">← Back</button>
          <div class="w-px h-5 bg-white/20"></div>
          <!-- Seller placeholder (no seller data from OutSystems) -->
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 bg-accent/20 text-accent font-display font-bold text-sm flex items-center justify-center">
              S
            </div>
            <div>
              <p class="font-display font-semibold text-sm">Seller</p>
              <div class="flex items-center gap-1.5">
                <span class="w-1.5 h-1.5 bg-sage rounded-full"></span>
                <span class="text-xs text-white/40 font-mono">Online</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Listing pill -->
        <div class="hidden sm:flex items-center gap-3 bg-white/5 border border-white/10 px-3 py-2">
          <div class="w-8 h-8 overflow-hidden bg-white/10 flex-shrink-0 flex items-center justify-center">
            <img
              v-if="listing.listingImgUrl && listing.listingImgUrl.length > 5"
              :src="listing.listingImgUrl"
              :alt="listing.listingName"
              class="w-full h-full object-cover"
            />
            <span v-else class="text-white/40 text-xs">🛍</span>
          </div>
          <div>
            <p class="font-display font-semibold text-xs leading-tight truncate max-w-[160px]">{{ listing.listingName }}</p>
            <p class="font-mono text-xs text-accent">${{ currentOffer || listing.listingPrice }}</p>
          </div>
        </div>
      </div>

      <!-- Chat area -->
      <div class="flex flex-1 overflow-hidden">
        <!-- Messages -->
        <div class="flex-1 flex flex-col">
          <!-- Message list -->
          <div ref="messagesContainer" class="flex-1 overflow-y-auto p-6 space-y-4 max-h-[calc(100vh-280px)]">
            <!-- System message -->
            <div class="text-center">
              <span class="section-label bg-cream px-3 py-1.5 text-muted">
                Negotiation started · {{ listing.listingName }}
              </span>
            </div>

            <!-- Messages -->
            <div
              v-for="msg in messages"
              :key="msg.id"
              class="flex"
              :class="msg.sender === 'buyer' ? 'justify-end' : 'justify-start'"
            >
              <!-- Seller avatar -->
              <div v-if="msg.sender === 'seller'" class="w-7 h-7 bg-white border border-ink/10 text-ink font-display font-bold text-xs flex items-center justify-center mr-2 mt-1 flex-shrink-0">
                S
              </div>

              <div class="max-w-[70%]">
                <!-- Offer message type -->
                <div v-if="msg.type === 'offer'" class="border-2 p-3 mb-1"
                  :class="msg.sender === 'buyer' ? 'border-accent bg-accent/5' : 'border-ink/20 bg-white'"
                >
                  <p class="section-label text-accent mb-1">{{ msg.sender === 'buyer' ? 'Your Offer' : 'Counter Offer' }}</p>
                  <p class="font-display font-bold text-2xl text-ink">${{ msg.offerAmount }}</p>
                  <p class="text-xs text-muted font-mono mt-1">
                    {{ msg.sender === 'buyer' ? `Down from $${listing.listingPrice}` : `Original: $${listing.listingPrice}` }}
                  </p>
                  <!-- Accept/reject buttons on seller offers (shown to buyer) -->
                  <div v-if="msg.sender === 'seller' && !agreedPrice && msg.id === lastSellerOfferId" class="flex gap-2 mt-3">
                    <button @click="acceptOffer(msg.offerAmount)" class="btn-primary text-xs px-3 py-1.5 flex-1">Accept ${{ msg.offerAmount }}</button>
                    <button @click="triggerCounterOffer" class="btn-secondary text-xs px-3 py-1.5 flex-1">Counter</button>
                  </div>
                </div>

                <!-- Agreement message -->
                <div v-else-if="msg.type === 'agreement'" class="bg-sage/10 border border-sage/30 p-3 text-center mb-1">
                  <span class="text-sage text-lg">🤝</span>
                  <p class="font-display font-semibold text-sm text-sage mt-1">Deal agreed at ${{ msg.offerAmount }}</p>
                  <p class="text-xs text-muted font-mono">Both parties confirmed</p>
                </div>

                <!-- Regular text message -->
                <div v-else
                  class="px-4 py-2.5 text-sm leading-relaxed"
                  :class="msg.sender === 'buyer'
                    ? 'bg-accent text-white'
                    : 'bg-white border border-ink/10 text-ink'"
                >
                  {{ msg.text }}
                </div>

                <p class="text-xs text-muted font-mono mt-1"
                  :class="msg.sender === 'buyer' ? 'text-right' : 'text-left'"
                >{{ msg.time }}</p>
              </div>

              <!-- Buyer avatar -->
              <div v-if="msg.sender === 'buyer'" class="w-7 h-7 bg-accent text-white font-display font-bold text-xs flex items-center justify-center ml-2 mt-1 flex-shrink-0">
                {{ mockUser.name.charAt(0) }}
              </div>
            </div>

          </div>

          <!-- Agreed — proceed to purchase -->
          <div v-if="agreedPrice" class="mx-6 mb-4 bg-sage/10 border border-sage/30 p-4 flex items-center justify-between">
            <div>
              <p class="font-display font-semibold text-sm text-sage">🤝 Deal agreed at ${{ agreedPrice }}</p>
              <p class="text-xs text-muted font-mono">Ready to proceed with payment</p>
            </div>
            <button @click="proceedToPurchase" class="btn-primary text-xs px-4 py-2">
              Pay ${{ agreedPrice }} →
            </button>
          </div>

          <!-- Input bar -->
          <div class="border-t border-ink/10 p-4 bg-paper" v-if="!agreedPrice">
            <!-- Quick actions -->
            <div class="flex gap-2 mb-3 flex-wrap">
              <button @click="showOfferInput = !showOfferInput" class="text-xs border border-accent text-accent px-3 py-1.5 hover:bg-accent hover:text-white transition-colors font-mono">
                💰 Make Offer
              </button>
              <button @click="sendQuickMessage('Is this still available?')" class="text-xs border border-ink/20 text-slate px-3 py-1.5 hover:border-ink/50 transition-colors font-mono">
                Still available?
              </button>
              <button @click="sendQuickMessage('Can we meet at an MRT station?')" class="text-xs border border-ink/20 text-slate px-3 py-1.5 hover:border-ink/50 transition-colors font-mono">
                MRT meetup?
              </button>
              <button @click="sendQuickMessage('What\'s the lowest you can go?')" class="text-xs border border-ink/20 text-slate px-3 py-1.5 hover:border-ink/50 transition-colors font-mono">
                Best price?
              </button>
            </div>

            <!-- Offer input -->
            <div v-if="showOfferInput" class="flex gap-2 mb-3">
              <div class="flex items-center border border-accent bg-accent/5 flex-1">
                <span class="px-3 font-mono text-accent font-semibold">$</span>
                <input
                  v-model="offerAmount"
                  type="number"
                  class="flex-1 bg-transparent py-2 font-mono text-ink outline-none"
                  :placeholder="listing.listingPrice"
                  :max="listing.listingPrice"
                  min="1"
                />
              </div>
              <button @click="sendOffer" class="btn-primary text-xs px-4" :disabled="!offerAmount">
                Send Offer
              </button>
              <button @click="showOfferInput = false" class="btn-secondary text-xs px-3">✕</button>
            </div>

            <!-- Message input -->
            <div class="flex gap-2">
              <input
                v-model="newMessage"
                type="text"
                class="input-field flex-1"
                placeholder="Type a message..."
                @keyup.enter="sendMessage"
              />
              <button @click="sendMessage" class="btn-primary px-4" :disabled="!newMessage.trim()">
                Send
              </button>
            </div>
          </div>
        </div>

        <!-- Right sidebar: listing summary -->
        <div class="hidden lg:block w-64 border-l border-ink/10 p-5 bg-cream/50">
          <p class="section-label mb-4">Listing</p>
          <div class="aspect-square bg-cream overflow-hidden mb-3 flex items-center justify-center">
            <img
              v-if="listing.listingImgUrl && listing.listingImgUrl.length > 5"
              :src="listing.listingImgUrl"
              :alt="listing.listingName"
              class="w-full h-full object-cover"
            />
            <span v-else class="text-4xl text-ink/10">🛍</span>
          </div>
          <p class="font-display font-semibold text-sm leading-tight mb-2">{{ listing.listingName }}</p>
          <div class="flex items-baseline gap-2 mb-3">
            <span class="font-display font-bold text-xl text-accent">${{ currentOffer || listing.listingPrice }}</span>
            <span v-if="currentOffer && currentOffer !== listing.listingPrice" class="font-mono text-xs text-muted line-through">${{ listing.listingPrice }}</span>
          </div>
          <div class="space-y-2 text-xs font-mono">
            <div class="flex justify-between">
              <span class="text-muted">Category</span>
              <span class="text-ink">{{ listing.listingCategory || 'General' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-muted">Stock</span>
              <span class="text-ink">{{ listing.listingStockQty }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-muted">Status</span>
              <span class="text-ink">{{ listing.listingStatus || 'ACTIVE' }}</span>
            </div>
          </div>

          <div class="mt-4 pt-4 border-t border-ink/10">
            <p class="section-label mb-2">Negotiation</p>
            <div class="space-y-1 text-xs font-mono">
              <div class="flex justify-between">
                <span class="text-muted">Listed at</span>
                <span>${{ listing.listingPrice }}</span>
              </div>
              <div class="flex justify-between" v-if="currentOffer">
                <span class="text-muted">Current offer</span>
                <span class="text-accent font-semibold">${{ currentOffer }}</span>
              </div>
              <div class="flex justify-between" v-if="agreedPrice">
                <span class="text-muted">Agreed</span>
                <span class="text-sage font-semibold">${{ agreedPrice }}</span>
              </div>
            </div>
          </div>

          <button
            v-if="!agreedPrice"
            @click="proceedToPurchaseAtListingPrice"
            class="btn-secondary w-full mt-4 text-xs"
          >
            Buy at ${{ listing.listingPrice }}
          </button>
        </div>
      </div>
    </div>

    <!-- Loading state -->
    <div v-else-if="!listing" class="flex-1 flex items-center justify-center pt-16">
      <p class="font-mono text-sm text-muted">Loading listing...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Navbar from '../../components/Navbar.vue'
import { mockUser } from '../../data/mockData.js'
import { fetchListingById, sendMessage as sendMessageToBackend, getMessagesByOrder } from '../../services/api.js'
import { getDeal } from '../../data/negotiationStore.js'

const route = useRoute()
const router = useRouter()

const listing = ref(null)

onMounted(async () => {
  // Use listingID as the conversation key so each product has its own chat history
  const listingID = parseInt(route.params.id)

  try {
    const [listingRes, messagesRes] = await Promise.all([
      fetchListingById(listingID),
      getMessagesByOrder(listingID).catch(() => []),
    ])
    listing.value = listingRes?.data ?? null

    // Load real messages from backend
    const raw = Array.isArray(messagesRes) ? messagesRes : []
    messages.value = raw.map(m => ({
      id:          m.messageID,
      sender:      m.senderID === mockUser.id ? 'buyer' : 'seller',
      type:        m.messageType || 'text',
      text:        m.content,
      offerAmount: m.offerAmount,
      time:        m.sentAt
        ? new Date(m.sentAt).toLocaleTimeString('en-SG', { hour: '2-digit', minute: '2-digit' })
        : timestamp(),
    }))
    // Restore agreed price — check messages first, then localStorage
    const agreement = messages.value.find(m => m.type === 'agreement')
    if (agreement) {
      agreedPrice.value = agreement.offerAmount
    } else {
      const deal = getDeal(listingID)
      if (deal?.price) {
        agreedPrice.value = deal.price
        currentOffer.value = deal.price
      }
    }
  } catch (err) {
    console.error('Failed to load listing or messages:', err)
  }
  await scrollToBottom()

  // Poll for new messages every 3 seconds
  pollHandle = setInterval(async () => {
    try {
      const fresh = await getMessagesByOrder(listingID)
      const raw = Array.isArray(fresh) ? fresh : []
      const existingIds = new Set(messages.value.map(m => m.id))
      const newMsgs = raw
        .filter(m =>
          !existingIds.has(m.messageID) &&
          !localPendingContents.has(m.content)
        )
        .map(m => ({
          id:          m.messageID,
          sender:      m.senderID === mockUser.id ? 'buyer' : 'seller',
          type:        m.messageType || 'text',
          text:        m.content,
          offerAmount: m.offerAmount,
          time:        m.sentAt
            ? new Date(m.sentAt).toLocaleTimeString('en-SG', { hour: '2-digit', minute: '2-digit' })
            : timestamp(),
        }))
      if (newMsgs.length > 0) {
        messages.value.push(...newMsgs)
        await scrollToBottom()
      }

      // Check localStorage for seller-confirmed deal (works even without DB messageType support)
      if (!agreedPrice.value) {
        const deal = getDeal(listingID)
        if (deal?.price) {
          agreedPrice.value = deal.price
          currentOffer.value = deal.price
        }
      }
    } catch {
      // silently ignore poll errors
    }
  }, 3000)
})

onUnmounted(() => clearInterval(pollHandle))

const messagesContainer = ref(null)
const newMessage = ref('')
const showOfferInput = ref(false)
const offerAmount = ref('')
const agreedPrice = ref(null)
const currentOffer = ref(null)

let pollHandle = null
// Track locally-sent messages by content to deduplicate when they return from backend
const localPendingContents = new Set()

function timestamp() {
  return new Date().toLocaleTimeString('en-SG', { hour: '2-digit', minute: '2-digit' })
}

const messages = ref([])

const lastSellerOfferId = computed(() => {
  const sellerOffers = messages.value.filter(m => m.sender === 'seller' && m.type === 'offer')
  return sellerOffers.length ? sellerOffers[sellerOffers.length - 1].id : null
})

async function scrollToBottom() {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// Fire-and-forget: persist message to backend, don't block the UI
async function persistToBackend(content, messageType = 'text', offerAmount = null) {
  const sellerID  = listing.value?.sellerID ?? 2
  const listingID = parseInt(route.params.id) // use listingID as orderID for conversation isolation
  try {
    await sendMessageToBackend({
      orderID:     listingID,
      senderID:    mockUser.id,
      receiverID:  sellerID,
      content,
      messageType,
      offerAmount,
    })
  } catch (err) {
    // Best-effort — silently ignore if backend is unavailable
    console.warn('[Messaging] Backend unavailable, message saved locally only:', err.message)
  }
}

function addLocalMessage(msg) {
  // Track content so the poller doesn't re-add it when it comes back from DB
  localPendingContents.add(msg.content ?? msg.text)
  messages.value.push(msg)
  scrollToBottom()
}

function sendMessage() {
  if (!newMessage.value.trim()) return
  const text = newMessage.value
  newMessage.value = ''
  addLocalMessage({ id: `local_${Date.now()}`, sender: 'buyer', type: 'text', text, content: text, time: timestamp() })
  persistToBackend(text)
}

function sendQuickMessage(text) {
  addLocalMessage({ id: `local_${Date.now()}`, sender: 'buyer', type: 'text', text, content: text, time: timestamp() })
  persistToBackend(text)
}

function sendOffer() {
  if (!offerAmount.value || !listing.value) return
  const amount = parseInt(offerAmount.value)
  currentOffer.value = amount
  const content = `Offer: ${amount}`
  offerAmount.value = ''
  showOfferInput.value = false
  addLocalMessage({ id: `local_${Date.now()}`, sender: 'buyer', type: 'offer', offerAmount: amount, text: content, content, time: timestamp() })
  persistToBackend(content, 'offer', amount)
}

function triggerCounterOffer() {
  showOfferInput.value = true
}

function acceptOffer(amount) {
  agreedPrice.value = amount
  currentOffer.value = amount
  const content = `Deal agreed at ${amount}`
  addLocalMessage({ id: `local_${Date.now()}`, sender: 'buyer', type: 'agreement', offerAmount: amount, text: content, content, time: timestamp() })
  persistToBackend(content, 'agreement', amount)
}

function proceedToPurchase() {
  if (agreedPrice.value) {
    router.push(`/purchase/${listing.value.listingID}?price=${agreedPrice.value}`)
  }
}

function proceedToPurchaseAtListingPrice() {
  router.push(`/purchase/${listing.value.listingID}`)
}
</script>
