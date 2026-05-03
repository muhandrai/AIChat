import { useRef, useState, useEffect } from 'react'
import { Paperclip, Send, X, FileText } from 'lucide-react'

export default function InputBar({ onSend, isStreaming, uploadFile, prefillText, onPrefillConsumed }) {
  const [text, setText] = useState('')

  useEffect(() => {
    if (prefillText) {
      setText(prefillText)
      onPrefillConsumed?.()
      setTimeout(() => textareaRef.current?.focus(), 50)
    }
  }, [prefillText, onPrefillConsumed])
  const [files, setFiles] = useState([]) // [{name, content}]
  const [uploading, setUploading] = useState(false)
  const textareaRef = useRef(null)
  const fileInputRef = useRef(null)

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current
    if (!ta) return
    ta.style.height = 'auto'
    ta.style.height = Math.min(ta.scrollHeight, 200) + 'px'
  }, [text])

  const handleFileChange = async (e) => {
    const selected = Array.from(e.target.files || [])
    if (!selected.length) return
    setUploading(true)
    try {
      const results = await Promise.all(selected.map(f => uploadFile(f)))
      setFiles(prev => [...prev, ...results])
    } catch (err) {
      console.error('upload error', err)
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  const removeFile = (idx) => setFiles(prev => prev.filter((_, i) => i !== idx))

  const handleSend = () => {
    const trimmed = text.trim()
    if (!trimmed && files.length === 0) return
    if (isStreaming) return

    let finalContent = trimmed
    for (const f of files) {
      finalContent += `\n--- Document Content: ${f.filename} ---\n${f.content}`
    }

    onSend(finalContent)
    setText('')
    setFiles([])
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // Expose a way for parent to pre-fill text (for suggestion chips)
  useEffect(() => {
    if (textareaRef.current) textareaRef.current.focus()
  }, [])

  return (
    <div className="input-area">
      <div className="input-wrapper">
        {files.length > 0 && (
          <div className="file-previews">
            {files.map((f, i) => (
              <div key={i} className="file-preview-chip">
                <FileText size={12} />
                <span>{f.filename}</span>
                <button className="file-preview-remove" onClick={() => removeFile(i)}>
                  <X size={12} />
                </button>
              </div>
            ))}
          </div>
        )}
        <div className="input-box">
          <label className="input-btn attach-btn" title="Attach file">
            <Paperclip size={17} />
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.txt,.json,.csv,.tsv"
              onChange={handleFileChange}
              disabled={isStreaming || uploading}
            />
          </label>
          <textarea
            ref={textareaRef}
            value={text}
            onChange={e => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={uploading ? 'Uploading file...' : 'Ask anything... (Shift+Enter for newline)'}
            disabled={isStreaming}
            rows={1}
            id="chat-input"
          />
          <button
            className="input-btn send-btn"
            onClick={handleSend}
            disabled={isStreaming || (!text.trim() && files.length === 0)}
            title="Send"
            id="send-btn"
          >
            <Send size={16} />
          </button>
        </div>
        <div className="input-footer">
          AI can make mistakes — verify important information.
        </div>
      </div>
    </div>
  )
}

// Expose setText externally via ref pattern — just export helper
export function prefillInput(ref, value) {
  if (ref?.current) ref.current.value = value
}
