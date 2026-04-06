<template>
  <router-view></router-view>
</template>

<script setup>
import { useNotifications } from './composables/useNotifications.js'
import { mockUser, mockSeller, mockAdmin } from './data/mockData.js'

// Pre-warm all three SSE connections on app start.
// Each is a singleton — calling useNotifications() again from any
// component (e.g. NotificationBell) returns the same shared instance.
useNotifications(mockUser.id)    // buyer  (id: 1)
useNotifications(mockSeller.id)  // seller (id: 2)
useNotifications(mockAdmin.id)   // admin  (id: 99)
</script>
