import apiClient from './client.js'

export async function getOccupancyForecast() {
  const response = await apiClient.get('/forecast/occupancy')
  return response.data
}