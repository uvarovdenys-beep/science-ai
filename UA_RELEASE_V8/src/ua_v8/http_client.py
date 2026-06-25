"""
UA Test v8.0 — HTTP helpers and LLM call.
"""
import json
import urllib.request

from . import config


def http_get(url):
    """Simple GET returning parsed JSON."""
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def http_post(url, payload, timeout=None):
    """Simple POST returning parsed JSON."""
    if timeout is None:
        timeout = config.REQUEST_TIMEOUT
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def call_llm(model_id, messages, temp):
    """Send a chat completion request and return the text response."""
    result = http_post(config.CHAT_ENDPOINT, {
        "model": model_id,
        "messages": messages,
        "temperature": temp,
        "max_tokens": config.MAX_TOKENS,
    })
    msg = result["choices"][0]["message"]
    return (msg.get("content") or msg.get("reasoning_content") or "").strip()
