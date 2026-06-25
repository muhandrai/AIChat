import httpx
import json

# Konfigurasi Model dan Provider yang diizinkan
AVAILABLE_MODELS = {
    "deepseek/deepseek-v4-flash": ["deepseek"],
    "deepseek/deepseek-v4-pro": ["deepseek"],
}

# Sesuai enum ReasoningEffort pada dokumentasi OpenRouter POST /responses
# (max, xhigh, high, medium, low, minimal, none)
REASONING_EFFORTS = ("none", "minimal", "low", "medium", "high", "xhigh", "max")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/responses"
DEFAULT_HEADERS = {
    "HTTP-Referer": "https://github.com/RanRod/ai-chat",
    "X-Title": "AndroAI",
    "Content-Type": "application/json",
}


def _normalize_effort(reasoning_effort: str) -> str:
    """Validasi nilai effort terhadap enum dokumentasi, fallback ke 'none'."""
    return reasoning_effort if reasoning_effort in REASONING_EFFORTS else "none"


def _sanitize_input(messages: list) -> list:
    """Petakan riwayat percakapan ke bentuk `EasyInputMessage` yang valid.

    Dokumentasi `input` hanya mengenal field `role`/`content` (dan `phase`/`type`)
    untuk pesan. Field internal seperti `reasoning` yang kita simpan untuk
    keperluan tampilan tidak boleh ikut dikirim ke API.
    """
    sanitized = []
    for msg in messages or []:
        role = msg.get("role")
        content = msg.get("content", "")
        if role is None:
            continue
        sanitized.append({"role": role, "content": content})
    return sanitized


def _build_reasoning_config(effort: str) -> dict:
    """Bangun objek ReasoningConfig sesuai dokumentasi.

    - effort "none"  -> matikan reasoning (`enabled: false`)
    - selain itu     -> aktifkan dengan effort terkait (`enabled: true`)
    """
    if effort == "none":
        return {"enabled": False}
    return {"effort": effort, "enabled": True}


def _extract_usage(usage: dict) -> dict:
    """Petakan objek Usage OpenResponses ke bentuk yang dipakai frontend.

    Dokumentasi memakai `input_tokens`/`output_tokens`/`total_tokens` (canonical),
    dengan fallback ke `prompt_tokens`/`completion_tokens` untuk kompatibilitas.
    """
    usage = usage or {}

    prompt = usage.get("input_tokens")
    if prompt is None:
        prompt = usage.get("prompt_tokens", 0)

    completion = usage.get("output_tokens")
    if completion is None:
        completion = usage.get("completion_tokens", 0)

    prompt = prompt or 0
    completion = completion or 0
    total = usage.get("total_tokens") or (prompt + completion)

    return {
        "total_tokens": total,
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "cost": usage.get("cost"),
    }


