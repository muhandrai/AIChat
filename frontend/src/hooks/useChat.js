import { useState, useRef, useCallback } from 'react'

const BACKEND_PORT = import.meta.env.VITE_BACKEND_PORT || '8000';
const API = `http://localhost:${BACKEND_PORT}`;

export function useChat() {
  const [chats, setChats] = useState([])          // [{id, title, message_count}]
  const [activeChatId, setActiveChatId] = useState(null)
  const [messages, setMessages] = useState([])    // [{role, content}]
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [streamingReasoning, setStreamingReasoning] = useState('')
  const [totalTokens, setTotalTokens] = useState(0)
  const abortRef = useRef(null)

  /* ── Load chat list ─────────────────────────────────────────────────────── */
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

  /* ── Load messages for a chat ───────────────────────────────────────────── */
  const loadMessages = useCallback(async (chatId) => {
    if (!chatId) return
    try {
      const res = await fetch(`${API}/api/chats/${chatId}/messages`)
      const data = await res.json()
      setMessages(data.messages || [])
      setActiveChatId(chatId)
      setStreamingContent('')
      setStreamingReasoning('')
    } catch (e) {
      console.error('loadMessages error', e)
    }
  }, [])

  /* ── Create new chat ────────────────────────────────────────────────────── */
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

  /* ── Delete chat ────────────────────────────────────────────────────────── */
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

  /* ── Send message (SSE stream) ──────────────────────────────────────────── */
  const sendMessage = useCallback(async (content, model, enableReasoning) => {
    if (!activeChatId || isStreaming) return

    // Optimistically add user message
    const userMsg = { role: 'user', content }
    setMessages(prev => [...prev, userMsg])
    setIsStreaming(true)
    setStreamingContent('')
    setStreamingReasoning('')

    const controller = new AbortController()
    abortRef.current = controller

    try {
      const res = await fetch(`${API}/api/chats/${activeChatId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, model, enable_reasoning: enableReasoning }),
        signal: controller.signal,
      })

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let accumulated = ''
      let accReasoning = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const raw = line.slice(6).trim()
          if (raw === '[DONE]') {
            // Commit final assistant message
            if (accumulated.trim()) {
              setMessages(prev => [...prev, { role: 'assistant', content: accumulated }])
            }
            setStreamingContent('')
            setStreamingReasoning('')
            await loadChats()
            break
          }
          try {
            const evt = JSON.parse(raw)
            if (evt.type === 'content') {
              accumulated += evt.content
              setStreamingContent(accumulated)
            } else if (evt.type === 'reasoning') {
              accReasoning += evt.content
              setStreamingReasoning(accReasoning)
            } else if (evt.type === 'usage') {
              setTotalTokens(parseInt(evt.content, 10) || 0)
            } else if (evt.type === 'title_update') {
              setChats(prev => prev.map(c => c.id === activeChatId ? { ...c, title: evt.content } : c))
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
        setMessages(prev => [...prev, { role: 'assistant', content: `⚠️ Connection error: ${e.message}` }])
      }
    } finally {
      setIsStreaming(false)
    }
  }, [activeChatId, isStreaming, loadChats])

  /* ── Upload file ────────────────────────────────────────────────────────── */
  const uploadFile = useCallback(async (file) => {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${API}/api/upload`, { method: 'POST', body: form })
    if (!res.ok) throw new Error('Upload failed')
    return await res.json() // {filename, content}
  }, [])

  /* ── Get models ─────────────────────────────────────────────────────────── */
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
    streamingContent, streamingReasoning, totalTokens,
    loadChats, loadMessages, createChat, deleteChat,
    sendMessage, uploadFile, getModels,
  }
}
