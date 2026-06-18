"""Client LLM tối giản theo chuẩn OpenAI-compatible (dùng qua gateway ckey.vn).

Cấu hình qua biến môi trường (nạp từ `.env` bằng python-dotenv):
- OPENAI_API_KEY  : API key của ckey.vn
- OPENAI_BASE_URL : base URL của ckey.vn (vd https://api.ckey.vn/v1 — lấy đúng theo tài liệu)
- OPENAI_MODEL    : tên model, mặc định "gpt-5.4-mini"

`chat()` trả về (text, Usage) — token/latency THẬT để agents.py ghi vào trace (B5).
Có retry + timeout cho các lỗi tạm thời (429/5xx/timeout) khi chạy hàng trăm lời gọi.
"""
from __future__ import annotations
import os
import time
from functools import lru_cache
from dotenv import load_dotenv
from .schemas import Usage

load_dotenv()

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
DEFAULT_TIMEOUT = float(os.getenv("OPENAI_TIMEOUT", "60"))
MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "4"))


@lru_cache(maxsize=1)
def _client():
    # Import trễ để backend "mock" không cần cài openai.
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    if not api_key:
        raise RuntimeError("Thiếu OPENAI_API_KEY trong môi trường/.env (key của ckey.vn).")
    if not base_url:
        raise RuntimeError("Thiếu OPENAI_BASE_URL trong môi trường/.env (base URL của ckey.vn).")
    return OpenAI(api_key=api_key, base_url=base_url, timeout=DEFAULT_TIMEOUT)


def chat(system: str, user: str, *, temperature: float = 0.0, json_mode: bool = False) -> tuple[str, Usage]:
    """Gọi chat-completions một lượt. Trả về (nội dung text, Usage thật).

    json_mode=True sẽ thử bật response_format={"type":"json_object"}; nếu gateway/model
    không hỗ trợ thì tự bỏ tham số và gọi lại (parse JSON vẫn được xử lý ở tầng trên).
    """
    from openai import OpenAIError  # type: ignore

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    kwargs: dict = {"model": DEFAULT_MODEL, "messages": messages, "temperature": temperature}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    last_err: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        t0 = time.perf_counter()
        try:
            resp = _client().chat.completions.create(**kwargs)
        except TypeError:
            # SDK/gateway không nhận response_format → bỏ và thử lại ngay.
            kwargs.pop("response_format", None)
            continue
        except OpenAIError as err:
            last_err = err
            status = getattr(err, "status_code", None)
            # Lỗi 4xx không-tạm-thời (401 auth, 402 billing, 403, 404) → fail ngay, retry vô ích.
            if status in (400, 401, 402, 403, 404) and "response_format" not in kwargs:
                raise RuntimeError(f"Gọi LLM bị từ chối (HTTP {status}): {err}") from err
            if "response_format" in kwargs:
                # Một số gateway báo lỗi tham số response_format → hạ cấp rồi thử lại.
                kwargs.pop("response_format", None)
                continue
            # Còn lại (408/409/429/5xx/timeout/connection) → backoff rồi thử lại.
            time.sleep(min(2 ** attempt, 16))
            continue

        latency_ms = int((time.perf_counter() - t0) * 1000)
        text = (resp.choices[0].message.content or "").strip()
        u = getattr(resp, "usage", None)
        usage = Usage(
            prompt_tokens=getattr(u, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(u, "completion_tokens", 0) or 0,
            total_tokens=getattr(u, "total_tokens", 0) or 0,
            latency_ms=latency_ms,
        )
        return text, usage

    raise RuntimeError(f"Gọi LLM thất bại sau {MAX_RETRIES} lần thử: {last_err}")
