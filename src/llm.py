"""
LLM wrapper for Project Ava.
Abstracts Claude CLI, Anthropic API, and Ollama so the rest of the pipeline
doesn't care which backend is used.

Usage:
    llm = LLM(backend="claude_cli")          # claude -p (Max plan, free)
    llm = LLM(backend="anthropic_api", model="claude-sonnet-4-20250514")
    llm = LLM(backend="ollama", model="deepseek-coder:6.7b")

    response = llm.generate(prompt, temperature=0.0)
    # Returns: LLMResponse(text, model, tokens_in, tokens_out, latency_ms)
"""

import json
import subprocess
import time
import urllib.request
from dataclasses import dataclass, field


@dataclass
class LLMResponse:
    text: str
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: float = 0.0
    backend: str = ""
    raw: dict = field(default_factory=dict)

    def extract_code(self) -> str:
        """Strip markdown code fences if present. Returns raw Python code."""
        text = self.text.strip()
        # Handle ```python ... ``` or ``` ... ```
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first line (```python or ```)
            lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            return "\n".join(lines)
        return text


class LLM:
    def __init__(self, backend="claude_cli", model=None, base_url=None):
        """
        backend: "claude_cli" | "anthropic_api" | "ollama"
        model: model name (defaults per backend)
        base_url: override URL for ollama (default: http://localhost:11434)
        """
        self.backend = backend
        self.base_url = base_url

        if backend == "claude_cli":
            self.model = model or "claude-cli"
        elif backend == "anthropic_api":
            self.model = model or "claude-sonnet-4-20250514"
            self._api_key = None  # cached on first use
        elif backend == "ollama":
            self.model = model or "deepseek-coder:6.7b"
            self.base_url = base_url or "http://localhost:11434"
        else:
            raise ValueError(f"Unknown backend: {backend}")

    def generate(self, prompt, temperature=0.0, max_tokens=8192) -> LLMResponse:
        """Send prompt to LLM, return structured response."""
        if self.backend == "claude_cli":
            return self._call_claude_cli(prompt)
        elif self.backend == "anthropic_api":
            return self._call_anthropic_api(prompt, temperature, max_tokens)
        elif self.backend == "ollama":
            return self._call_ollama(prompt, temperature)
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

    def _call_claude_cli(self, prompt) -> LLMResponse:
        """Call claude -p via subprocess, piping prompt through stdin."""
        start = time.monotonic()
        result = subprocess.run(
            ["claude", "-p"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=600,
        )
        latency = (time.monotonic() - start) * 1000

        if result.returncode != 0:
            raise RuntimeError(
                f"claude -p failed (exit {result.returncode}): {result.stderr}"
            )

        return LLMResponse(
            text=result.stdout,
            model="claude-cli",
            latency_ms=latency,
            backend="claude_cli",
        )

    def _call_anthropic_api(self, prompt, temperature, max_tokens) -> LLMResponse:
        """Call Anthropic API directly via urllib (no SDK dependency)."""
        import os

        if not self._api_key:
            self._api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self._api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set. "
                "Export it or use backend='claude_cli' instead."
            )

        payload = json.dumps({
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
            },
        )

        start = time.monotonic()
        # Retry with exponential backoff for rate limits
        max_retries = 5
        for attempt in range(max_retries):
            try:
                with urllib.request.urlopen(req, timeout=300) as resp:
                    data = json.loads(resp.read())
                break
            except urllib.error.HTTPError as e:
                if e.code in (429, 529) and attempt < max_retries - 1:
                    wait = 2 ** attempt * 5  # 5, 10, 20, 40, 80 seconds
                    print(f"  [llm] Rate limited (HTTP {e.code}), retrying in {wait}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait)
                    # Rebuild request (urlopen consumes it)
                    req = urllib.request.Request(
                        "https://api.anthropic.com/v1/messages",
                        data=payload,
                        headers={
                            "Content-Type": "application/json",
                            "x-api-key": self._api_key,
                            "anthropic-version": "2023-06-01",
                        },
                    )
                else:
                    # Read error body for debugging
                    try:
                        error_body = e.read().decode("utf-8")
                        print(f"  [llm] HTTP {e.code} error body: {error_body[:500]}")
                    except Exception:
                        pass
                    raise
        latency = (time.monotonic() - start) * 1000

        text = data["content"][0]["text"]
        usage = data.get("usage", {})

        return LLMResponse(
            text=text,
            model=self.model,
            tokens_in=usage.get("input_tokens", 0),
            tokens_out=usage.get("output_tokens", 0),
            latency_ms=latency,
            backend="anthropic_api",
            raw=data,
        )

    def _call_ollama(self, prompt, temperature) -> LLMResponse:
        """Call Ollama local API."""
        payload = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }).encode()

        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )

        start = time.monotonic()
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read())
        latency = (time.monotonic() - start) * 1000

        return LLMResponse(
            text=data.get("response", ""),
            model=self.model,
            tokens_in=data.get("prompt_eval_count", 0),
            tokens_out=data.get("eval_count", 0),
            latency_ms=latency,
            backend="ollama",
            raw=data,
        )

    def __repr__(self):
        return f"LLM(backend={self.backend!r}, model={self.model!r})"
