"""
UA Test v8.0 — HTTP helpers and LLM call.
"""
import json
import time
import urllib.error
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
    """Send a chat completion request and return the text response.

    Retries on transient LM Studio failures (HTTP 5xx, sporadic 400, and
    connection/timeout errors) with linear backoff. Raises the last error
    only after exhausting RETRY_MAX_ATTEMPTS.
    """
    payload = {
        "model": model_id,
        "messages": messages,
        "temperature": temp,
        "max_tokens": config.MAX_TOKENS,
    }
    last_err = None
    for attempt in range(1, config.RETRY_MAX_ATTEMPTS + 1):
        try:
            result = http_post(config.CHAT_ENDPOINT, payload)
            msg = result["choices"][0]["message"]
            return (msg.get("content")
                    or msg.get("reasoning_content") or "").strip()
        except urllib.error.HTTPError as e:
            # Retry server errors and transient 400s; re-raise other 4xx.
            if e.code >= 500 or e.code == 400:
                last_err = e
            else:
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last_err = e
        if attempt < config.RETRY_MAX_ATTEMPTS:
            time.sleep(config.RETRY_BACKOFF_SEC * attempt)
    raise last_err
