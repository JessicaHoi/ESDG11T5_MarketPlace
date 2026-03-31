<template>
  <div class="min-h-screen bg-paper">
    <Navbar :user="mockUser" />

    <div class="pt-16">
      <div class="max-w-4xl mx-auto px-6 pt-8">
        <button @click="$router.back()" class="section-label text-muted hover:text-accent transition-colors">← Back</button>
      </div>

      <div v-if="listing" class="max-w-4xl mx-auto px-6 py-6">
        <h1 class="font-display font-extrabold text-3xl mb-8">Complete Purchase</h1>

        <div v-if="apiError" class="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm font-mono">
          ⚠ {{ apiError }}
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-5 gap-8">
          <div class="lg:col-span-3 space-y-6">
            <div class="bg-white border border-ink/10 p-6">
              <p class="section-label mb-4">Contact Information</p>
              <div class="space-y-3">
                <input type="text" class="input-field" placeholder="Full name" v-model="contact.name" />
                <input type="email" class="input-field" placeholder="Email" v-model="contact.email" />
                <input type="tel" class="input-field" placeholder="Phone number" v-model="contact.phone" />
              </div>
            </div>

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

            <div class="bg-white border border-ink/10 p-6">
              <div class="flex items-center justify-between mb-4">
                <p class="section-label">Payment Details</p>
                <div class="flex gap-2 items-center">
                  <span class="text-xs font-mono text-muted">Powered by</span>
                  <span class="font-display font-bold text-sm text-purple-600">stripe</span>
                </div>
              </div>

              <div class="space-y-3">
                <div>
                  <label class="section-label block mb-2">Card Number</label>
                  <div class="input-field flex items-center justify-between">
                    <input v-model="cardNumber" type="text" class="flex-1 font-mono text-sm outline-none bg-transparent" placeholder="4242 4242 4242 4242" maxlength="19" />
                    <span class="text-muted text-lg">💳</span>
                  </div>
                </div>
                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label class="section-label block mb-2">Expiry Date</label>
                    <input type="text" class="input-field font-mono" placeholder="MM / YY" v-model="cardExpiry" maxlength="7" />
                  </div>
                  <div>
                    <label class="section-label block mb-2">CVC</label>
                    <input type="text" class="input-field font-mono" placeholder="•••" v-model="cardCvc" maxlength="4" />
                  </div>
                </div>
                <div>
                  <label class="section-label block mb-2">Name on Card</label>
                  <input type="text" class="input-field" placeholder="Full name" v-model="cardName" />
                </div>
              </div>

              <div class="mt-3 bg-amber-50 border border-amber-200 p-2 text-xs text-amber-700 font-mono">
                ℹ Demo mode: uses Stripe test card (pm_card_visa)
              </div>

              <div class="mt-4 bg-sage/5 border border-sage/20 p-3 flex gap-2">
                <span class="text-sage">🔒</span>
                <p class="text-xs text-slate leading-relaxed">
                  <strong class="font-display">Escrow Protection:</strong> Your ${{ totalAmount }} will be held securely.
                  Funds are only released to the seller once you confirm receipt.
                </p>
              </div>
            </div>

            <button @click="handlePayment" class="btn-primary w-full py-4 text-base" :disabled="processing">
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
                  <span class="font-mono">${{ negotiatedPrice || listing.price }}</span>
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
      <div class="bg-cream p-3 mb-6 text-left space-y-2">
        <div class="flex justify-between text-xs font-mono">
          <span class="text-muted">Order ID</span>
          <span class="text-ink">{{ orderResult?.orderID }}</span>
        </div>
        <div class="flex justify-between text-xs font-mono">
          <span class="text-muted">Payment ID</span>
          <span class="text-ink">{{ orderResult?.paymentID }}</span>
        </div>
      </div>
      <button @click="$router.push('/orders')" class="btn-primary w-full">View My Orders</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Navbar from '../../components/Navbar.vue'
import { mockUser } from '../../data/mockData.js'
import { placeOrder, fetchListingById } from '../../services/api.js'

const route = useRoute()
const router = useRouter()

const listing = ref(null)
const pageLoading = ref(true)
const apiError    = ref(null)

onMounted(async () => {
  try {
    const res = await fetchListingById(route.params.id)
    if (res && res.data && res.data.listingName) {
      const data = res.data
      listing.value = {
        id: data.listingID,
        title: data.listingName,
        price: data.listingPrice,
        condition: data.listingCategory || 'General',
        seller: 'External Seller',
        sellerId: 2, // Required mock for functioning checkout downstream
        image: data.listingImgUrl && data.listingImgUrl.length > 5 ? data.listingImgUrl : 'https://placehold.co/400x400/f2f2eb/1a1a1a?text=Product'
      }
    } else {
      apiError.value = "Product could not be found."
    }
  } catch (err) {
    apiError.value = "Failed to load product details from the server."
    console.error(err)
  } finally {
    pageLoading.value = false
  }
})

const negotiatedPrice = computed(() => route.query.price ? parseInt(route.query.price) : null)
const totalAmount = computed(() => {
  if (!listing.value) return 0
  const base = negotiatedPrice.value || listing.value.price
  return base + (delivery.value === 'shipping' ? 5 : 0)
})

const delivery   = ref('meetup')
const cardNumber = ref('')
const cardExpiry = ref('')
const cardCvc    = ref('')
const cardName   = ref('')
const contact    = ref({ name: mockUser.name, email: mockUser.email, phone: '' })

const processing  = ref(false)
const success     = ref(false)
const orderResult = ref(null)

const protections = [
  'Escrow payment protection',
  'Buyer guarantee on disputes',
  '48-hour seller response window',
  'Full refund if item not delivered',
]

async function handlePayment() {
  if (!listing.value) return
  apiError.value = null
  processing.value = true

  try {
    const STRIPE_TEST_PM = 'pm_card_visa'

    const result = await placeOrder({
      listingID:       listing.value.id,
      buyerID:         mockUser.id,
      sellerID:        listing.value.sellerId ?? 2,
      amount:          totalAmount.value,
      listingTitle:    listing.value.title,
      message:         `Hi! I'd like to purchase your ${listing.value.title}.`,
      paymentMethodID: STRIPE_TEST_PM,
    })

    orderResult.value = result
    success.value = true
  } catch (err) {
    apiError.value = err.message || 'Something went wrong. Please try again.'
  } finally {
    processing.value = false
  }
}
</script>
