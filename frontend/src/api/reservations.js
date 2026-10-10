import apiClient from './client.js'

export async function createReservation(reservationData) {
  const response = await apiClient.post(
    '/reservations',
    reservationData,
  )

  return response.data
}

export async function assignReservationRoom(
  reservationId,
  roomId,
) {
  const response = await apiClient.post(
    `/reservations/${reservationId}/assign-room`,
    {
      room_id: roomId,
    },
  )

  return response.data
}

export async function checkInReservation(reservationId) {
  const response = await apiClient.post(
    `/reservations/${reservationId}/check-in`,
  )

  return response.data
}

export async function checkOutReservation(reservationId) {
  const response = await apiClient.post(
    `/reservations/${reservationId}/check-out`,
  )

  return response.data
}

export async function cancelReservation(reservationId) {
  const response = await apiClient.post(
    `/reservations/${reservationId}/cancel`,
  )

  return response.data
}