import { useState, useEffect, useRef } from 'react'
import { Toaster, toast } from 'react-hot-toast'
import { PanelLeftClose, PanelLeftOpen } from 'lucide-react'
import { useChat } from './hooks/useChat'
import Sidebar from './components/Sidebar'
import ChatWindow from './components/ChatWindow'
import InputBar from './components/InputBar'

export default function App() {
  const {
    chats, activeChatId, messages, isStreaming,
    streamingContent, streamingReasoning, totalTokens,
    loadChats, loadMessages, createChat, deleteChat,
    sendMessage, uploadFile, getModels,
  } = useChat()

  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [models, setModels] = useState([])
  const [selectedModel, setSelectedModel] = useState('')
  const [enableReasoning, setEnableReasoning] = useState(false)
  const [prefillText, setPrefillText] = useState('')
  const inputRef = useRef(null)

  /* ── Bootstrap ──────────────────────────────────────────────────────────── */
  useEffect(() => {
    const boot = async () => {
      try {
        const [chatList, modelList] = await Promise.all([loadChats(), getModels()])
        if (modelList.length) setSelectedModel(modelList[0])
        setModels(modelList)

        if (chatList.length > 0) {
          await loadMessages(chatList[0].id)
        } else {
          await createChat()
        }
      } catch {
        toast.error('Cannot connect to backend. Make sure the Python server is running on port 8000.')
      }
    }
    boot()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  /* ── Active chat title ──────────────────────────────────────────────────── */
  const activeChat = chats.find(c => c.id === activeChatId)
  const chatTitle = activeChat?.title || 'New Chat'

  /* ── Handlers ───────────────────────────────────────────────────────────── */
  const handleSend = async (content) => {
    if (!selectedModel) { toast.error('Please select a model'); return }
    try {
      await sendMessage(content, selectedModel, enableReasoning)
    } catch (e) {
      toast.error('Failed to send message: ' + e.message)
    }
  }

  const handleNewChat = async () => {
    try { await createChat() }
    catch { toast.error('Failed to create chat') }
  }

  const handleSelectChat = async (id) => {
    if (id === activeChatId) return
    try { await loadMessages(id) }
    catch { toast.error('Failed to load chat') }
  }

  const handleDeleteChat = async (id) => {
    try { await deleteChat(id); toast.success('Chat deleted') }
    catch { toast.error('Failed to delete chat') }
  }

  const handleSuggestion = (text) => {
    setPrefillText(text)
  }

  /* ── Inject suggestion text into InputBar ───────────────────────────────── */
  useEffect(() => {
    if (prefillText && inputRef.current) {
      inputRef.current.focus()
      // We'll handle this via a state prop on InputBar
    }
  }, [prefillText])

  return (
    <div className="app-layout">
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#16162a',
            color: '#f0f0ff',
            border: '1px solid rgba(124,58,237,0.3)',
            fontSize: '13.5px',
            fontFamily: 'Inter, sans-serif',
          },
          success: { iconTheme: { primary: '#a855f7', secondary: '#16162a' } },
          error: { iconTheme: { primary: '#f87171', secondary: '#16162a' } },
        }}
      />

      {/* Sidebar */}
      <div className={`sidebar ${sidebarOpen ? '' : 'collapsed'}`}>
        <Sidebar
          chats={chats}
          activeChatId={activeChatId}
          models={models}
          selectedModel={selectedModel}
          enableReasoning={enableReasoning}
          totalTokens={totalTokens}
          onNewChat={handleNewChat}
          onSelectChat={handleSelectChat}
          onDeleteChat={handleDeleteChat}
          onModelChange={setSelectedModel}
          onReasoningToggle={setEnableReasoning}
        />
      </div>

      {/* Main */}
      <div className="main-area">
        {/* Topbar */}
        <div className="topbar">
          <button
            className="topbar-toggle"
            onClick={() => setSidebarOpen(o => !o)}
            title={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
            id="sidebar-toggle"
          >
            {sidebarOpen ? <PanelLeftClose size={17} /> : <PanelLeftOpen size={17} />}
          </button>
          <div className="topbar-title">{chatTitle}</div>
          {selectedModel && (
            <div className="topbar-model-badge">{selectedModel.split('/')[1] || selectedModel}</div>
          )}
        </div>

        {/* Chat */}
        <ChatWindow
          messages={messages}
          isStreaming={isStreaming}
          streamingContent={streamingContent}
          streamingReasoning={streamingReasoning}
          onSuggestion={handleSuggestion}
        />

        {/* Input */}
        <InputBar
          onSend={handleSend}
          isStreaming={isStreaming}
          uploadFile={uploadFile}
          prefillText={prefillText}
          onPrefillConsumed={() => setPrefillText('')}
        />
      </div>
    </div>
  )
}
