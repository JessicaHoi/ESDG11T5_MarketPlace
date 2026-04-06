/**
 * useNotifications.js
 * Singleton SSE notification composable.
 * Only ONE connection per receiverID is maintained across the entire app.
 * All components calling useNotifications(id) share the same reactive state.
 */
import { ref, computed } from 'vue'

// ── Singleton store — one entry per receiverID ────────────────────────────────
const store = {}  // { [receiverID]: { notifications, connected, eventSource, retryTimeout, retryDelay } }

function getOrCreate(receiverID) {
  if (store[receiverID]) return store[receiverID]

  const notifications = ref([])
  const connected     = ref(false)
  let eventSource     = null
  let retryTimeout    = null
  let retryDelay      = 2000

  function connect() {
    if (eventSource) eventSource.close()

    const url = `/sse/notification/stream?receiverID=${receiverID}`
    eventSource = new EventSource(url)

    eventSource.addEventListener('connected', () => {
      connected.value = true
      retryDelay      = 2000
      console.log(`[SSE] Connected as user ${receiverID}`)
    })

    eventSource.addEventListener('notification', (e) => {
      try {
        const data = JSON.parse(e.data)
        notifications.value.unshift({ ...data, read: false })
      } catch (err) {
        console.warn('[SSE] Could not parse notification:', e.data)
      }
    })

    eventSource.onerror = () => {
      connected.value = false
      eventSource.close()
      eventSource  = null
      retryDelay   = Math.min(retryDelay * 2, 30000)
      console.warn(`[SSE] Disconnected. Retrying in ${retryDelay / 1000}s...`)
      retryTimeout = setTimeout(connect, retryDelay)
    }
  }

  // Start immediately
  connect()

  const instance = {
    notifications,
    connected,
    unreadCount: computed(() => notifications.value.filter(n => !n.read).length),
    markAllRead() { notifications.value.forEach(n => { n.read = true }) },
    clearAll()   { notifications.value = [] },
  }

  store[receiverID] = instance
  return instance
}

export function useNotifications(receiverID) {
  if (!receiverID) {
    return {
      notifications: ref([]),
      connected:     ref(false),
      unreadCount:   computed(() => 0),
      markAllRead:   () => {},
      clearAll:      () => {},
    }
  }
  return getOrCreate(receiverID)
}
