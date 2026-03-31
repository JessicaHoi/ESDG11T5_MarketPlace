/**
 * api.js — Centralised API service layer
 */

const BASE = '/api'

async function request(method, path, body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  }
  if (body) opts.body = JSON.stringify(body)

  const res = await fetch(`${BASE}${path}`, opts)
  const data = await res.json().catch(() => ({}))

  if (!res.ok) {
    // Show full backend error so we can see exactly which field is missing
    const msg = data?.message || data?.detail || JSON.stringify(data) || `HTTP ${res.status}`
    throw new Error(msg)
  }
  return data
}

const get   = (path)        => request('GET',   path)
const post  = (path, body)  => request('POST',  path, body)
const put   = (path, body)  => request('PUT',   path, body)
const patch = (path, body)  => request('PATCH', path, body)

// ─── COMPOSITE: Place Order ──────────────────────────────────────────────────
export function placeOrder(payload) {
  return post('/placeorder', payload)
}

// ─── COMPOSITE: Raise Dispute ────────────────────────────────────────────────
export function raiseDispute(payload) {
  return post('/raise-dispute', payload)
}

export function approveEvidence(disputeID, evidenceID) {
  return put(`/raise-dispute/${disputeID}/approve-evidence/${evidenceID}`)
}

export function resolveDispute(disputeID, orderID) {
  return post(`/raise-dispute/${disputeID}/resolve`, { orderID })
}

// ─── ATOMIC: Orders ──────────────────────────────────────────────────────────
export function getOrders() {
  return get('/orders')
}

export function getOrder(orderID) {
  return get(`/orders/${orderID}`)
}

export function confirmOrder(orderID) {
  return put(`/orders/${orderID}/confirm`)
}

export function updateOrder(orderID, fields) {
  return put(`/orders/${orderID}`, fields)
}

// ─── ATOMIC: Payment ─────────────────────────────────────────────────────────
export function holdPayment({ orderID, amount, paymentMethodID }) {
  return post('/payment/escrow', { orderID, amount, paymentMethodID })
}

export function releasePayment(orderID) {
  return post('/payment/release', { orderID })
}

export function freezePayment(paymentID) {
  return patch(`/payment/${paymentID}/freeze`)
}

export function refundPayment(orderID) {
  return post('/payment/refund', { orderID })
}

export function getAllPayments() {
  return get('/payment')
}

// ─── ATOMIC: Messaging ───────────────────────────────────────────────────────
export function sendMessage({ orderID, senderID, receiverID, content, receiverPhone }) {
  return post('/messages', { orderID, senderID, receiverID, content, receiverPhone })
}

export function getMessage(messageID) {
  return get(`/messages/${messageID}`)
}

// ─── ATOMIC: Notifications ───────────────────────────────────────────────────
export function getNotification(notificationID) {
  return get(`/notification/${notificationID}`)
}

export function sendNotification({ orderID, disputeID, notification, receiverID }) {
  return post('/notification', { orderID, disputeID, notification, receiverID })
}

// ─── ATOMIC: Dispute ─────────────────────────────────────────────────────────
export function getDisputes() {
  return get('/dispute')
}

export function getDispute(disputeID) {
  return get(`/dispute/${disputeID}`)
}

// ─── EXTERNAL: Listing Service (OutSystems) ──────────────────────────────────
export async function fetchListings() {
  const res = await fetch('https://personal-8vnud50n.outsystemscloud.com/Listing/rest/Listing/listing/')
  if (!res.ok) throw new Error(`Listing API HTTP ${res.status}`)
  return res.json()
}

export async function fetchListingById(listingID) {
  const res = await fetch(`https://personal-8vnud50n.outsystemscloud.com/Listing/rest/Listing/listing/${listingID}/`)
  if (!res.ok) throw new Error(`Listing API HTTP ${res.status}`)
  return res.json()
}
