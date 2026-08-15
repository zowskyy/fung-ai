from __future__ import annotations

import json
import urllib.request
from typing import Callable

from .backend import AIBackend


class OpenAICompatBackend(AIBackend):
    """Speaks to any OpenAI-compatible server (Ollama, LM Studio, a cloud key)."""

    name = "OpenAI-compatible"

    def __init__(self, base_url: str, api_key: str = "", model: str = ""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model or "default"

    def is_available(self) -> bool:
        try:
            with urllib.request.urlopen(self.base_url + "/v1/models", timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def complete(
        self,
        system: str,
        messages: list[dict],
        on_delta: Callable[[str], None] | None = None,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, *messages],
            "stream": True,
        }
        request = urllib.request.Request(
            self.base_url + "/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        if self.api_key:
            request.add_header("Authorization", f"Bearer {self.api_key}")

        chunks: list[str] = []
        with urllib.request.urlopen(request, timeout=180) as response:
            for raw in response:
                line = raw.decode("utf-8", errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                data = line[len("data:"):].strip()
                if data == "[DONE]":
                    break
                try:
                    event = json.loads(data)
                except json.JSONDecodeError:
                    continue
                delta = event.get("choices", [{}])[0].get("delta", {}).get("content")
                if delta:
                    chunks.append(delta)
                    if on_delta is not None:
                        on_delta(delta)

        text = "".join(chunks).strip()
        if not text:
            raise RuntimeError("The AI server returned an empty reply.")
        return text
