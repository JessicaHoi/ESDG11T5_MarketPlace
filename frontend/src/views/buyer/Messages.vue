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

            <!-- Typing indicator -->
            <div v-if="sellerTyping" class="flex items-center gap-2">
              <div class="w-7 h-7 bg-white border border-ink/10 text-ink font-display font-bold text-xs flex items-center justify-center flex-shrink-0">
                S
              </div>
              <div class="bg-white border border-ink/10 px-4 py-2.5 flex items-center gap-1">
                <span v-for="i in 3" :key="i" class="w-1.5 h-1.5 bg-muted rounded-full animate-bounce" :style="{ animationDelay: `${i * 0.15}s` }"></span>
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
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Navbar from '../../components/Navbar.vue'
import { mockUser } from '../../data/mockData.js'
import { fetchListingById } from '../../services/api.js'

const route = useRoute()
const router = useRouter()

const listing = ref(null)

onMounted(async () => {
  try {
    const res = await fetchListingById(route.params.id)
    listing.value = res?.data ?? null
  } catch (err) {
    console.error('Failed to load listing:', err)
  }
})

const messagesContainer = ref(null)
const newMessage = ref('')
const showOfferInput = ref(false)
const offerAmount = ref('')
const sellerTyping = ref(false)
const agreedPrice = ref(null)
const currentOffer = ref(null)

let msgCounter = 10

function timestamp() {
  return new Date().toLocaleTimeString('en-SG', { hour: '2-digit', minute: '2-digit' })
}

const messages = ref([
  {
    id: 1,
    sender: 'seller',
    type: 'text',
    text: 'Hi! Yes, this item is still available. Feel free to ask any questions.',
    time: '10:02 AM',
  },
  {
    id: 2,
    sender: 'buyer',
    type: 'text',
    text: "Hi! I'm interested. Has the item been used heavily?",
    time: '10:04 AM',
  },
  {
    id: 3,
    sender: 'seller',
    type: 'text',
    text: "Not at all — I've only used it a handful of times. It's practically brand new.",
    time: '10:05 AM',
  },
])

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

function sendMessage() {
  if (!newMessage.value.trim()) return
  messages.value.push({
    id: ++msgCounter,
    sender: 'buyer',
    type: 'text',
    text: newMessage.value,
    time: timestamp(),
  })
  newMessage.value = ''
  scrollToBottom()
  simulateSellerReply()
}

function sendQuickMessage(text) {
  messages.value.push({
    id: ++msgCounter,
    sender: 'buyer',
    type: 'text',
    text,
    time: timestamp(),
  })
  scrollToBottom()
  simulateSellerReply()
}

function sendOffer() {
  if (!offerAmount.value || !listing.value) return
  const amount = parseInt(offerAmount.value)
  currentOffer.value = amount
  messages.value.push({
    id: ++msgCounter,
    sender: 'buyer',
    type: 'offer',
    offerAmount: amount,
    text: `Offer: $${amount}`,
    time: timestamp(),
  })
  offerAmount.value = ''
  showOfferInput.value = false
  scrollToBottom()
  simulateSellerCounterOffer(amount)
}

function triggerCounterOffer() {
  showOfferInput.value = true
}

function acceptOffer(amount) {
  agreedPrice.value = amount
  currentOffer.value = amount
  messages.value.push({
    id: ++msgCounter,
    sender: 'buyer',
    type: 'agreement',
    offerAmount: amount,
    text: `Deal agreed at $${amount}`,
    time: timestamp(),
  })
  scrollToBottom()
}

async function simulateSellerReply() {
  sellerTyping.value = true
  await new Promise(r => setTimeout(r, 1500))
  sellerTyping.value = false
  const replies = [
    'Sure, happy to answer any questions!',
    'Yes, the item is in great condition.',
    'I can do a meetup near Jurong East MRT.',
    'That works for me! When are you free?',
  ]
  messages.value.push({
    id: ++msgCounter,
    sender: 'seller',
    type: 'text',
    text: replies[Math.floor(Math.random() * replies.length)],
    time: timestamp(),
  })
  scrollToBottom()
}

async function simulateSellerCounterOffer(buyerOffer) {
  sellerTyping.value = true
  await new Promise(r => setTimeout(r, 2000))
  sellerTyping.value = false

  if (!listing.value) return
  const listed = listing.value.listingPrice
  const diff = listed - buyerOffer

  if (diff <= 10) {
    agreedPrice.value = buyerOffer
    messages.value.push({
      id: ++msgCounter,
      sender: 'seller',
      type: 'agreement',
      offerAmount: buyerOffer,
      text: `Deal agreed at $${buyerOffer}`,
      time: timestamp(),
    })
  } else {
    const counter = Math.round((listed + buyerOffer) / 2)
    messages.value.push({
      id: ++msgCounter,
      sender: 'seller',
      type: 'offer',
      offerAmount: counter,
      text: `Counter offer: $${counter}`,
      time: timestamp(),
    })
    messages.value.push({
      id: ++msgCounter,
      sender: 'seller',
      type: 'text',
      text: `How about $${counter}? That's my best offer given the condition.`,
      time: timestamp(),
    })
  }
  scrollToBottom()
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
