import { apiClient } from './client'

export interface ChatTestResponse {
  response: string
  conversation_id: string | null
  thread_id: string | null
  request_id: string | null
}

export async function sendTestMessage(message: string): Promise<ChatTestResponse> {
  const { data } = await apiClient.post<ChatTestResponse>('/chat/test', { message })
  return data
}
