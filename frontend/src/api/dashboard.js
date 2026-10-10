import apiClient from './client.js'

export async function getDashboardData(role) {
  const data = {
    rooms: [],
    reservations: [],
    tasks: [],
    guestRequests: [],
  }

  if (role === 'MANAGER' || role === 'FRONT_DESK') {
    const [
      roomsResponse,
      reservationsResponse,
      tasksResponse,
      guestRequestsResponse,
    ] = await Promise.all([
      apiClient.get('/rooms'),
      apiClient.get('/reservations'),
      apiClient.get('/tasks'),
      apiClient.get('/guest-requests'),
    ])

    data.rooms = roomsResponse.data
    data.reservations = reservationsResponse.data
    data.tasks = tasksResponse.data
    data.guestRequests = guestRequestsResponse.data

    return data
  }

  if (role === 'OPERATIONS') {
    const [
      roomsResponse,
      tasksResponse,
      guestRequestsResponse,
    ] = await Promise.all([
      apiClient.get('/rooms'),
      apiClient.get('/tasks'),
      apiClient.get('/guest-requests'),
    ])

    data.rooms = roomsResponse.data
    data.tasks = tasksResponse.data
    data.guestRequests = guestRequestsResponse.data

    return data
  }

  if (role === 'GUEST') {
    const [
      reservationsResponse,
      guestRequestsResponse,
    ] = await Promise.all([
      apiClient.get('/reservations'),
      apiClient.get('/guest-requests'),
    ])

    data.reservations = reservationsResponse.data
    data.guestRequests = guestRequestsResponse.data

    return data
  }

  return data
}