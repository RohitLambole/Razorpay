"""
LLM integration module
- call_llm: wrap OpenAI ChatCompletion (or other provider)
- parse_action: parse model output (expected to be JSON) and validate against pydantic LLMAction
- persist trace via db.create_llm_trace
"""
from typing import Any, Dict
import os
import json
from datetime import datetime

import openai
from pydantic import ValidationError

from . import db
from .schemas import LLMAction

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not OPENAI_API_KEY:
    # do not raise at import time in environments without AI keys; functions will error if used
    pass
else:
    openai.api_key = OPENAI_API_KEY


def call_llm(system_prompt: str, user_prompt: str, max_tokens: int = 512, temperature: float = 0.0) -> Dict[str, Any]:
    """Call OpenAI ChatCompletion and return the raw assistant message text and the full response."""
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not configured")
    resp = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    # extract assistant message
    assistant_msg = resp.choices[0].message.content
    return {"assistant": assistant_msg, "raw": resp}


def parse_action(assistant_text: str) -> Dict[str, Any]:
    """Parse assistant text as JSON and validate against LLMAction schema.
    The model is expected to emit a JSON object only (or with surrounding markdown code fences)."""
    # extract JSON block if inside triple backticks
    txt = assistant_text.strip()
    if txt.startswith("```") and txt.endswith("```"):
        # strip code fences
        parts = txt.split("\n")
        # remove first and last lines
        txt = "\n".join(parts[1:-1]).strip()

    # attempt to parse JSON
    try:
        payload = json.loads(txt)
    except Exception as e:
        raise ValueError(f"LLM output is not valid JSON: {e}\nOutput:\n{txt}")

    # validate using pydantic
    try:
        action = LLMAction.parse_obj(payload)
    except ValidationError as e:
        raise ValueError(f"LLM action validation failed: {e}")

    return action.dict()


def call_and_parse(system_prompt: str, user_prompt: str, session_id: str = None, save_trace: bool = True) -> Dict[str, Any]:
    resp = call_llm(system_prompt, user_prompt)
    assistant_text = resp["assistant"]
    parsed = None
    error = None
    try:
        parsed = parse_action(assistant_text)
    except Exception as e:
        error = str(e)

    # save trace
    if save_trace:
        db.create_llm_trace({
            "session_id": session_id,
            "model": OPENAI_MODEL,
            "prompt": user_prompt,
            "response": {"assistant": assistant_text, "raw": resp["raw"]},
            "tool_calls": parsed if parsed else {"error": error},
            "deterministic_seed": None,
            "created_at": datetime.utcnow().isoformat()
        })

    if error:
        raise RuntimeError(error)

    return parsed
