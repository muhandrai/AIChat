import { useState } from 'react'
import { ChevronDown, Brain } from 'lucide-react'

export default function ReasoningPanel({ reasoning, isStreaming }) {
  const [open, setOpen] = useState(true)
  if (!reasoning) return null

  return (
    <div className="reasoning-panel">
      <div className="reasoning-header" onClick={() => setOpen(o => !o)}>
        <span className="reasoning-header-left">
          <Brain size={14} />
          {isStreaming ? '💭 Thinking...' : '✅ Reasoning'}
        </span>
        <ChevronDown size={14} className={`reasoning-chevron ${open ? 'open' : ''}`} />
      </div>
      <div className={`reasoning-body ${open ? 'open' : ''}`}>
        <div className="reasoning-text">{reasoning}</div>
      </div>
    </div>
  )
}
