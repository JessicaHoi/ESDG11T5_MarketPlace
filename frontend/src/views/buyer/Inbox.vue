<template>
  <div class="min-h-screen bg-paper">
    <Navbar :user="mockUser" />

    <div class="pt-16">
      <div class="bg-ink text-paper py-10 px-6">
        <div class="max-w-4xl mx-auto">
          <p class="section-label text-white/40 mb-2">Messages</p>
          <h1 class="font-display font-extrabold text-4xl">My Inbox</h1>
        </div>
      </div>

      <div class="max-w-4xl mx-auto px-6 py-8">
        <div v-if="loading" class="text-center py-20 text-muted font-mono text-sm">Loading conversations...</div>

        <template v-else>
          <div v-if="conversations.length === 0" class="text-center py-20">
            <p class="text-4xl mb-4">💬</p>
            <p class="font-display font-semibold text-xl text-ink/30">No conversations yet</p>
            <p class="text-muted font-mono text-sm mt-2">Start negotiating on a listing to begin a chat</p>
            <router-link to="/listings" class="btn-primary inline-block mt-4">Browse Listings</router-link>
          </div>

          <div v-else class="space-y-3">
            <div
              v-for="conv in conversations"
              :key="conv.listingID"
              @click="$router.push(`/messages/${conv.listingID}`)"
              class="bg-white border border-ink/10 p-5 hover:border-ink/30 transition-all cursor-pointer group flex items-center gap-4"
            >
              <!-- Avatar -->
              <div class="w-12 h-12 bg-ink flex items-center justify-center font-display font-bold text-sm flex-shrink-0 text-paper">
                S
              </div>

              <!-- Content -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between gap-2 mb-1">
                  <p class="font-display font-semibold text-sm group-hover:text-accent transition-colors truncate">
                    {{ conv.title }}
                  </p>
                  <p class="text-xs text-muted font-mono flex-shrink-0">{{ conv.time }}</p>
                </div>
                <p class="text-xs text-slate font-mono truncate">{{ conv.lastMessage }}</p>
              </div>

              <!-- Unread dot if last message is from seller -->
              <div v-if="conv.lastSenderID !== mockUser.id" class="w-2 h-2 bg-accent rounded-full flex-shrink-0"></div>
              <span v-else class="text-muted group-hover:text-accent transition-colors text-sm flex-shrink-0">→</span>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Navbar from '../../components/Navbar.vue'
import { mockUser } from '../../data/mockData.js'
import { getMessagesByReceiver, fetchListings } from '../../services/api.js'

const loading       = ref(true)
const conversations = ref([])

onMounted(async () => {
  try {
    // Fetch all messages where buyer is the receiver OR sender
    const [receivedData, listingsData] = await Promise.all([
      getMessagesByReceiver(mockUser.id).catch(() => []),
      fetchListings().catch(() => null),
    ])

    const listings = listingsData?.data?.listings ?? listingsData?.listings ?? []
    const listingMap = {}
    listings.forEach(l => { listingMap[l.listingID] = l })

    // Group messages by orderID (which is the listingID for pre-purchase chats)
    const received = Array.isArray(receivedData) ? receivedData : []

    // Build a map of listingID → last message
    const convMap = {}
    received.forEach(msg => {
      const key = msg.orderID
      if (!convMap[key] || new Date(msg.sentAt) > new Date(convMap[key].sentAt)) {
        convMap[key] = msg
      }
    })

    // Build conversation list
    conversations.value = Object.entries(convMap)
      .map(([listingID, lastMsg]) => {
        const listing = listingMap[parseInt(listingID)]
        return {
          listingID:    parseInt(listingID),
          title:        listing?.listingName ?? `Listing #${listingID}`,
          lastMessage:  lastMsg.content || 'No messages',
          lastSenderID: lastMsg.senderID,
          time:         lastMsg.sentAt
            ? new Date(lastMsg.sentAt).toLocaleDateString('en-SG', { day: 'numeric', month: 'short' })
            : '',
          sentAt: lastMsg.sentAt,
        }
      })
      .sort((a, b) => new Date(b.sentAt) - new Date(a.sentAt))  // newest first

  } catch (err) {
    console.error('Failed to load inbox:', err)
  } finally {
    loading.value = false
  }
})
</script>
