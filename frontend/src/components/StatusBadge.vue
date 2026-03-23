<template>
  <span class="status-badge" :class="badgeClass">{{ label }}</span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: { type: String, required: true }
})

const config = {
  HELD:      { label: 'In Escrow',  class: 'bg-amber-100 text-amber-800' },
  RELEASED:  { label: 'Released',   class: 'bg-sage/20 text-sage' },
  FROZEN:    { label: 'Frozen',     class: 'bg-blue-100 text-blue-800' },
  REFUNDED:  { label: 'Refunded',   class: 'bg-purple-100 text-purple-800' },
  PENDING:   { label: 'Pending',    class: 'bg-amber-100 text-amber-800' },
  APPROVED:  { label: 'Approved',   class: 'bg-sage/20 text-sage' },
  REJECTED:  { label: 'Rejected',   class: 'bg-red-100 text-red-700' },
  Completed: { label: 'Completed',  class: 'bg-sage/20 text-sage' },
  'Dispute Raised': { label: 'Dispute', class: 'bg-red-100 text-red-700' },
  'Pending Delivery': { label: 'In Transit', class: 'bg-blue-100 text-blue-800' },
}

const badgeClass = computed(() => config[props.status]?.class || 'bg-gray-100 text-gray-600')
const label = computed(() => config[props.status]?.label || props.status)
</script>
