import streamlit as st
from openai import OpenAI

# Konfigurasi Model dan Provider yang diizinkan
AVAILABLE_MODELS = {
    "deepseek/deepseek-v4-pro": ["deepseek"],
    "deepseek/deepseek-v4-flash": ["deepseek"],
    "qwen/qwen3.6-plus": ["alibaba"],
    "google/gemini-2.5-flash": ["google-vertex/global"],
}

def generate_title_from_first_ai_response(api_key: str, base_url: str, model_name: str, response_text: str) -> str:
    """
    Menghasilkan judul singkat berdasarkan respons pertama AI menggunakan API.
    """
    try:
        headers = {}
        if "openrouter.ai" in base_url:
            headers = {
                "HTTP-Referer": "https://github.com/RanRod/ai-chat",
                "X-Title": "Multi-Provider AI Chat",
            }
            
        client = OpenAI(
            api_key=api_key, 
            base_url=base_url,
            default_headers=headers
        )
        
        prompt = f"Summarize the following AI response into a very short, concise chat title (maximum 5 words). Do not use quotes or special characters:\n\n{response_text[:1000]}"
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates short chat titles."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=20,
            temperature=0.7
        )
        
        title = response.choices[0].message.content.strip()
        # Bersihkan jika ada tanda kutip atau karakter aneh
        title = title.replace('"', '').replace("'", "").replace("*", "").replace("#", "").strip()
        
        return title if title else "New chat"
        
    except Exception as e:
        print(f"Error generating title: {e}")
        # Fallback ke 5 kata pertama jika API gagal
        words = response_text.split()[:5]
        return " ".join(words) + "..." if words else "New chat"



def stream_openrouter(api_key: str, messages: list, model_name: str, reasoning_box, enable_reasoning: bool, token_placeholder):
    """
    Implementasi stream OpenRouter lengkap berdasarkan API Reference.
    """
    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://github.com/RanRod/ai-chat",
            "X-Title": "Multi-Provider AI Chat",
        }
    )
    
    # Ambil provider yang sesuai dari konfigurasi pusat
    allowed_providers = AVAILABLE_MODELS.get(model_name, [])
    
    # Konfigurasi routing provider & reasoning
    extra_body = {
        "provider": {
            "only": allowed_providers
        },
        "include_reasoning": enable_reasoning
    }
    
    if enable_reasoning:
        extra_body["reasoning"] = {
            "enabled": True,
            "exclude": False,
        }
    
    try:
        stream = client.chat.completions.create(
            model=model_name,
            messages=messages,
            stream=True,
            extra_body=extra_body,
            stream_options={"include_usage": True}
        )
        
        thinking_text = ""
        in_content_think_block = False
        
        # Container untuk proses berpikir agar lebih rapi
        reasoning_container = None
        if enable_reasoning:
            reasoning_container = reasoning_box.status("💭 Menghasilkan pemikiran...", expanded=True)

        for chunk in stream:
            # 1. Statistik Penggunaan
            if hasattr(chunk, 'usage') and chunk.usage:
                usage_data = chunk.usage
                total_tokens = getattr(usage_data, 'total_tokens', 0)
                if total_tokens:
                    st.session_state.total_tokens = total_tokens
                    token_placeholder.metric("Total Tokens (Context)", f"{total_tokens:,}")

            if not chunk.choices:
                continue
                
            delta = chunk.choices[0].delta
            
            # 2. Tangkap Native Reasoning
            reasoning = getattr(delta, 'reasoning', None) or getattr(delta, 'reasoning_content', None)
            if reasoning and enable_reasoning:
                thinking_text += reasoning
                reasoning_container.markdown(thinking_text)
                yield ("reasoning", reasoning) # Kirim sinyal reasoning ke UI
            
            # 3. Tangkap Content (dengan penanganan tag <think> yang lebih kuat)
            content = getattr(delta, 'content', None)
            if content:
                pending_content = content
                
                while pending_content:
                    if not in_content_think_block:
                        if "<think>" in pending_content:
                            parts = pending_content.split("<think>", 1)
                            if parts[0]:
                                yield ("content", parts[0])
                            
                            in_content_think_block = True
                            pending_content = parts[1] if len(parts) > 1 else ""
                        else:
                            yield ("content", pending_content)
                            pending_content = ""
                    else:
                        if "</think>" in pending_content:
                            parts = pending_content.split("</think>", 1)
                            if parts[0] and enable_reasoning:
                                thinking_text += parts[0]
                                reasoning_container.markdown(thinking_text)
                                yield ("reasoning", parts[0])
                            
                            in_content_think_block = False
                            if reasoning_container:
                                reasoning_container.update(label="✅ Pemikiran Selesai", state="complete", expanded=False)
                            
                            pending_content = parts[1] if len(parts) > 1 else ""
                        else:
                            if enable_reasoning:
                                thinking_text += pending_content
                                reasoning_container.markdown(thinking_text)
                                yield ("reasoning", pending_content)
                            pending_content = ""

        
        # Pastikan status box tertutup jika tidak ada tag </think> tapi streaming selesai
        if reasoning_container:
            reasoning_container.update(label="✅ Pemikiran Selesai", state="complete", expanded=False)

                
    except Exception as e:
        st.error(f"OpenRouter Stream Error: {e}")
        yield ("content", f"⚠️ Error: {str(e)}")
