from openai import OpenAI, AsyncOpenAI

# Konfigurasi Model dan Provider yang diizinkan
AVAILABLE_MODELS = {
    "deepseek/deepseek-v4-pro": ["deepseek"],
    "deepseek/deepseek-v4-flash": ["deepseek"],
}


async def stream_openrouter(api_key: str, messages: list, model_name: str, enable_reasoning: bool):
    """
    Async generator yang yield dict: {"type": "reasoning"|"content"|"usage", "content": str}
    """
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        timeout=600.0, # Timeout 10 menit untuk mencegah AFK/Timeout
        default_headers={
            "HTTP-Referer": "https://github.com/RanRod/ai-chat",
            "X-Title": "AndroAI",
        }
    )

    allowed_providers = AVAILABLE_MODELS.get(model_name, [])

    extra_body: dict = {
        "provider": {
            "only": allowed_providers
        },
        "include_reasoning": enable_reasoning,
    }

    if enable_reasoning:
        extra_body["reasoning"] = {"enabled": True}
    else:
        extra_body["reasoning"] = {"effort": "none"}

    try:
        stream = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            stream=True,
            extra_body=extra_body,
            stream_options={"include_usage": True}
        )

        in_content_think_block = False

        async for chunk in stream:
            # 1. Statistik Penggunaan
            if hasattr(chunk, 'usage') and chunk.usage:
                usage_data = chunk.usage
                total_tokens = getattr(usage_data, 'total_tokens', 0)
                if total_tokens:
                    yield {"type": "usage", "content": str(total_tokens)}

            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            reasoning = getattr(delta, 'reasoning', None) or getattr(delta, 'reasoning_content', None)
            if reasoning and enable_reasoning:
                yield {"type": "reasoning", "content": reasoning}

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


async def generate_chat_title(api_key: str, ai_response: str, model_name: str) -> str:
    """
    Generates a concise title from the AI response.
    """
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        timeout=30.0,
        default_headers={
            "HTTP-Referer": "https://github.com/RanRod/ai-chat",
            "X-Title": "AndroAI",
        }
    )

    messages = [
        {"role": "system", "content": "You are a concise title generator. Output ONLY the title. No reasoning, no explanation, no thinking, no introduction."},
        {"role": "user", "content": f"Title for: {ai_response}"}
    ]

    allowed_providers = AVAILABLE_MODELS.get(model_name, [])
    
    extra_body = {
        "provider": {
            "only": allowed_providers
        },
        "include_reasoning": False,
        "reasoning": {
            "effort": "none"
        }
    }

    try:
        response = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=50,
            extra_body=extra_body
        )
        
        content = response.choices[0].message.content
        if content:
            title = content.strip().strip('"').strip("'").strip(".")
            if title.lower().startswith("title:"):
                title = title[6:].strip()
            
            return title.strip()
            
        return "New chat"
    except Exception:
        return "New chat"
