import { useRef, useState, useEffect } from 'react'
import { Paperclip, Send, X, FileText, Square, Loader2, UploadCloud } from 'lucide-react'

export default function InputBar({ onSend, onStop, isStreaming, uploadFile, prefillText, onPrefillConsumed }) {
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
  const [isDragging, setIsDragging] = useState(false)
  const textareaRef = useRef(null)
  const fileInputRef = useRef(null)

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current
    if (!ta) return
    ta.style.height = 'auto'
    const newHeight = Math.min(ta.scrollHeight, 200)
    ta.style.height = newHeight + 'px'
  }, [text])

  const handleFileChange = async (e) => {
    const selected = Array.from(e.target.files || [])
    if (!selected.length) return
    await processFiles(selected)
    e.target.value = ''
  }

  const processFiles = async (selected) => {
    setUploading(true)
    try {
      const results = await Promise.all(selected.map(f => uploadFile(f)))
      setFiles(prev => [...prev, ...results])
    } catch (err) {
      console.error('upload error', err)
    } finally {
      setUploading(false)
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (!isStreaming && !uploading) {
      setIsDragging(true)
    }
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDrop = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    if (isStreaming || uploading) return

    const droppedFiles = Array.from(e.dataTransfer.files)
    if (!droppedFiles.length) return

    await processFiles(droppedFiles)
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
                <FileText size={14} />
                <span className="file-preview-name">{f.filename}</span>
                <button className="file-preview-remove" onClick={() => removeFile(i)}>
                  <X size={14} />
                </button>
              </div>
            ))}
          </div>
        )}
        <div 
          className={`input-box ${isDragging ? 'dragging' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {isDragging && (
            <div className="drag-overlay">
              <div className="drag-overlay-icon">
                <UploadCloud size={24} />
              </div>
              <span>Drop files here to attach</span>
            </div>
          )}
          <label className="input-btn attach-btn" title="Attach file">
            {uploading ? <Loader2 size={18} className="animate-spin" /> : <Paperclip size={18} />}
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
            placeholder={uploading ? 'Uploading file...' : 'Ask anything...'}
            disabled={isStreaming}
            rows={1}
            id="chat-input"
          />
          {isStreaming ? (
            <button
              className="input-btn stop-btn"
              onClick={onStop}
              title="Stop generating"
              id="stop-btn"
            >
              <Square size={16} fill="currentColor" />
            </button>
          ) : (
            <button
              className="input-btn send-btn"
              onClick={handleSend}
              disabled={!text.trim() && files.length === 0}
              title="Send"
              id="send-btn"
            >
              <Send size={18} />
            </button>
          )}
        </div>
        <div className="input-footer">
          <p>AI can make mistakes. Consider checking important information.</p>
        </div>
      </div>
    </div>
  )
}
