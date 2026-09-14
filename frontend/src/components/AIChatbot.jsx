import { useState, useRef, useEffect } from 'react'
import { MessageCircle, X, Send, Trash2, Bot, Loader2, AlertCircle, ChevronRight, ChevronLeft } from 'lucide-react'
import agentService from '../services/agentService.js'

function AIChatbot() {
  const [isOpen, setIsOpen] = useState(true)
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      content: "Hello! I'm your AI Inventory Agent. I can help you manage products, check stock levels, and handle inventory operations.\n\nTry commands like:\n• \"Show all products\"\n• \"Add a new laptop\"\n• \"Which products need restocking?\"",
    },
  ])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Focus input when panel opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 200)
    }
  }, [isOpen])

  const handleSendMessage = async (text) => {
    const messageText = text || inputValue.trim()
    if (!messageText || isLoading) return

    setError(null)

    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: messageText,
    }
    setMessages((prev) => [...prev, userMsg])
    setInputValue('')
    setIsLoading(true)

    try {
      const response = await agentService.sendMessage(messageText)

      const assistantMsg = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.message,
        action: response.action,
        success: response.success,
        data: response.data,
        needsConfirmation: response.needs_confirmation,
        confirmationType: response.confirmation_type,
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch (err) {
      console.error('Agent error:', err)
      let errorMsg = 'Something went wrong. Please try again.'

      if (err.response?.status === 401) {
        errorMsg = 'Your session has expired. Please log in again.'
      } else if (err.response?.status === 403) {
        errorMsg = 'You do not have permission to perform this action.'
      } else if (err.response?.data?.detail) {
        errorMsg = err.response.data.detail
      } else if (err.message) {
        errorMsg = `Error: ${err.message}`
      }

      setError(errorMsg)
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: 'assistant',
          content: `⚠️ ${errorMsg}`,
          isError: true,
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleClearChat = async () => {
    try {
      await agentService.clearConversation()
    } catch {
      // Silently fail
    }
    setMessages([
      {
        id: Date.now(),
        role: 'assistant',
        content: "Chat history cleared. How can I help you with your inventory?",
      },
    ])
    setError(null)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const formatMessage = (content) => {
    if (!content) return null

    const lines = content.split('\n')
    return lines.map((line, i) => {
      line = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      if (line.startsWith('• ')) {
        return (
          <div key={i} className="flex items-start gap-2 ml-2">
            <span className="text-primary-500 mt-0.5">•</span>
            <span dangerouslySetInnerHTML={{ __html: line.slice(2) }} />
          </div>
        )
      }
      if (line.startsWith('- ')) {
        return (
          <div key={i} className="flex items-start gap-2 ml-2">
            <span className="text-gray-400 mt-0.5">-</span>
            <span dangerouslySetInnerHTML={{ __html: line.slice(2) }} />
          </div>
        )
      }
      if (/^\d+\.\s/.test(line)) {
        return (
          <div key={i} className="ml-2" dangerouslySetInnerHTML={{ __html: line }} />
        )
      }
      if (line.trim() === '') {
        return <div key={i} className="h-2" />
      }
      return (
        <div key={i} dangerouslySetInnerHTML={{ __html: line }} />
      )
    })
  }

  // Collapsed toggle button
  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="flex items-center gap-2 px-3 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors shadow-sm text-sm font-medium"
        title="Open AI Agent"
      >
        <MessageCircle className="h-4 w-4" />
        <span className="hidden xl:inline">AI Agent</span>
      </button>
    )
  }

  // Expanded inline chat panel
  return (
    <div className="flex flex-col h-full bg-white border-l border-gray-200 shadow-sm" style={{ width: '380px', minWidth: '380px' }}>
      {/* Header */}
      <div className="bg-primary-600 px-4 py-3 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center">
            <Bot className="h-4 w-4 text-white" />
          </div>
          <div>
            <h3 className="text-white font-semibold text-sm leading-tight">AI Inventory Agent</h3>
            <p className="text-primary-200 text-xs">Ask me anything</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={handleClearChat}
            className="text-primary-200 hover:text-white p-1.5 rounded-lg hover:bg-primary-500 transition-colors"
            title="Clear conversation"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="text-primary-200 hover:text-white p-1.5 rounded-lg hover:bg-primary-500 transition-colors"
            title="Collapse"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[88%] rounded-2xl px-3.5 py-2.5 ${
                msg.role === 'user'
                  ? 'bg-primary-600 text-white rounded-br-md'
                  : msg.isError
                    ? 'bg-red-50 text-red-800 border border-red-200 rounded-bl-md'
                    : 'bg-gray-100 text-gray-800 rounded-bl-md'
              }`}
            >
              {msg.role === 'assistant' && (
                <div className="flex items-center gap-1.5 mb-1">
                  <Bot className="h-3 w-3 text-primary-500 flex-shrink-0" />
                  <span className="text-xs font-medium text-primary-600">Agent</span>
                  {msg.isError && <AlertCircle className="h-3 w-3 text-red-500" />}
                </div>
              )}
              <div className="text-sm leading-relaxed whitespace-pre-wrap">
                {msg.role === 'assistant' ? formatMessage(msg.content) : msg.content}
              </div>
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-2xl rounded-bl-md px-3.5 py-2.5">
              <div className="flex items-center gap-2">
                <Bot className="h-3 w-3 text-primary-500" />
                <div className="flex items-center gap-1.5">
                  <Loader2 className="h-3.5 w-3.5 text-primary-500 animate-spin" />
                  <span className="text-xs text-gray-500">Thinking...</span>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-3 flex-shrink-0">
        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            disabled={isLoading}
            className="flex-1 px-3 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-colors disabled:opacity-50"
          />
          <button
            onClick={() => handleSendMessage()}
            disabled={!inputValue.trim() || isLoading}
            className="p-2 bg-primary-600 text-white rounded-xl hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  )
}

export default AIChatbot
