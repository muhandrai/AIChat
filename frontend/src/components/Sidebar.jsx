import { Sparkles, Plus, Trash2, MessageSquare } from 'lucide-react'

export default function Sidebar({
  chats, activeChatId, models, selectedModel, reasoningEffort, totalTokens, usageDetails,
  onNewChat, onSelectChat, onDeleteChat, onModelChange, onReasoningChange,
}) {
  return (
    <>
      {/* Header + logo */}
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">
            <Sparkles size={16} color="white" />
          </div>
          <span className="sidebar-logo-text">AndroAI</span>
        </div>
        <button className="new-chat-btn" onClick={onNewChat} id="new-chat-btn">
          <Plus size={15} /> New Chat
        </button>
      </div>

      {/* Settings */}
      <div className="sidebar-settings">
        <span className="settings-label">Model</span>
        <div className="select-wrapper">
          <select value={selectedModel} onChange={e => onModelChange(e.target.value)} id="model-select">
            {models.map(m => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>

        <span className="settings-label">Reasoning</span>
        <div className="select-wrapper">
          <select value={reasoningEffort} onChange={e => onReasoningChange(e.target.value)} id="reasoning-select">
            <option value="none">None</option>
            <option value="minimal">Minimal</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="xhigh">X-High</option>
            <option value="max">Max</option>
          </select>
        </div>

        <div className="token-badge">
          <span className="token-badge-label">Tokens used</span>
          <span className="token-badge-value">{totalTokens.toLocaleString()}</span>
          {usageDetails && (
            <span className="token-badge-detail">
              ↑ {(usageDetails.prompt_tokens || 0).toLocaleString()} · ↓ {(usageDetails.completion_tokens || 0).toLocaleString()}
              {usageDetails.cost != null && ` · $${Number(usageDetails.cost).toFixed(4)}`}
            </span>
          )}
        </div>
      </div>

      {/* Chat list */}
      <div className="sidebar-chats">
        <div className="chat-list-label">Recent Chats</div>
        {chats.length === 0 && (
          <div style={{ fontSize: 12, color: 'var(--text-muted)', padding: '8px 6px' }}>No chats yet.</div>
        )}
        {chats.map(chat => (
          <div
            key={chat.id}
            className={`chat-item ${chat.id === activeChatId ? 'active' : ''}`}
            onClick={() => onSelectChat(chat.id)}
          >
            <MessageSquare size={13} style={{ flexShrink: 0, color: 'var(--text-muted)' }} />
            <span className="chat-item-text" title={chat.title}>{chat.title}</span>
            <button
              className="chat-delete-btn"
              onClick={e => { e.stopPropagation(); onDeleteChat(chat.id) }}
              title="Delete chat"
            >
              <Trash2 size={13} />
            </button>
          </div>
        ))}
      </div>
    </>
  )
}
