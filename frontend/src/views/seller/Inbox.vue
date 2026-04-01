<template>
  <div class="min-h-screen bg-paper">
    <SellerNavbar :seller="mockSeller" />

    <div class="pt-16">
      <div class="bg-ink text-paper py-10 px-6">
        <div class="max-w-3xl mx-auto">
          <p class="section-label text-white/40 mb-2">{{ threads.length }} conversation{{ threads.length !== 1 ? 's' : '' }}</p>
          <h1 class="font-display font-extrabold text-4xl">Inbox</h1>
        </div>
      </div>

      <div class="max-w-3xl mx-auto px-6 py-8">

        <div v-if="loading" class="text-center py-20 text-muted font-mono text-sm">
          Loading messages...
        </div>

        <div v-else-if="threads.length === 0" class="text-center py-20">
          <p class="font-display font-semibold text-2xl text-ink/30">No messages yet</p>
          <p class="text-muted font-mono text-sm mt-2">Buyers will appear here when they message you</p>
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="thread in threads"
            :key="thread.listingID"
            class="bg-white border border-ink/10 p-5 hover:border-ink/30 transition-all cursor-pointer group"
            @click="openThread(thread)"
          >
            <div class="flex items-center gap-4">
              <!-- Listing image -->
              <div class="w-14 h-14 bg-cream overflow-hidden flex-shrink-0 flex items-center justify-center">
                <img
                  v-if="listingImages[thread.listingID]"
                  :src="listingImages[thread.listingID]"
                  class="w-full h-full object-cover"
                />
                <span v-else class="text-2xl">🛍</span>
              </div>

              <!-- Thread info -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between mb-1">
                  <p class="font-display font-semibold text-sm group-hover:text-accent transition-colors">
                    {{ listingNames[thread.listingID] || `Listing #${thread.listingID}` }}
                  </p>
                  <p class="text-xs text-muted font-mono flex-shrink-0 ml-4">{{ thread.lastTime }}</p>
                </div>
                <p class="text-xs text-muted font-mono mb-1">
                  {{ thread.messageCount }} message{{ thread.messageCount !== 1 ? 's' : '' }}
                  · Buyer #{{ thread.buyerID }}
                </p>
                <p class="text-sm text-slate truncate">{{ thread.lastMessage }}</p>
              </div>

              <!-- Unread indicator -->
              <div
                v-if="thread.hasUnread"
                class="w-2 h-2 bg-accent rounded-full flex-shrink-0"
              ></div>
              <span class="text-muted group-hover:text-accent transition-colors ml-1 flex-shrink-0">→</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import SellerNavbar from '../../components/SellerNavbar.vue'
import { mockSeller } from '../../data/mockData.js'
import { getMessagesByReceiver } from '../../services/api.js'

const router  = useRouter()
const loading = ref(true)
const allMessages   = ref([])
const listingImages = ref({})
const listingNames  = ref({})

// Group messages by orderID (which equals listingID for pre-order conversations)
const threads = computed(() => {
  const groups = {}

  allMessages.value.forEach(msg => {
    const key = `order_${msg.orderID}`
    if (!groups[key]) {
      groups[key] = {
        key,
        listingID:    msg.orderID,  // orderID == listingID for pre-order messages
        buyerID:      msg.senderID,
        orderID:      msg.orderID,
        messages:     [],
        lastMessage:  '',
        lastTime:     '',
        messageCount: 0,
        hasUnread:    false,
      }
    }
    groups[key].messages.push(msg)
  })

  return Object.values(groups).map(group => {
    group.messages.sort((a, b) => new Date(a.sentAt) - new Date(b.sentAt))
    const last = group.messages[group.messages.length - 1]
    group.lastMessage  = last.content
    group.messageCount = group.messages.length
    group.lastTime     = last.sentAt
      ? new Date(last.sentAt).toLocaleTimeString('en-SG', { hour: '2-digit', minute: '2-digit' })
      : ''
    return group
  }).sort((a, b) => new Date(b.messages[b.messages.length - 1].sentAt) - new Date(a.messages[a.messages.length - 1].sentAt))
})

function openThread(thread) {
  // Route to seller messages using orderID (= listingID) as the conversation key
  router.push(`/seller/inbox/${thread.orderID}`)
}

onMounted(async () => {
  try {
    const [messagesData, listingsData] = await Promise.all([
      getMessagesByReceiver(mockSeller.id),
      fetch('/tmp.json').then(r => r.json()).catch(() => null),
    ])

    allMessages.value = Array.isArray(messagesData) ? messagesData : []

    const listings = listingsData?.data?.listings ?? []
    listings.forEach(l => {
      if (l.listingImgUrl && l.listingImgUrl.length > 5) {
        listingImages.value[l.listingID] = l.listingImgUrl
      }
      listingNames.value[l.listingID] = l.listingName
    })
  } catch (err) {
    console.error('Failed to load inbox:', err)
  } finally {
    loading.value = false
  }
})
</script>
