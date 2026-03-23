<template>
  <div class="min-h-screen bg-paper">
    <Navbar :user="mockUser" />

    <div class="pt-16">
      <!-- Back always visible -->
      <div class="max-w-4xl mx-auto px-6 pt-8">
        <button @click="$router.back()" class="section-label text-muted hover:text-accent transition-colors">← Back</button>
      </div>

      <div v-if="listing" class="max-w-4xl mx-auto px-6 py-6">
        <h1 class="font-display font-extrabold text-3xl mb-8">Complete Purchase</h1>

        <div class="grid grid-cols-1 lg:grid-cols-5 gap-8">
          <!-- Payment form -->
          <div class="lg:col-span-3 space-y-6">
            <!-- Contact -->
            <div class="bg-white border border-ink/10 p-6">
              <p class="section-label mb-4">Contact Information</p>
              <div class="space-y-3">
                <input type="text" class="input-field" placeholder="Full name" value="Mark Foo" />
                <input type="email" class="input-field" placeholder="Email" value="mark@tradenest.sg" />
                <input type="tel" class="input-field" placeholder="Phone number" value="+65 9123 4567" />
              </div>
            </div>

            <!-- Delivery -->
            <div class="bg-white border border-ink/10 p-6">
              <p class="section-label mb-4">Meetup / Delivery Preference</p>
              <div class="space-y-2">
                <label class="flex items-center gap-3 p-3 border border-ink/10 cursor-pointer hover:border-accent/40 transition-colors" :class="{ 'border-accent bg-accent/5': delivery === 'meetup' }">
                  <input type="radio" v-model="delivery" value="meetup" class="accent-accent" />
                  <div>
                    <p class="font-display font-semibold text-sm">Self-Collection / Meetup</p>
                    <p class="text-xs text-muted font-mono">Arrange with seller directly</p>
                  </div>
                </label>
                <label class="flex items-center gap-3 p-3 border border-ink/10 cursor-pointer hover:border-accent/40 transition-colors" :class="{ 'border-accent bg-accent/5': delivery === 'shipping' }">
                  <input type="radio" v-model="delivery" value="shipping" class="accent-accent" />
                  <div>
                    <p class="font-display font-semibold text-sm">Shipping (+$5.00)</p>
                    <p class="text-xs text-muted font-mono">Delivered to your address</p>
                  </div>
                </label>
              </div>
            </div>

            <!-- Payment details -->
            <div class="bg-white border border-ink/10 p-6">
              <div class="flex items-center justify-between mb-4">
                <p class="section-label">Payment Details</p>
                <div class="flex gap-2 items-center">
                  <span class="text-xs font-mono text-muted">Powered by</span>
                  <span class="font-display font-bold text-sm text-purple-600">stripe</span>
                </div>
              </div>

              <!-- Mock Stripe card element -->
              <div class="space-y-3">
                <div>
                  <label class="section-label block mb-2">Card Number</label>
                  <div class="input-field flex items-center justify-between">
                    <input
                      v-model="cardNumber"
                      type="text"
                      class="flex-1 font-mono text-sm outline-none bg-transparent"
                      placeholder="4242 4242 4242 4242"
                      maxlength="19"
                    />
                    <span class="text-muted text-lg">💳</span>
                  </div>
                  <div class="flex gap-1 mt-1">
                    <span v-for="brand in ['visa', 'mc', 'amex']" :key="brand"
                      class="text-xs font-mono border border-ink/10 px-1.5 py-0.5 text-muted"
                    >{{ brand.toUpperCase() }}</span>
                  </div>
                </div>

                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label class="section-label block mb-2">Expiry Date</label>
                    <input type="text" class="input-field font-mono" placeholder="MM / YY"/>
                  </div>
                  <div>
                    <label class="section-label block mb-2">CVC</label>
                    <input type="text" class="input-field font-mono" placeholder="•••"/>
                  </div>
                </div>

                <div>
                  <label class="section-label block mb-2">Name on Card</label>
                  <input type="text" class="input-field" placeholder="Full name" value="Mark Foo" />
                </div>
              </div>

              <!-- Escrow notice -->
              <div class="mt-4 bg-sage/5 border border-sage/20 p-3 flex gap-2">
                <span class="text-sage">🔒</span>
                <p class="text-xs text-slate leading-relaxed">
                  <strong class="font-display">Escrow Protection:</strong> Your ${{ totalAmount }} will be held securely.
                  Funds are only released to the seller once you confirm receipt.
                </p>
              </div>
            </div>

            <!-- Pay button -->
            <button
              @click="handlePayment"
              class="btn-primary w-full py-4 text-base"
              :disabled="processing"
            >
              <span v-if="processing" class="flex items-center justify-center gap-2">
                <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                Processing...
              </span>
              <span v-else>Pay ${{ totalAmount }} — Hold in Escrow</span>
            </button>
          </div>

          <!-- Order summary -->
          <div class="lg:col-span-2">
            <div class="bg-white border border-ink/10 p-6 sticky top-24">
              <p class="section-label mb-4">Order Summary</p>

              <div v-if="negotiatedPrice && negotiatedPrice !== listing.price" class="bg-sage/10 border border-sage/20 px-3 py-2 mb-3 flex items-center gap-2">
                <span class="text-sage text-sm">🤝</span>
                <p class="text-xs text-sage font-mono">Negotiated: ${{ negotiatedPrice }} <span class="line-through text-muted">${{ listing.price }}</span></p>
              </div>

              <div class="flex gap-3 mb-4">
                <div class="w-16 h-16 bg-cream overflow-hidden flex-shrink-0">
                  <img :src="listing.image" :alt="listing.title" class="w-full h-full object-cover" />
                </div>
                <div>
                  <p class="font-display font-semibold text-sm leading-tight">{{ listing.title }}</p>
                  <p class="text-xs text-muted font-mono mt-1">{{ listing.condition }} · {{ listing.seller }}</p>
                </div>
              </div>

              <div class="border-t border-ink/10 pt-4 space-y-2">
                <div class="flex justify-between text-sm">
                  <span class="text-slate">Item price</span>
                  <span class="font-mono">${{ listing.price }}</span>
                </div>
                <div class="flex justify-between text-sm" v-if="delivery === 'shipping'">
                  <span class="text-slate">Shipping</span>
                  <span class="font-mono">$5.00</span>
                </div>
                <div class="flex justify-between text-sm text-muted">
                  <span>Escrow fee</span>
                  <span class="font-mono">$0.00</span>
                </div>
              </div>

              <div class="border-t border-ink/10 pt-4 mt-4 flex justify-between">
                <span class="font-display font-bold">Total</span>
                <span class="font-display font-bold text-accent">${{ totalAmount }}</span>
              </div>

              <div class="mt-4 pt-4 border-t border-ink/10">
                <p class="section-label mb-2">Protected by TradeNest</p>
                <ul class="space-y-1">
                  <li v-for="item in protections" :key="item" class="text-xs text-slate flex items-center gap-2">
                    <span class="text-sage">✓</span>{{ item }}
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div v-if="success" class="fixed inset-0 bg-ink/60 flex items-center justify-center z-50 p-6">
    <div class="bg-paper max-w-sm w-full p-8 text-center">
      <div class="w-16 h-16 bg-sage/20 flex items-center justify-center mx-auto mb-4 text-3xl">✓</div>
      <h2 class="font-display font-extrabold text-2xl mb-2">Payment Held!</h2>
      <p class="text-slate text-sm mb-6 leading-relaxed">
        Your ${{ totalAmount }} has been securely held in escrow.
        The seller will now arrange delivery with you.
      </p>
      <div class="bg-cream p-3 mb-6 text-left">
        <p class="section-label mb-1">Payment Intent ID</p>
        <p class="font-mono text-xs text-slate break-all">pi_3TDk0lRyvvjJItIf_mock_{{ Date.now() }}</p>
      </div>
      <button @click="$router.push('/orders')" class="btn-primary w-full">View My Orders</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watchEffect } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Navbar from '../../components/Navbar.vue'
import { mockListings, mockUser } from '../../data/mockData.js'

const route = useRoute()
const router = useRouter()

const listing = ref(null)

watchEffect(() => {
  listing.value = mockListings.find(l => l.id === parseInt(route.params.id)) || null
})

const negotiatedPrice = computed(() => route.query.price ? parseInt(route.query.price) : null)

const delivery = ref('meetup')
const cardFocused = ref(false)
const cardNumber = ref('')
const processing = ref(false)
const success = ref(false)

const totalAmount = computed(() => {
  if (!listing.value) return 0
  const base = negotiatedPrice.value || listing.value.price
  return base + (delivery.value === 'shipping' ? 5 : 0)
})

const protections = [
  'Escrow payment protection',
  'Buyer guarantee on disputes',
  '48-hour seller response window',
  'Full refund if item not delivered',
]

async function handlePayment() {
  processing.value = true
  await new Promise(r => setTimeout(r, 2000))
  processing.value = false
  success.value = true
}
</script>
