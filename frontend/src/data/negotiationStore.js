/**
 * negotiationStore.js
 * Stores agreed negotiation prices and quantity offsets in localStorage keyed by listingID.
 * This is a frontend-only solution that bridges the buyer and seller
 * without requiring backend schema changes.
 */

const KEY_PREFIX     = 'ouimarche_deal_'
const QTY_PREFIX     = 'ouimarche_qty_'

// ─── Deal (negotiated price) ──────────────────────────────────────────────────

export function saveDeal(listingID, price) {
  localStorage.setItem(`${KEY_PREFIX}${listingID}`, JSON.stringify({
    price:     parseFloat(price),
    agreedAt:  new Date().toISOString(),
    listingID: parseInt(listingID),
  }))
}

export function getDeal(listingID) {
  try {
    const raw = localStorage.getItem(`${KEY_PREFIX}${listingID}`)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function clearDeal(listingID) {
  localStorage.removeItem(`${KEY_PREFIX}${listingID}`)
}

// ─── Quantity offset (how many have been purchased locally) ──────────────────

export function decrementQty(listingID) {
  const current = getQtyOffset(listingID)
  localStorage.setItem(`${QTY_PREFIX}${listingID}`, current + 1)
}

export function getQtyOffset(listingID) {
  return parseInt(localStorage.getItem(`${QTY_PREFIX}${listingID}`) || '0')
}

export function resetQty(listingID) {
  localStorage.removeItem(`${QTY_PREFIX}${listingID}`)
}
