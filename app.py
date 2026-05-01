import streamlit as st
import os
import uuid
import PyPDF2
from dotenv import load_dotenv

# Import local modules
from database import init_db, load_chats_from_db, save_chat_to_db
from api_client import generate_title_from_first_ai_response, stream_openrouter, AVAILABLE_MODELS

load_dotenv()

st.set_page_config(page_title="Multi-Provider AI Chat", page_icon="🤖", layout="wide")
st.title("💬 Multi-Provider AI Chat")
st.caption("A chat application that automatically routes processes based on the selected model with SQLite history.")

def create_new_chat() -> None:
    chat_id = str(uuid.uuid4())
    st.session_state.chats[chat_id] = {"title": "New chat", "messages": []}
    st.session_state.chat_order.insert(0, chat_id)
    st.session_state.active_chat_id = chat_id
    st.session_state.total_tokens = 0
    save_chat_to_db(chat_id, st.session_state.chats[chat_id])

def initialize_session_state() -> None:
    if "total_tokens" not in st.session_state:
        st.session_state.total_tokens = 0

    if "chats" not in st.session_state:
        chats, order = load_chats_from_db()
        if chats:
            st.session_state.chats = chats
            st.session_state.chat_order = order
            st.session_state.active_chat_id = order[0]
        else:
            st.session_state.chats = {}
            st.session_state.chat_order = []
            create_new_chat()

# Inisialisasi Database dan Session State
init_db()
initialize_session_state()

current_chat = st.session_state.chats[st.session_state.active_chat_id]

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Chat Settings")
    
    # Ambil daftar model dari api_client.py secara dinamis
    model_options = list(AVAILABLE_MODELS.keys())
    selected_model = st.selectbox("Select Model:", model_options)
    
    provider = "OpenRouter"
    base_url = "https://openrouter.ai/api/v1"
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    st.caption(f"*Active Provider: {provider}*")
    st.divider()
    
    enable_reasoning_radio = st.radio("Thinking Process (Reasoning):", ["Off", "On"], index=0)
    enable_reasoning = True if enable_reasoning_radio == "On" else False

    st.divider()
    token_placeholder = st.empty()
    token_placeholder.metric("Total Tokens (Context)", f"{st.session_state.total_tokens:,}")

    st.divider()
    st.subheader("🗂️ Chat Sessions")

    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        create_new_chat()
        st.rerun()
    
    st.divider()
    
    for chat_id in st.session_state.chat_order:
        chat_data = st.session_state.chats[chat_id]
        is_active = chat_id == st.session_state.active_chat_id
        title = chat_data["title"] if len(chat_data["title"]) <= 32 else f"{chat_data['title'][:32]}..."
        label = f"🟢 {title}" if is_active else title

        if st.button(
            label,
            key=f"chat_{chat_id}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
            help=f"{len(chat_data['messages'])} messages",
        ):
            st.session_state.active_chat_id = chat_id
            st.session_state.total_tokens = 0
            st.rerun()

# --- MAIN CHAT AREA ---
if not api_key:
    st.info(f"💡 Please enter your API Key for {provider} in the sidebar to start.")
    st.stop()

if not current_chat["messages"]:
    st.info("Start the conversation by typing a question below.")

for msg in current_chat["messages"]:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            display_text = msg["content"]
            if "\n--- Document Content:" in display_text:
                user_msg_part = display_text.split("\n--- Document Content:")[0].strip()
                if user_msg_part:
                    st.markdown(user_msg_part)
                st.caption("📎 *(Document attached in AI context)*")
            else:
                st.markdown(display_text)
        else:
            st.markdown(msg["content"])

prompt_data = st.chat_input(
    "Type your message and/or upload files...",
    accept_file="multiple",
    file_type=["pdf", "json", "txt", "csv", "tsv"]
)

if prompt_data:
    user_text = prompt_data.text if prompt_data.text else ""
    uploaded_files = prompt_data.files if hasattr(prompt_data, 'files') and prompt_data.files else []
    
    final_prompt = user_text
    file_contents = []
    
    if uploaded_files:
        for file in uploaded_files:
            try:
                ext = file.name.split('.')[-1].lower()
                if ext == "pdf":
                    reader = PyPDF2.PdfReader(file)
                    text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
                else:
                    text = file.read().decode("utf-8")
                    
                file_contents.append(f"\n--- Document Content: {file.name} ---\n{text}")
            except Exception as e:
                st.error(f"Failed to read file {file.name}: {e}")
                
        if file_contents:
            final_prompt += "".join(file_contents)
            
    if final_prompt.strip():
        with st.chat_message("user"):
            if user_text:
                st.markdown(user_text)
            for file in uploaded_files:
                st.caption(f"📎 File uploaded: {file.name}")
        
        current_chat["messages"].append({"role": "user", "content": final_prompt})
        
        # Pindahkan chat yang aktif ke urutan paling atas
        if st.session_state.active_chat_id in st.session_state.chat_order:
            st.session_state.chat_order.remove(st.session_state.active_chat_id)
        st.session_state.chat_order.insert(0, st.session_state.active_chat_id)
        
        save_chat_to_db(st.session_state.active_chat_id, current_chat)
        
        with st.chat_message("assistant"):
            reasoning_box = st.empty()
            response_placeholder = st.empty()
            
            generator = stream_openrouter(api_key, current_chat["messages"], selected_model, reasoning_box, enable_reasoning, token_placeholder)
            
            full_response = ""
            # full_reasoning hanya untuk display sementara, tidak disimpan
            
            # Handle structured stream
            for chunk_type, chunk_content in generator:
                if chunk_type == "reasoning":
                    # Kita biarkan api_client yang mengupdate reasoning_box
                    pass
                else:
                    full_response += chunk_content
                    response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            
            # SIMPAN HANYA KONTEN, TANPA REASONING
            current_chat["messages"].append({
                "role": "assistant", 
                "content": full_response
            })
            
            assistant_count = sum(1 for m in current_chat["messages"] if m["role"] == "assistant")
            if assistant_count == 1 and current_chat.get("title", "New chat") == "New chat" and full_response.strip():
                try:
                    new_title = generate_title_from_first_ai_response(api_key, base_url, selected_model, full_response)
                    current_chat["title"] = new_title
                except Exception as e:
                    st.error(f"Error generating title: {e}")

            save_chat_to_db(st.session_state.active_chat_id, current_chat)
            st.rerun()