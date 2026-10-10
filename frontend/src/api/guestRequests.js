import apiClient from './client.js'

export async function createGuestRequest(requestData) {
  const response = await apiClient.post(
    '/guest-requests',
    requestData,
  )

  return response.data
}

export async function assignGuestRequest(requestId, assignedTo) {
  const response = await apiClient.post(
    `/guest-requests/${requestId}/assign`,
    {
      assigned_to: assignedTo,
    },
  )

  return response.data
}

export async function startGuestRequest(requestId) {
  const response = await apiClient.post(
    `/guest-requests/${requestId}/start`,
  )

  return response.data
}

export async function resolveGuestRequest(
  requestId,
  resolutionNotes,
) {
  const response = await apiClient.post(
    `/guest-requests/${requestId}/resolve`,
    {
      resolution_notes: resolutionNotes,
    },
  )

  return response.data
}