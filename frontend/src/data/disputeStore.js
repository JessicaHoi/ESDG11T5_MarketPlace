/**
 * disputeStore.js
 * Lightweight localStorage-backed store for disputes raised during this session.
 * Merges with mockDisputes so the admin pages always have a complete, up-to-date list.
 */

const STORAGE_KEY = 'tradenest_disputes'

export function saveDispute(dispute) {
  const existing = loadLocalDisputes()
  // Replace if same id already exists, otherwise prepend
  const idx = existing.findIndex(d => d.id === dispute.id)
  if (idx !== -1) {
    existing[idx] = dispute
  } else {
    existing.unshift(dispute)
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(existing))
}

export function loadLocalDisputes() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
  } catch {
    return []
  }
}

export function updateDisputeStatus(id, status, mockDisputes = []) {
  const existing = loadLocalDisputes()
  const idx = existing.findIndex(d => d.id === id)
  if (idx !== -1) {
    // Already in localStorage — just update status
    existing[idx] = { ...existing[idx], status }
  } else {
    // Not in localStorage yet — it's a seeded mock dispute.
    // Copy it in so the update persists.
    const seed = mockDisputes.find(d => d.id === id)
    if (seed) {
      existing.unshift({ ...seed, status })
    }
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(existing))
}

/**
 * Update the seller's response text on a dispute.
 * If the dispute isn't in localStorage yet (it's a mock), copy it in first.
 */
export function updateSellerResponse(id, responseText, mockDisputes = []) {
  const existing = loadLocalDisputes()
  const idx = existing.findIndex(d => d.id === id)
  if (idx !== -1) {
    existing[idx] = { ...existing[idx], sellerResponse: responseText }
  } else {
    const seed = mockDisputes.find(d => d.id === id)
    if (seed) {
      existing.unshift({ ...seed, sellerResponse: responseText })
    }
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(existing))
}

/**
 * Merge mockDisputes with localStorage disputes.
 * localStorage disputes take priority (they are newer / user-raised).
 */
export function getMergedDisputes(mockDisputes) {
  const local = loadLocalDisputes()
  const localIds = new Set(local.map(d => d.id))
  // Keep mock disputes that haven't been overridden by a local one
  const filtered = mockDisputes.filter(d => !localIds.has(d.id))
  return [...local, ...filtered]
}

/**
 * Given a numeric orderID, find its dispute and return the resolved order status.
 * APPROVED dispute → order should show as REFUNDED
 * REJECTED dispute → order should show as COMPLETED (funds released to seller)
 * PENDING dispute  → order stays DISPUTED
 * No dispute found → returns null (no override needed)
 */
export function getOrderStatusFromDispute(orderID) {
  const all = loadLocalDisputes()
  // Dispute orderID is stored as "ORD-{id}" string
  const dispute = all.find(d => d.orderID === `ORD-${orderID}`)
  if (!dispute) return null
  if (dispute.status === 'APPROVED') return 'REFUNDED'
  if (dispute.status === 'REJECTED') return 'COMPLETED'
  return null // PENDING — no change yet
}
