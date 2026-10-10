import apiClient from './client.js'

export async function createTask(taskData) {
  const response = await apiClient.post('/tasks', taskData)

  return response.data
}

export async function assignTask(taskId, assignedTo) {
  const response = await apiClient.post(
    `/tasks/${taskId}/assign`,
    {
      assigned_to: assignedTo,
    },
  )

  return response.data
}

export async function startTask(taskId) {
  const response = await apiClient.post(
    `/tasks/${taskId}/start`,
  )

  return response.data
}

export async function completeTask(taskId, completionNotes) {
  const response = await apiClient.post(
    `/tasks/${taskId}/complete`,
    {
      completion_notes: completionNotes,
    },
  )

  return response.data
}