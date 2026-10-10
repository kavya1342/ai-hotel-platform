import apiClient from './client.js'

export async function getCurrentUser() {
  const response = await apiClient.get('/auth/me')
  return response.data
}