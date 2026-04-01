/**
 * negotiationStore.js
 * Stores agreed negotiation prices in localStorage keyed by listingID.
 * This is a frontend-only solution that bridges the buyer and seller
 * without requiring backend schema changes.
 */

const KEY_PREFIX = 'tradenest_deal_'

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
