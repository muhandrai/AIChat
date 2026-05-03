from openai import OpenAI, AsyncOpenAI

# Konfigurasi Model dan Provider yang diizinkan
AVAILABLE_MODELS = {
    "deepseek/deepseek-v4-pro": ["deepseek"],
    "deepseek/deepseek-v4-flash": ["deepseek"],
    "qwen/qwen3.6-plus": ["alibaba"],
    "google/gemini-2.5-flash": ["google-vertex/global"],
}


def stream_openrouter(api_key: str, messages: list, model_name: str, enable_reasoning: bool):
    """
    Pure Python generator yang yield dict: {"type": "reasoning"|"content"|"usage", "content": str}
    Tidak ada dependensi Streamlit sama sekali.
    """
    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://github.com/RanRod/ai-chat",
            "X-Title": "AndroAI",
        }
    )

    # Ambil provider yang sesuai dari konfigurasi pusat
    allowed_providers = AVAILABLE_MODELS.get(model_name, [])

    # Konfigurasi routing provider & reasoning
    extra_body: dict = {
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

        in_content_think_block = False

        for chunk in stream:
            # 1. Statistik Penggunaan
            if hasattr(chunk, 'usage') and chunk.usage:
                usage_data = chunk.usage
                total_tokens = getattr(usage_data, 'total_tokens', 0)
                if total_tokens:
                    yield {"type": "usage", "content": str(total_tokens)}

            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            # 2. Tangkap Native Reasoning
            reasoning = getattr(delta, 'reasoning', None) or getattr(delta, 'reasoning_content', None)
            if reasoning and enable_reasoning:
                yield {"type": "reasoning", "content": reasoning}

            # 3. Tangkap Content (dengan penanganan tag <think> yang lebih kuat)
            content = getattr(delta, 'content', None)
            if content:
                pending_content = content

                while pending_content:
                    if not in_content_think_block:
                        if "<think>" in pending_content:
                            parts = pending_content.split("<think>", 1)
                            if parts[0]:
                                yield {"type": "content", "content": parts[0]}
                            in_content_think_block = True
                            pending_content = parts[1] if len(parts) > 1 else ""
                        else:
                            yield {"type": "content", "content": pending_content}
                            pending_content = ""
                    else:
                        if "</think>" in pending_content:
                            parts = pending_content.split("</think>", 1)
                            if parts[0] and enable_reasoning:
                                yield {"type": "reasoning", "content": parts[0]}
                            in_content_think_block = False
                            pending_content = parts[1] if len(parts) > 1 else ""
                        else:
                            if enable_reasoning:
                                yield {"type": "reasoning", "content": pending_content}
                            pending_content = ""

    except Exception as e:
        yield {"type": "error", "content": str(e)}


def generate_chat_title(api_key: str, ai_response: str, model_name: str) -> str:
    """
    Generates a concise title from the AI response.
    """
    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://github.com/RanRod/ai-chat",
            "X-Title": "AndroAI",
        }
    )

    prompt = f"Summarize the following AI response into a very short, concise title (max 5 words). Output ONLY the title, no quotes or punctuation.\n\nAI Response: {ai_response}"

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
        )
        title = response.choices[0].message.content.strip()
        # Clean up title
        title = title.strip('"').strip("'").strip(".")
        return title
    except Exception as e:
        print(f"Error generating title: {e}")
        return "New chat"
