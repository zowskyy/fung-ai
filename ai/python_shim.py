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

    def _endpoint(self, suffix: str) -> str:
        """Build an OpenAI-compatible endpoint, adding /v1 exactly once.

        Provider base URLs already end in /v1 (e.g. https://api.blockrun.dev/v1),
        while local servers like http://localhost:11434 do not. Appending
        '/v1' blindly produced '.../v1/v1/...' and 404s for every request.
        """
        base = self.base_url.rstrip("/")
        if base.endswith("/v1"):
            return base + suffix
        return base + "/v1" + suffix

    def is_available(self) -> bool:
        try:
            with urllib.request.urlopen(self._endpoint("/models"), timeout=5) as resp:
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
            self._endpoint("/chat/completions"),
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
                if "error" in event:
                    raise RuntimeError(f"AI server returned an error: {event['error']}")
                choices = event.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta", {}).get("content")
                if delta:
                    chunks.append(delta)
                    if on_delta is not None:
                        on_delta(delta)

        text = "".join(chunks).strip()
        if not text:
            raise RuntimeError("The AI server returned an empty reply.")
        return text
