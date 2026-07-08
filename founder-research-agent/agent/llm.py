"""
Thin Groq wrapper -- same pattern as the Deal Screening Agent's agent/llm.py
(kept duplicated rather than shared so this tool stays independently
runnable with zero dependency on the other two tools' folders).
"""
import json
import os
import re

from groq import Groq
from pydantic import BaseModel

GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")


def get_client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Copy .env.example to .env and add your key.")
    return Groq(api_key=api_key)


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    return match.group(1) if match else text


def call_json(system_prompt: str, user_prompt: str, schema: type[BaseModel], temperature: float = 0.1) -> BaseModel:
    client = get_client()
    messages = [
        {"role": "system", "content": system_prompt + "\n\nRespond with ONLY valid JSON, no prose, no markdown fences."},
        {"role": "user", "content": user_prompt},
    ]
    last_err = None
    for attempt in range(2):
        resp = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=1800,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content
        try:
            cleaned = _strip_code_fence(raw)
            data = json.loads(cleaned)
            return schema.model_validate(data)
        except Exception as e:
            last_err = e
            messages.append({"role": "assistant", "content": raw})
            messages.append(
                {
                    "role": "user",
                    "content": f"That was not valid JSON matching the required schema ({e}). "
                    f"Reply again with ONLY corrected valid JSON.",
                }
            )
    raise RuntimeError(f"LLM did not return valid JSON after retry: {last_err}")


def call_text(system_prompt: str, user_prompt: str, temperature: float = 0.3, max_tokens: int = 1200) -> str:
    client = get_client()
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content
