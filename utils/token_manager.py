from typing import Tuple

from .summarize import summarize_resume

# You can tune this; we keep it small for safety
MAX_PROMPT_TOKENS = 3000


def count_tokens(client, model: str, contents) -> int:
    """
    Wrapper around Gemini token counter.
    """
    result = client.models.count_tokens(model=model, contents=contents)
    # In Google docs, result.total_tokens is used
    return getattr(result, "total_tokens", result)


def ensure_prompt_within_limit(client, model: str, prompt: str,
                               max_tokens: int = MAX_PROMPT_TOKENS) -> Tuple[str, int]:
    """
    Ensures the final prompt is within token limits.
    If too long, uses heuristic summarization and truncation.
    """
    total = count_tokens(client, model, prompt)
    if total <= max_tokens:
        return prompt, total

    # First try: summarize only the resume part
    summarized = summarize_resume(prompt, max_chars=4000)
    total2 = count_tokens(client, model, summarized)

    if total2 <= max_tokens:
        return summarized, total2

    # Final hard cut as a fallback
    ratio = max_tokens / max(total2, 1)
    cutoff = max(1000, int(len(summarized) * ratio))
    trimmed = summarized[:cutoff]
    final_tokens = min(count_tokens(client, model, trimmed), max_tokens)
    return trimmed, final_tokens
