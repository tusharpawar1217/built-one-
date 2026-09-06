import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, FileText } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { queryDocuments } from '../api/query'
import type { QueryResponse } from '../types'

interface Message {
  role: 'user' | 'assistant'
  content: string
  citations?: any[]
  timestamp: Date
}

interface ChatInterfaceProps {
  userId: string
  selectedDocuments: string[]
}

export default function ChatInterface({ userId, selectedDocuments }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const queryMutation = useMutation({
    mutationFn: (query: string) =>
      queryDocuments(query, userId, selectedDocuments, messages),
    onSuccess: (data: QueryResponse) => {
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.answer,
        citations: data.citations,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, assistantMessage])
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || selectedDocuments.length === 0) return

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    queryMutation.mutate(input)
    setInput('')
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center text-center">
            <div>
              <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Ready to answer your questions
              </h3>
              <p className="text-sm text-gray-600 max-w-md">
                {selectedDocuments.length === 0
                  ? 'Select documents from the left sidebar to get started'
                  : 'Ask anything about your uploaded documents'}
              </p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message, idx) => (
              <div
                key={idx}
                className={`flex ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-4 ${
                    message.role === 'user'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  
                  {/* Citations */}
                  {message.citations && message.citations.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-300">
                      <p className="text-xs font-medium mb-2 text-gray-700">
                        Sources:
                      </p>
                      <div className="space-y-2">
                        {message.citations.slice(0, 3).map((citation, cidx) => (
                          <div
                            key={cidx}
                            className="text-xs bg-white p-2 rounded border border-gray-200"
                          >
                            <p className="font-medium text-gray-900">
                              {citation.document_name} - Page {citation.page_number}
                            </p>
                            <p className="text-gray-600 mt-1 line-clamp-2">
                              {citation.chunk_text}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <p className="text-xs mt-2 opacity-70">
                    {message.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
            
            {queryMutation.isPending && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg p-4">
                  <div className="flex items-center space-x-2">
                    <Loader2 className="w-4 h-4 animate-spin text-primary-600" />
                    <span className="text-sm text-gray-600">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Error Display */}
      {queryMutation.isError && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-800">
            Failed to get answer. Please try again.
          </p>
        </div>
      )}

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="flex items-end space-x-2">
        <div className="flex-1">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              selectedDocuments.length === 0
                ? 'Select documents first...'
                : 'Ask a question about your documents...'
            }
            disabled={selectedDocuments.length === 0 || queryMutation.isPending}
            className="input-field resize-none"
            rows={3}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSubmit(e)
              }
            }}
          />
        </div>
        <button
          type="submit"
          disabled={
            !input.trim() ||
            selectedDocuments.length === 0 ||
            queryMutation.isPending
          }
          className="btn-primary h-[76px] px-6"
        >
          <Send className="w-5 h-5" />
        </button>
      </form>
    </div>
  )
}
