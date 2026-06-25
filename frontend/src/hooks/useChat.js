import { useState, useRef, useCallback } from 'react'

const API = ''

export function useChat() {
  const [chats, setChats] = useState([])
  const [activeChatId, setActiveChatId] = useState(null)
  const [messages, setMessages] = useState([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [isReasoning, setIsReasoning] = useState(false)
  const [totalTokens, setTotalTokens] = useState(0)
  const [usageDetails, setUsageDetails] = useState(null) // {total_tokens, prompt_tokens, completion_tokens}
  const abortRef = useRef(null)

  const loadChats = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/chats`)
      const data = await res.json()
      setChats(data.chats || [])
      return data.chats || []
    } catch (e) {
      console.error('loadChats error', e)
      return []
    }
  }, [])

  const loadMessages = useCallback(async (chatId) => {
    if (!chatId) return
    try {
      const res = await fetch(`${API}/api/chats/${chatId}/messages`)
      const data = await res.json()
      setMessages(data.messages || [])
      setActiveChatId(chatId)
      setStreamingContent('')
      setIsReasoning(false)
    } catch (e) {
      console.error('loadMessages error', e)
    }
  }, [])

  const createChat = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/chats`, { method: 'POST' })
      const data = await res.json()
      await loadChats()
      await loadMessages(data.chat_id)
      return data.chat_id
    } catch (e) {
      console.error('createChat error', e)
    }
  }, [loadChats, loadMessages])

  const deleteChat = useCallback(async (chatId) => {
    try {
      await fetch(`${API}/api/chats/${chatId}`, { method: 'DELETE' })
      const remaining = await loadChats()
      if (chatId === activeChatId) {
        if (remaining.length > 0) {
          await loadMessages(remaining[0].id)
        } else {
          const newChat = await createChat()
          await loadMessages(newChat)
        }
      }
    } catch (e) {
      console.error('deleteChat error', e)
    }
  }, [activeChatId, loadChats, loadMessages, createChat])

  const sendMessage = useCallback(async (content, model, reasoningEffort) => {
    if (!activeChatId || isStreaming) return

    const userMsg = { role: 'user', content }
    setMessages(prev => [...prev, userMsg])
    setIsStreaming(true)
    setStreamingContent('')
    setIsReasoning(false)
    setUsageDetails(null)

    const controller = new AbortController()
    abortRef.current = controller

    let accumulated = ''
    let completed = false

    try {
      const res = await fetch(`${API}/api/chats/${activeChatId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, model, reasoning_effort: reasoningEffort }),
        signal: controller.signal,
      })

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      reading: while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const raw = line.slice(6).trim()

          if (raw === '[DONE]') {
            completed = true
            break reading
          }

          try {
            const evt = JSON.parse(raw)

            if (evt.type === 'content') {
              accumulated += evt.content
              setStreamingContent(accumulated)
              // Konten mulai mengalir → reasoning selesai
              setIsReasoning(false)
            } else if (evt.type === 'reasoning') {
              // Status saja: model sedang bernalar (tanpa menampilkan isinya)
              setIsReasoning(true)
            } else if (evt.type === 'usage') {
              const u = evt.content
              setTotalTokens(u.total_tokens || 0)
              setUsageDetails(u)
            } else if (evt.type === 'title_update') {
              setChats(prev => prev.map(c =>
                c.id === activeChatId ? { ...c, title: evt.content } : c
              ))
            } else if (evt.type === 'error') {
              accumulated += `\n\n⚠️ Error: ${evt.content}`
              setStreamingContent(accumulated)
            }
          } catch { /* ignore parse errors */ }
        }
      }
    } catch (e) {
      if (e.name !== 'AbortError') {
        console.error('stream error', e)
        accumulated += `\n\n⚠️ Connection error: ${e.message}`
      }
    } finally {
      if (accumulated.trim()) {
        setMessages(prev => [...prev, { role: 'assistant', content: accumulated }])
      }
      setStreamingContent('')
      setIsReasoning(false)
      setIsStreaming(false)
      // Reconcile with DB after both clean completion and abort (backend persists partial)
      await loadChats()
    }
  }, [activeChatId, isStreaming, loadChats])

  const stopStreaming = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort()
      setIsStreaming(false)
    }
  }, [])

  const uploadFile = useCallback(async (file) => {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${API}/api/upload`, { method: 'POST', body: form })
    if (!res.ok) throw new Error('Upload failed')
    return await res.json()
  }, [])

  const getModels = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/models`)
      const data = await res.json()
      return data.models || []
    } catch {
      return []
    }
  }, [])

  return {
    chats, activeChatId, messages, isStreaming,
    streamingContent, isReasoning, totalTokens,
    usageDetails,
    loadChats, loadMessages, createChat, deleteChat,
    sendMessage, stopStreaming, uploadFile, getModels,
  }
}
