import api from './api.js'

const agentService = {
  /**
   * Send a message to the AI Agent.
   * @param {string} message - User's natural language message
   * @returns {Promise<Object>} Agent response with message, action, success, data, needs_confirmation
   */
  sendMessage: async (message) => {
    const response = await api.post('/agent/chat', { message })
    return response.data
  },

  /**
   * Clear the conversation history on the backend.
   * @returns {Promise<Object>} Confirmation message
   */
  clearConversation: async () => {
    const response = await api.post('/agent/clear')
    return response.data
  },
}

export default agentService
