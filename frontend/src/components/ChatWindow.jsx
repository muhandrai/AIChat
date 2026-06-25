import { useRef, useEffect } from 'react'
import MessageBubble, { StreamingMessage } from './MessageBubble'
import { Sparkles, MessageSquare, Zap, Code2, FileText } from 'lucide-react'

const SUGGESTIONS = [
  { icon: <Sparkles size={14} />, text: 'Explain quantum computing simply' },
  { icon: <Code2 size={14} />,    text: 'Write a Python web scraper' },
  { icon: <Zap size={14} />,      text: 'Summarize a document for me' },
  { icon: <MessageSquare size={14} />, text: 'Help me write a cover letter' },
]

export default function ChatWindow({ messages, isStreaming, streamingContent, isReasoning, onSuggestion }) {
  const windowRef = useRef(null)
  const bottomRef = useRef(null)
  const prevMessagesLength = useRef(messages.length)
  const prevMessages = useRef(messages)

  // Scroll on new user message or chat switch
  useEffect(() => {
    if (!windowRef.current) return

    const hasNewMessage = messages.length > prevMessagesLength.current
    const lastMessageIsUser = messages[messages.length - 1]?.role === 'user'
    const isDifferentChat = messages !== prevMessages.current && messages.length > 0

    if ((hasNewMessage && lastMessageIsUser) || isDifferentChat) {
      bottomRef.current?.scrollIntoView({
        behavior: isDifferentChat ? 'auto' : 'smooth'
      })
    }

    prevMessagesLength.current = messages.length
    prevMessages.current = messages
  }, [messages, isStreaming])

  // Auto-scroll during streaming (only if user is near bottom)
  useEffect(() => {
    if (!isStreaming || !windowRef.current) return
    const el = windowRef.current
    const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 150
    if (isNearBottom) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [streamingContent, isReasoning, isStreaming])

  if (messages.length === 0 && !isStreaming) {
    return (
      <div className="chat-window">
        <div className="chat-empty">
          <div className="chat-empty-icon">
            <Sparkles size={30} color="white" />
          </div>
          <div>
            <h2>How can I help you today?</h2>
          </div>
          <p>Ask me anything — from coding challenges to creative writing, analysis, or document review.</p>
          <div className="chat-empty-suggestions">
            {SUGGESTIONS.map((s, i) => (
              <button key={i} className="suggestion-chip" onClick={() => onSuggestion(s.text)}>
                {s.icon} {s.text}
              </button>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="chat-window" ref={windowRef}>
      <div className="chat-messages-inner">
        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}
        {isStreaming && (
          <StreamingMessage content={streamingContent} isReasoning={isReasoning} />
        )}
        <div ref={bottomRef} style={{ height: 16 }} />
      </div>
    </div>
  )
}