async def stream_openrouter(api_key: str, messages: list, model_name: str, reasoning_effort: str):
    """
    Async generator yang yield dict:
      {"type": "reasoning"|"content"|"usage"|"error", "content": ...}
    """
    allowed_providers = AVAILABLE_MODELS.get(model_name, [])
    effort = _normalize_effort(reasoning_effort)
    enable_reasoning = effort != "none"

    payload = {
        "model": model_name,
        "input": _sanitize_input(messages),
        "stream": True,
        "provider": {"only": allowed_providers},
        "reasoning": _build_reasoning_config(effort),
    }

    headers = {
        **DEFAULT_HEADERS,
        "Authorization": f"Bearer {api_key}",
    }

    in_content_think_block = False

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(600.0)) as client:
            async with client.stream("POST", OPENROUTER_BASE_URL, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    error_body = await response.aread()
                    try:
                        error_json = json.loads(error_body)
                        error_msg = error_json.get("error", {}).get("message", error_body.decode())
                    except Exception:
                        error_msg = error_body.decode()
                    yield {"type": "error", "content": f"API Error {response.status_code}: {error_msg}"}
                    return

                buffer = ""
                async for raw_chunk in response.aiter_bytes():
                    buffer += raw_chunk.decode("utf-8", errors="replace")
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()

                        if not line or line.startswith(":"):
                            continue
                        if not line.startswith("data: "):
                            continue

                        data_str = line[6:]
                        if data_str == "[DONE]":
                            return

                        try:
                            event = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue

                        event_type = event.get("type", "")

                        if event_type in ("response.created", "response.in_progress"):
                            continue

                        if event_type in ("response.completed", "response.incomplete"):
                            resp = event.get("response", {})
                            yield {"type": "usage", "content": _extract_usage(resp.get("usage", {}))}
                            continue

                        # Stream teks jawaban utama
                        if event_type == "response.output_text.delta":
                            delta_text = event.get("delta", "")
                            if not delta_text:
                                continue

                            pending_content = delta_text
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
                                            yield {"type": "reasoning"}
                                        in_content_think_block = False
                                        pending_content = parts[1] if len(parts) > 1 else ""
                                    else:
                                        if enable_reasoning:
                                            yield {"type": "reasoning"}
                                        pending_content = ""
                            continue

                        # Reasoning native (Responses API). Kontennya tidak diteruskan
                        # ke klien maupun disimpan — cukup ditandai bahwa model sedang
                        # bernalar agar UI bisa menampilkan status "Reasoning...".
                        if event_type in (
                            "response.reasoning_summary_text.delta",
                            "response.reasoning_text.delta",
                            "response.reasoning.delta",
                        ):
                            if enable_reasoning and event.get("delta"):
                                yield {"type": "reasoning"}
                            continue

                        # Error mid-stream
                        if event_type in ("response.failed", "error"):
                            resp = event.get("response", {})
                            err = resp.get("error") or event.get("error") or event.get("message")
                            if isinstance(err, dict):
                                err = err.get("message", str(err))
                            yield {"type": "error", "content": err or "Streaming failed"}
                            return

                        # Event lain (delta done, item done, dll.) diabaikan
                        continue

    except httpx.ReadTimeout:
        yield {"type": "error", "content": "Request timed out after 10 minutes. Try a shorter prompt."}
    except httpx.ConnectError:
        yield {"type": "error", "content": "Cannot connect to OpenRouter API. Check your internet connection."}
    except Exception as e:
        yield {"type": "error", "content": str(e)}


def _extract_output_text(data: dict) -> str:
    """Ambil teks jawaban dari OpenResponsesResult.

    Utamakan field konvenien `output_text`, lalu fallback menelusuri array `output`.
    """
    output_text = data.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    for item in data.get("output", []):
        if item.get("type") == "message" and item.get("role") == "assistant":
            for block in item.get("content", []):
                if block.get("type") == "output_text":
                    text = block.get("text", "")
                    if text:
                        return text
    return ""


async def generate_chat_title(api_key: str, ai_response: str, model_name: str) -> str:
    allowed_providers = AVAILABLE_MODELS.get(model_name, [])

    payload = {
        "model": model_name,
        "input": [
            {"role": "system", "content": "You are a concise title generator. Output ONLY the title. No reasoning, no explanation, no thinking, no introduction."},
            {"role": "user", "content": f"Title for: {ai_response}"},
        ],
        "max_output_tokens": 50,
        "provider": {"only": allowed_providers},
        "reasoning": _build_reasoning_config("none"),
    }

    headers = {
        **DEFAULT_HEADERS,
        "Authorization": f"Bearer {api_key}",
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            resp = await client.post(OPENROUTER_BASE_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            text = _extract_output_text(data)
            if text:
                title = text.strip().strip('"').strip("'").strip(".")
                if title.lower().startswith("title:"):
                    title = title[6:].strip()
                title = title.strip()
                if title:
                    return title

            return "New chat"
    except Exception:
        return "New chat"
