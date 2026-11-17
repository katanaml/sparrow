"""
Request-scoped collector for backend usage statistics (e.g. Mistral token counts).

How it is used:
  - api.py calls start() before running the pipeline and summarize() after it.
  - The sparrow-parse pipeline calls add(usage) for every inference run it makes.
  - Outside an API request (CLI, tests) no collector is started, so add() does nothing.

The collector is stored in a ContextVar, so every request gets its own list and requests don't mix.
"""
from contextvars import ContextVar


_collector: ContextVar = ContextVar("usage_collector", default=None)


def start():
    """Start a fresh collector for the current request."""
    _collector.set([])


def add(usage):
    """Add the usage dicts of one inference run. Does nothing if no collector was started."""
    collector = _collector.get()
    if collector is None or not usage:
        return
    collector.extend(usage)


def summarize():
    """
    Sum the token counts over everything collected for the current request.

    Returns a dict {"calls", "prompt_tokens", "completion_tokens", "total_tokens"},
    or None when nothing with token counts was collected (OCR-only calls, MLX, vLLM, ...).
    """
    collector = _collector.get()
    if not collector:
        return None

    chat_entries = [u for u in collector if u.get("prompt_tokens") is not None]
    if not chat_entries:
        return None

    prompt_tokens = sum(u.get("prompt_tokens") or 0 for u in chat_entries)
    completion_tokens = sum(u.get("completion_tokens") or 0 for u in chat_entries)
    return {
        "calls": len(chat_entries),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }