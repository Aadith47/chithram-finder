import os
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)

# Hard limits: after this long we stop waiting for a model and try the next one.
GEMINI_DEADLINE_SECONDS = 10
FALLBACK_DEADLINE_SECONDS = 12

# After this long in total, stop trying models and let the search use the user's own words.
TOTAL_BUDGET_SECONDS = 20

# Lite models are fast and plenty for turning a sentence into search queries.
GEMINI_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
]


class QueryInfo(BaseModel):
    main_subject: str = Field(description="the main thing in the image")
    environment: str = Field(description="where the scene takes place")
    device: str = Field(description="any device present, empty string if none")
    screen_content: str = Field(description="what is on a screen, empty string if not applicable")
    style: str = Field(description="visual style, e.g. realistic, illustration")
    queries: list[str] = Field(description="exactly 3 short image-search strings")


FALLBACK_MODELS = [
    "google/gemma-4-31b-it:free",
    "dots-studio/dots-3-note-preview:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "liquid/lfm-2.5-2.6b:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
]


def extract_text(response) -> str:
    # response.content can be a plain string, or a list of content blocks,
    # depending on the model/provider. Normalize both shapes into one string.
    if isinstance(response.content, str):
        return response.content

    parts = []
    for block in response.content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and "text" in block:
            parts.append(block["text"])

    return "\n".join(parts)


def parse_queries(text: str) -> list[str]:
    lines = text.strip().split("\n")

    queries = []
    for line in lines:
        cleaned = line.strip("-* \t")
        if cleaned:
            queries.append(cleaned)

    return queries


def build_prompt(context: str) -> str:
    return (
        "You analyze an image description and break it down into structured fields.\n"
        f"User description: {context}\n\n"
        "Return ONLY a JSON object, no markdown, no code fences, no extra text, "
        "with exactly these keys:\n"
        '  "main_subject": the main thing in the image\n'
        '  "environment": where the scene takes place\n'
        '  "device": any device present, or "" if none\n'
        '  "screen_content": what is on a screen, or "" if not applicable\n'
        '  "style": visual style, e.g. realistic, illustration\n'
        '  "queries": a list of exactly 3 short image-search strings\n\n'
        "Use an empty string for any field that doesn't apply."
    )


def parse_structured_response(text: str):
    # A model may still wrap JSON in a code fence even when told not to -
    # strip that off before trying to parse it.
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
        queries = data.get("queries", [])
        if isinstance(queries, list) and queries:
            return data, queries
    except (json.JSONDecodeError, AttributeError):
        pass

    # JSON parsing failed or came back empty - fall back to the old
    # line-by-line style so a query still gets generated either way.
    return None, parse_queries(text)


def run_with_deadline(function, seconds):
    """Run function, but stop waiting after `seconds`.

    A library's own timeout can restart whenever the server sends a little
    data, so a request stuck in a queue may never time out. This one is a
    real deadline. If it passes, the slow call is left to finish by itself
    in the background and we move on."""
    pool = ThreadPoolExecutor(max_workers=1)
    future = pool.submit(function)
    try:
        return future.result(timeout=seconds)
    finally:
        pool.shutdown(wait=False)


def ask_gemini(model_name, prompt):
    model = ChatGoogleGenerativeAI(model=model_name, max_retries=0)
    return model.with_structured_output(QueryInfo).invoke(prompt)


def get_queries(context: str):
    """
    Returns (structured_info, queries) for the given context.
    Tries Gemini models first (with an enforced schema), then falls through
    a list of OpenRouter free models. Returns (None, []) if all of them fail.
    """
    prompt = build_prompt(context)
    overall_start = time.time()

    for model_name in GEMINI_MODELS:
        started = time.time()
        try:
            result = run_with_deadline(lambda: ask_gemini(model_name, prompt), GEMINI_DEADLINE_SECONDS)
            print(f"(used {model_name}, structured output) {time.time() - started:.1f}s", flush=True)
            return result.model_dump(), result.queries

        except Exception as error:
            logger.warning("%s failed after %.1fs: %s: %s", model_name,
                           time.time() - started, type(error).__name__, error)

    api_key = os.getenv("OPENROUTER_API_KEY")

    for model_name in FALLBACK_MODELS:
        if time.time() - overall_start > TOTAL_BUDGET_SECONDS:
            logger.warning("Out of time after %.0fs, skipping the remaining models", time.time() - overall_start)
            break

        started = time.time()
        try:
            fallback_model = ChatOpenAI(
                model=model_name,
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                max_retries=0,
            )
            response = run_with_deadline(lambda: fallback_model.invoke(prompt), FALLBACK_DEADLINE_SECONDS)
            text = extract_text(response)
            print(f"(used OpenRouter fallback: {model_name}) {time.time() - started:.1f}s", flush=True)
            return parse_structured_response(text)

        except Exception as error:
            logger.warning("%s failed after %.1fs: %s: %s", model_name,
                           time.time() - started, type(error).__name__, error)

    logger.warning("All models failed, no queries generated")
    return None, []