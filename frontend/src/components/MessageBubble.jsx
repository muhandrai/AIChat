import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Copy, Check, Bot, User, Paperclip } from 'lucide-react'
import ReasoningPanel from './ReasoningPanel'

function CodeBlock({ language, children }) {
  const [copied, setCopied] = useState(false)
  const code = String(children).replace(/\n$/, '')

  const handleCopy = () => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="code-block-wrapper">
      <div className="code-block-header">
        <span>{language || 'code'}</span>
        <button className="code-copy-btn" onClick={handleCopy}>
          {copied ? <><Check size={11} /> Copied</> : <><Copy size={11} /> Copy</>}
        </button>
      </div>
      <SyntaxHighlighter
        style={oneDark}
        language={language || 'text'}
        PreTag="div"
        customStyle={{ margin: 0, borderRadius: 0, fontSize: '13px', background: '#0d0d1a' }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  )
}

const markdownComponents = {
  code({ node, inline, className, children, ...props }) {
    const match = /language-(\w+)/.exec(className || '')
    return !inline && match ? (
      <CodeBlock language={match[1]}>{children}</CodeBlock>
    ) : (
      <code className={className} {...props}>{children}</code>
    )
  },
  pre({ children }) { return <>{children}</> },
  table({ children }) {
    return (
      <div className="table-wrapper">
        <table>{children}</table>
      </div>
    )
  },
}

/* ── Typing indicator ─────────────────────────────────────────────────────── */
function TypingIndicator() {
  return (
    <div className="typing-indicator">
      <div className="typing-dot" />
      <div className="typing-dot" />
      <div className="typing-dot" />
    </div>
  )
}

/* ── Single message bubble ────────────────────────────────────────────────── */
function MessageBubble({ message }) {
  const isUser = message.role === 'user'

  // Separate file annotations from visible text
  let displayText = message.content
  let hasFile = false
  if (isUser && displayText.includes('\n--- Document Content:')) {
    const parts = displayText.split('\n--- Document Content:')
    displayText = parts[0].trim()
    hasFile = true
  }

  return (
    <div className={`message-row ${isUser ? 'user' : 'assistant'}`}>
      <div className={`avatar ${isUser ? 'user' : 'assistant'}`}>
        {isUser ? <User size={16} color="white" /> : <Bot size={16} color="#a855f7" />}
      </div>
      <div className="message-content-wrap">
        <div className={`bubble ${isUser ? 'user' : 'assistant'}`}>
          {isUser ? (
            <>{displayText}</>
          ) : (
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
              {message.content}
            </ReactMarkdown>
          )}
        </div>
        {hasFile && (
          <span className="file-tag">
            <Paperclip size={11} /> Document attached in AI context
          </span>
        )}
      </div>
    </div>
  )
}

/* ── Streaming assistant row ─────────────────────────────────────────────── */
export function StreamingMessage({ content, reasoning }) {
  const showTyping = !content && !reasoning
  return (
    <div className="message-row assistant">
      <div className="avatar assistant">
        <Bot size={16} color="#a855f7" />
      </div>
      <div className="message-content-wrap">
        {reasoning && <ReasoningPanel reasoning={reasoning} isStreaming={!content} />}
        {showTyping ? (
          <TypingIndicator />
        ) : content ? (
          <div className="bubble assistant stream-cursor">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
              {content}
            </ReactMarkdown>
          </div>
        ) : null}
      </div>
    </div>
  )
}

export default MessageBubble
