<template>
  <div class="min-h-screen bg-paper flex flex-col">
    <SellerNavbar :seller="mockSeller" />

    <div class="pt-16 flex-1 flex flex-col">
      <!-- Header -->
      <div class="bg-ink text-paper px-6 py-4 flex items-center justify-between border-b border-white/10">
        <div class="flex items-center gap-4">
          <button @click="$router.back()" class="text-white/40 hover:text-accent transition-colors text-sm font-mono">← Back</button>
          <div class="w-px h-5 bg-white/20"></div>
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 bg-accent/20 text-accent font-display font-bold text-sm flex items-center justify-center">B</div>
            <div>
              <p class="font-display font-semibold text-sm">Buyer #{{ order?.buyer_id }}</p>
              <p class="text-xs text-white/40 font-mono">Order #{{ orderID }}</p>
            </div>
          </div>
        </div>

        <!-- Order pill -->
        <div v-if="order" class="hidden sm:flex items-center gap-3 bg-white/5 border border-white/10 px-3 py-2">
          <div class="w-8 h-8 overflow-hidden bg-white/10 flex items-center justify-center flex-shrink-0">
            <img v-if="listingImage" :src="listingImage" class="w-full h-full object-cover" />
            <span v-else class="text-white/40 text-xs">🛍</span>
          </div>
          <div>
            <p class="font-display font-semibold text-xs truncate max-w-[160px]">
              {{ order.order_details || `Listing #${order.listing_id}` }}
            </p>
            <p class="font-mono text-xs text-accent">${{ order.agreed_price }}</p>
          </div>
        </div>
      </div>

      <!-- Chat area -->
      <div class="flex flex-1 overflow-hidden">
        <div class="flex-1 flex flex-col">

          <!-- Message list -->
          <div ref="messagesContainer" class="flex-1 overflow-y-auto p-6 space-y-4 max-h-[calc(100vh-240px)]">
            <div class="text-center">
              <span class="section-label bg-cream px-3 py-1.5 text-muted">
                Conversation for Order #{{ orderID }}
              </span>
            </div>

            <!-- Loading messages -->
            <div v-if="loadingMessages" class="text-center py-8 text-muted font-mono text-sm">
              Loading messages...
            </div>

            <template v-else>
              <div
                v-for="msg in messages"
                :key="msg.id"
                class="flex"
                :class="msg.sender === 'seller' ? 'justify-end' : 'justify-start'"
              >
                <!-- Buyer avatar -->
                <div v-if="msg.sender === 'buyer'" class="w-7 h-7 bg-white border border-ink/10 text-ink font-display font-bold text-xs flex items-center justify-center mr-2 mt-1 flex-shrink-0">
                  B
                </div>

                <div class="max-w-[70%]">
                  <!-- Offer bubble -->
                  <div v-if="msg.type === 'offer'" class="border-2 p-3 mb-1"
                    :class="msg.sender === 'seller' ? 'border-accent bg-accent/5' : 'border-ink/20 bg-white'"
                  >
                    <p class="section-label text-accent mb-1">{{ msg.sender === 'seller' ? 'Your Final Offer' : 'Buyer Offer' }}</p>
                    <p class="font-display font-bold text-2xl text-ink">${{ msg.offerAmount }}</p>
                    <!-- Accept/counter buttons for seller on buyer offers -->
                    <div v-if="msg.sender === 'buyer' && !agreedPrice && msg.id === lastBuyerOfferId" class="flex gap-2 mt-3">
                      <button @click="acceptBuyerOffer(msg.offerAmount)" class="btn-primary text-xs px-3 py-1.5 flex-1">Accept ${{ msg.offerAmount }}</button>
                      <button @click="showCounterInput = true" class="btn-secondary text-xs px-3 py-1.5 flex-1">Counter</button>
                    </div>
                  </div>

                  <!-- Agreement bubble -->
                  <div v-else-if="msg.type === 'agreement'" class="bg-sage/10 border border-sage/30 p-3 text-center mb-1">
                    <span class="text-sage text-lg">🤝</span>
                    <p class="font-display font-semibold text-sm text-sage mt-1">Deal agreed at ${{ msg.offerAmount }}</p>
                    <p class="text-xs text-muted font-mono">Both parties confirmed</p>
                  </div>

                  <!-- Text bubble -->
                  <div v-else
                    class="px-4 py-2.5 text-sm leading-relaxed"
                    :class="msg.sender === 'seller'
                      ? 'bg-accent text-white'
                      : 'bg-white border border-ink/10 text-ink'"
                  >
                    {{ msg.text }}
                  </div>

                  <p class="text-xs text-muted font-mono mt-1" :class="msg.sender === 'seller' ? 'text-right' : 'text-left'">
                    {{ msg.time }}
                  </p>
                </div>

                <!-- Seller avatar -->
                <div v-if="msg.sender === 'seller'" class="w-7 h-7 bg-accent text-white font-display font-bold text-xs flex items-center justify-center ml-2 mt-1 flex-shrink-0">
                  {{ mockSeller.name.charAt(0) }}
                </div>
              </div>

              <div v-if="messages.length === 0" class="text-center py-12 text-muted font-mono text-sm">
                No messages yet. Start the conversation.
              </div>
            </template>
          </div>

          <!-- Agreed banner -->
          <div v-if="agreedPrice" class="mx-6 mb-4 bg-sage/10 border border-sage/30 p-4 flex items-center justify-between">
            <div>
              <p class="font-display font-semibold text-sm text-sage">🤝 Deal confirmed at ${{ agreedPrice }}</p>
              <p class="text-xs text-muted font-mono">Buyer can now proceed to payment</p>
            </div>
            <button @click="agreedPrice = null" class="text-xs font-mono text-muted hover:text-red-500 transition-colors">Revoke</button>
          </div>

          <!-- Input bar -->
          <div class="border-t border-ink/10 p-4 bg-paper">
            <!-- Counter offer input -->
            <div v-if="showCounterInput" class="flex gap-2 mb-3">
              <div class="flex items-center border border-accent bg-accent/5 flex-1">
                <span class="px-3 font-mono text-accent font-semibold">$</span>
                <input
                  v-model="counterAmount"
                  type="number"
                  class="flex-1 bg-transparent py-2 font-mono text-ink outline-none"
                  placeholder="Enter final offer amount"
                  min="1"
                />
              </div>
              <button @click="sendCounterOffer" class="btn-primary text-xs px-4" :disabled="!counterAmount">Send</button>
              <button @click="showCounterInput = false" class="btn-secondary text-xs px-3">✕</button>
            </div>

            <!-- Deal input panel -->
            <div v-if="showDealInput" class="flex gap-2 mb-3">
              <div class="flex items-center border-2 border-sage bg-sage/5 flex-1">
                <span class="px-3 font-mono text-sage font-bold">$</span>
                <input
                  v-model="agreedPriceInput"
                  type="number"
                  class="flex-1 bg-transparent py-2 font-mono text-ink outline-none"
                  placeholder="Enter agreed price"
                  min="1"
                  @keyup.enter="confirmDeal()"
                />
              </div>
              <button @click="confirmDeal()" :disabled="!agreedPriceInput" class="bg-sage text-white text-xs px-4 font-mono font-semibold hover:bg-sage/80 transition-colors disabled:opacity-40">
                ✅ Confirm
              </button>
              <button @click="showDealInput = false" class="btn-secondary text-xs px-3">✕</button>
            </div>

            <!-- Quick replies -->
            <div class="flex gap-2 mb-3 flex-wrap">
              <button @click="showCounterInput = !showCounterInput" class="text-xs border border-accent text-accent px-3 py-1.5 hover:bg-accent hover:text-white transition-colors font-mono">
                💰 Final Offer
              </button>
              <button @click="sendQuickMessage('The item is still available!')" class="text-xs border border-ink/20 text-slate px-3 py-1.5 hover:border-ink/50 transition-colors font-mono">
                Still available
              </button>
              <button @click="sendQuickMessage('I can meet at Tampines MRT.')" class="text-xs border border-ink/20 text-slate px-3 py-1.5 hover:border-ink/50 transition-colors font-mono">
                Meetup location
              </button>
              <button @click="sendQuickMessage('That is my final price, sorry!')" class="text-xs border border-ink/20 text-slate px-3 py-1.5 hover:border-ink/50 transition-colors font-mono">
                Final price
              </button>
            </div>

            <!-- Message input -->
            <div class="flex gap-2">
              <input
                v-model="newMessage"
                type="text"
                class="input-field flex-1"
                placeholder="Reply to buyer..."
                @keyup.enter="sendMessage"
              />
              <button @click="sendMessage" class="btn-primary px-4" :disabled="!newMessage.trim() || sending">
                {{ sending ? '...' : 'Send' }}
              </button>
            </div>
          </div>

        </div>

        <!-- Right sidebar: listing summary -->
        <div class="hidden lg:block w-64 border-l border-ink/10 p-5 bg-cream/50">
          <p class="section-label mb-4">Listing</p>

          <!-- Post-order: show order + listing data -->
          <div v-if="order">
            <div class="aspect-square bg-cream overflow-hidden mb-3 flex items-center justify-center">
              <img v-if="listingImage" :src="listingImage" class="w-full h-full object-cover" />
              <span v-else class="text-4xl text-ink/10">🛍</span>
            </div>
            <p class="font-display font-semibold text-sm leading-tight mb-2">
              {{ order.order_details || `Listing #${order.listing_id}` }}
            </p>
            <div class="flex items-baseline gap-2 mb-3">
              <span class="font-display font-bold text-xl text-accent">${{ agreedPrice || order.agreed_price }}</span>
              <span v-if="agreedPrice && agreedPrice !== order.agreed_price" class="font-mono text-xs text-muted line-through">${{ order.agreed_price }}</span>
            </div>
            <div class="space-y-2 text-xs font-mono">
              <div class="flex justify-between">
                <span class="text-muted">Status</span>
                <span class="text-ink">{{ order.status }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-muted">Buyer ID</span>
                <span class="text-ink">#{{ order.buyer_id }}</span>
              </div>
            </div>
            <div class="mt-4 pt-4 border-t border-ink/10">
              <p class="section-label mb-2">Negotiation</p>
              <div class="space-y-1 text-xs font-mono">
                <div class="flex justify-between">
                  <span class="text-muted">Listed at</span>
                  <span>${{ order.agreed_price }}</span>
                </div>
                <div v-if="agreedPrice" class="flex justify-between">
                  <span class="text-muted">Agreed</span>
                  <span class="text-sage font-semibold">${{ agreedPrice }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Pre-order (inbox): show listing data from OutSystems -->
          <div v-else-if="listing">
            <div class="aspect-square bg-cream overflow-hidden mb-3 flex items-center justify-center">
              <img v-if="listing.listingImgUrl" :src="listing.listingImgUrl" class="w-full h-full object-cover" />
              <span v-else class="text-4xl text-ink/10">🛍</span>
            </div>
            <p class="font-display font-semibold text-sm leading-tight mb-2">{{ listing.listingName }}</p>
            <div class="flex items-baseline gap-2 mb-3">
              <span class="font-display font-bold text-xl text-accent">${{ agreedPrice || listing.listingPrice }}</span>
              <span v-if="agreedPrice" class="font-mono text-xs text-muted line-through">${{ listing.listingPrice }}</span>
            </div>
            <div class="space-y-2 text-xs font-mono">
              <div class="flex justify-between">
                <span class="text-muted">Category</span>
                <span class="text-ink">{{ listing.listingCategory }}</span>
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
            <div v-if="agreedPrice" class="mt-4 pt-4 border-t border-ink/10">
              <p class="section-label mb-2">Negotiation</p>
              <div class="space-y-1 text-xs font-mono">
                <div class="flex justify-between">
                  <span class="text-muted">Listed at</span>
                  <span>${{ listing.listingPrice }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-muted">Agreed</span>
                  <span class="text-sage font-semibold">${{ agreedPrice }}</span>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="text-muted font-mono text-xs">Loading listing details...</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import SellerNavbar from '../../components/SellerNavbar.vue'
import { mockSeller, mockUser } from '../../data/mockData.js'
import { getOrdersBySeller, getMessagesByOrder, sendMessage as sendMessageApi, fetchListings, sendNotification, fetchListingById } from '../../services/api.js'
import { saveDeal, getDeal } from '../../data/negotiationStore.js'

const route   = useRoute()
const router  = useRouter()
// Support both /seller/messages/:orderID and /seller/inbox/:listingID
// For inbox route, listingID is used as the orderID (conversation key)
const orderID  = parseInt(route.params.orderID ?? 0)
const inboxKey = parseInt(route.params.listingID ?? 0) // listingID used as orderID for pre-order chats
const convKey  = inboxKey || orderID // the actual key to fetch messages by

const order           = ref(null)
const listing         = ref(null)  // fallback for pre-order inbox chats
const listingImages   = ref({})
const messages        = ref([])
const loadingMessages = ref(true)
const newMessage      = ref('')
const sending         = ref(false)
const showCounterInput = ref(false)
const counterAmount   = ref('')
const agreedPrice      = ref(null)
const agreedPriceInput = ref('')
const showDealInput    = ref(false)
let pollHandle         = null
const localPendingContents = new Set()

const messagesContainer = ref(null)

const listingImage = computed(() =>
  order.value ? listingImages.value[order.value.listing_id] || null : null
)

// Last buyer offer ID — for showing accept/counter buttons
const lastBuyerOfferId = computed(() => {
  const buyerOffers = messages.value.filter(m => m.sender === 'buyer' && m.type === 'offer')
  return buyerOffers.length ? buyerOffers[buyerOffers.length - 1].id : null
})

function timestamp() {
  return new Date().toLocaleTimeString('en-SG', { hour: '2-digit', minute: '2-digit' })
}

// Convert a raw DB message to the display format
function toDisplayMsg(raw) {
  const isSeller = raw.senderID === mockSeller.id
  return {
    id:          raw.messageID,
    sender:      isSeller ? 'seller' : 'buyer',
    type:        raw.messageType || 'text',
    text:        raw.content,
    offerAmount: raw.offerAmount,
    time:        raw.sentAt ? new Date(raw.sentAt.includes('T') ? raw.sentAt : raw.sentAt.replace(' ', 'T') + 'Z').toLocaleTimeString('en-SG', { hour: '2-digit', minute: '2-digit' }) : timestamp(),
  }
}

async function scrollToBottom() {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

onMounted(async () => {
  try {
    const [ordersData, listingsData, messagesData] = await Promise.all([
      getOrdersBySeller(mockSeller.id),
      fetchListings().catch(() => null),
      getMessagesByOrder(convKey).catch(() => []),
    ])

    const allOrders = Array.isArray(ordersData) ? ordersData : (ordersData.orders ?? [])
    // Find order by order_id OR by listing_id (for inbox/pre-order chats)
    order.value = allOrders.find(o =>
      (orderID && o.order_id === orderID) ||
      (inboxKey && o.listing_id === inboxKey)
    ) || null

    // If no order found yet (pre-payment), fetch listing details from OutSystems
    if (!order.value && inboxKey) {
      try {
        const listingRes = await fetchListingById(inboxKey)
        listing.value = listingRes?.data ?? null
      } catch (e) {
        console.warn('[Seller Messages] Could not fetch listing:', e)
      }
    }

    const listings = listingsData?.data?.listings ?? []
    listings.forEach(l => {
      if (l.listingImgUrl && l.listingImgUrl.length > 5) {
        listingImages.value[l.listingID] = l.listingImgUrl
      }
    })

    // Load real messages from backend
    const rawMessages = Array.isArray(messagesData) ? messagesData : []
    messages.value = rawMessages.map(toDisplayMsg)

    // Check if any agreement already exists in messages
    const agreement = messages.value.find(m => m.type === 'agreement')
    if (agreement) agreedPrice.value = agreement.offerAmount

    // Also restore from localStorage in case it was set manually
    const savedDeal = getDeal(order.value ? order.value.listing_id : convKey)
    if (savedDeal && !agreedPrice.value) agreedPrice.value = savedDeal.price

  } catch (err) {
    console.error('Failed to load seller messages:', err)
  } finally {
    loadingMessages.value = false
    scrollToBottom()
  }

  // Poll for new messages every 3 seconds
  const fetchFn = () => getMessagesByOrder(convKey)

  pollHandle = setInterval(async () => {
    try {
      const fresh = await fetchFn()
      const raw = Array.isArray(fresh) ? fresh : []
      const existingIds = new Set(messages.value.map(m => m.id))
      const newMsgs = raw
        .filter(m => !existingIds.has(m.messageID) && !localPendingContents.has(m.content))
        .map(toDisplayMsg)
      if (newMsgs.length > 0) {
        messages.value.push(...newMsgs)
        // Update agreedPrice if buyer sent an agreement
        const newAgreement = newMsgs.find(m => m.type === 'agreement')
        if (newAgreement) agreedPrice.value = newAgreement.offerAmount
        await scrollToBottom()
      }
    } catch {
      // silently ignore poll errors
    }
  }, 3000)
})

onUnmounted(() => clearInterval(pollHandle))

function addLocalMessage(msg) {
  localPendingContents.add(msg.content ?? msg.text)
  messages.value.push(msg)
  scrollToBottom()
}

async function sendMessage() {
  if (!newMessage.value.trim() || sending.value) return
  const content = newMessage.value
  newMessage.value = ''
  sending.value = true
  addLocalMessage({ id: `local_${Date.now()}`, sender: 'seller', type: 'text', text: content, content, time: timestamp() })

  try {
    await sendMessageApi({
      orderID:     convKey,
      senderID:    mockSeller.id,
      receiverID:  order.value?.buyer_id ?? mockUser?.id ?? 1,
      content,
      messageType: 'text',
    })
    // Bell notification to buyer (no SMS)
    sendNotification({
      orderID:    convKey,
      disputeID:  null,
      notification: `[TradeNest] New message from seller: "${content.slice(0, 60)}${content.length > 60 ? '...' : ''}"`,
      receiverID: order.value?.buyer_id ?? 1,
    }).catch(() => {})
  } catch (err) {
    console.warn('[Seller Messaging] Backend unavailable:', err.message)
  } finally {
    sending.value = false
  }
}

async function sendQuickMessage(text) {
  newMessage.value = text
  await sendMessage()
}

async function sendCounterOffer() {
  if (!counterAmount.value) return
  const amount = parseFloat(counterAmount.value)
  const content = `Counter offer: $${amount}`
  showCounterInput.value = false
  counterAmount.value = ''

  addLocalMessage({ id: `local_${Date.now()}`, sender: 'seller', type: 'offer', text: content, content, offerAmount: amount, time: timestamp() })

  try {
    await sendMessageApi({
      orderID:     convKey,
      senderID:    mockSeller.id,
      receiverID:  order.value?.buyer_id ?? mockUser?.id ?? 1,
      content,
      messageType: 'offer',
      offerAmount: amount,
    })
  } catch (err) {
    console.warn('[Seller Messaging] Backend unavailable:', err.message)
  }
}

async function acceptBuyerOffer(amount) {
  confirmDeal(amount)
}

function confirmDeal(amount) {
  const price = parseFloat(amount || agreedPriceInput.value)
  if (!price || price <= 0) return

  agreedPrice.value = price
  showDealInput.value = false
  agreedPriceInput.value = ''

  // Save to localStorage so buyer page picks it up automatically
  const dealKey = order.value ? order.value.listing_id : convKey
  saveDeal(dealKey, price)

  // Also post a regular text message so it appears in both chats
  const content = `✅ Deal confirmed at ${price}. Proceed to payment.`
  addLocalMessage({ id: `local_${Date.now()}`, sender: 'seller', type: 'text', text: content, content, time: timestamp() })

  sendMessageApi({
    orderID:     convKey,
    senderID:    mockSeller.id,
    receiverID:  order.value?.buyer_id ?? mockUser?.id ?? 1,
    content,
    messageType: 'text',
  }).catch(err => console.warn('[Seller Messaging] Backend unavailable:', err.message))
}
</script>
