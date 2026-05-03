import { Sparkles, Plus, Trash2, MessageSquare } from 'lucide-react'

export default function Sidebar({
  chats, activeChatId, models, selectedModel, enableReasoning, totalTokens,
  onNewChat, onSelectChat, onDeleteChat, onModelChange, onReasoningToggle,
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

        <div className="toggle-row">
          <span className="toggle-label">🧠 Reasoning Mode</span>
          <label className="toggle-switch">
            <input type="checkbox" checked={enableReasoning} onChange={e => onReasoningToggle(e.target.checked)} id="reasoning-toggle" />
            <span className="toggle-track" />
          </label>
        </div>

        <div className="token-badge">
          <span className="token-badge-label">Tokens used</span>
          <span className="token-badge-value">{totalTokens.toLocaleString()}</span>
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
