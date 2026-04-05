<template>
  <div class="relative" ref="bellRef">
    <!-- Bell button -->
    <button
      @click="toggleOpen"
      class="relative flex items-center justify-center w-9 h-9 hover:bg-ink/10 transition-colors"
      :title="connected ? 'Notifications (live)' : 'Notifications (reconnecting...)'"
    >
      <span class="text-lg">🔔</span>
      <!-- Unread badge -->
      <span
        v-if="unreadCount > 0"
        class="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 text-white text-xs font-bold flex items-center justify-center rounded-full leading-none"
      >{{ unreadCount > 9 ? '9+' : unreadCount }}</span>
      <!-- Connection status dot -->
      <span
        class="absolute bottom-0.5 right-0.5 w-2 h-2 rounded-full border border-white"
        :class="connected ? 'bg-sage' : 'bg-amber-400'"
      ></span>
    </button>

    <!-- Dropdown -->
    <transition name="notif-drop">
      <div
        v-if="isOpen"
        class="absolute right-0 mt-2 w-80 bg-paper border border-ink/10 shadow-xl z-50"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-4 py-3 border-b border-ink/10">
          <span class="font-display font-semibold text-sm">Notifications</span>
          <div class="flex items-center gap-3">
            <button
              v-if="notifications.length > 0"
              @click="markAllRead"
              class="text-xs text-muted hover:text-accent transition-colors font-mono"
            >Mark all read</button>
            <button
              v-if="notifications.length > 0"
              @click="clearAll"
              class="text-xs text-muted hover:text-red-500 transition-colors font-mono"
            >Clear</button>
          </div>
        </div>

        <!-- Notification list -->
        <div class="max-h-80 overflow-y-auto">
          <div v-if="notifications.length === 0" class="px-4 py-8 text-center">
            <p class="text-2xl mb-2">🔔</p>
            <p class="text-muted font-mono text-xs">No notifications yet</p>
          </div>

          <div
            v-for="notif in notifications"
            :key="notif.notificationID"
            class="px-4 py-3 border-b border-ink/5 hover:bg-cream/50 transition-colors cursor-pointer"
            :class="{ 'bg-accent/5': !notif.read }"
            @click="notif.read = true"
          >
            <div class="flex items-start gap-2">
              <span class="flex-shrink-0 mt-0.5">
                {{ notifIcon(notif.notification) }}
              </span>
              <div class="flex-1 min-w-0">
                <p class="text-xs text-ink leading-relaxed">{{ notif.notification }}</p>
                <p class="text-xs text-muted font-mono mt-1">{{ formatTime(notif.sentAt) }}</p>
              </div>
              <span v-if="!notif.read" class="w-2 h-2 bg-accent rounded-full flex-shrink-0 mt-1"></span>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="px-4 py-2 border-t border-ink/10 flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full" :class="connected ? 'bg-sage' : 'bg-amber-400'"></span>
          <span class="text-xs text-muted font-mono">{{ connected ? 'Live updates active' : 'Reconnecting...' }}</span>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useNotifications } from '../composables/useNotifications.js'

const props = defineProps({
  receiverID: { type: Number, required: true }
})

const isOpen  = ref(false)
const bellRef = ref(null)

// Uses singleton — same connection shared across all components
const { notifications, unreadCount, connected, markAllRead, clearAll } = useNotifications(props.receiverID)

function toggleOpen() {
  isOpen.value = !isOpen.value
  if (isOpen.value) markAllRead()
}

// Close on click outside
function handleClickOutside(e) {
  if (bellRef.value && !bellRef.value.contains(e.target)) {
    isOpen.value = false
  }
}

onMounted(() => document.addEventListener('click', handleClickOutside))
onUnmounted(() => document.removeEventListener('click', handleClickOutside))

function notifIcon(text) {
  if (!text) return '📢'
  const t = text.toLowerCase()
  if (t.includes('dispute'))  return '⚠️'
  if (t.includes('approved')) return '✅'
  if (t.includes('rejected')) return '❌'
  if (t.includes('payment') || t.includes('paid')) return '💰'
  if (t.includes('refund'))   return '↩️'
  if (t.includes('receipt') || t.includes('confirmed')) return '✅'
  if (t.includes('message') || t.includes('negotiat')) return '💬'
  return '🔔'
}

function formatTime(iso) {
  if (!iso) return ''
  // sentAt is stored as UTC in MySQL — append 'Z' so JS parses it as UTC, not local time
  const utcStr = iso.includes('T') || iso.endsWith('Z') ? iso : iso.replace(' ', 'T') + 'Z'
  const d = new Date(utcStr)
  const now = new Date()
  const diffMs = now - d
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1)  return 'Just now'
  if (diffMin < 60) return `${diffMin}m ago`
  const diffHr = Math.floor(diffMin / 60)
  if (diffHr < 24)  return `${diffHr}h ago`
  return d.toLocaleDateString('en-SG', { day: 'numeric', month: 'short' })
}
</script>

<style scoped>
.notif-drop-enter-active,
.notif-drop-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.notif-drop-enter-from,
.notif-drop-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
