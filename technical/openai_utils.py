from typing import List, Dict, Any
from openai import OpenAI, InternalServerError, RateLimitError
from openai.types.chat import ChatCompletion
from constant.constant import OPENAI_THINKING_TRACE_KEY
import base64
import io
import json
import os
import time


DEFAULT_OPENAI_BASE_URL = "https://proxy.vectorinstitute.ai/v1"
DEFAULT_OPENAI_API_KEY = os.getenv("VECTOR_KEY")
DEFAULT_OPENAI_MODEL = "gpt-oss-120b"

__CACHE__ = {
    "openai_client": None,
    "base_url": None,
    "api_key": None,
}


def _get_client(
    base_url: str = DEFAULT_OPENAI_BASE_URL,
    api_key: str | None = DEFAULT_OPENAI_API_KEY,
) -> OpenAI:
    base_url = base_url or DEFAULT_OPENAI_BASE_URL
    api_key = DEFAULT_OPENAI_API_KEY if api_key is None else api_key
    client = __CACHE__.get("openai_client", None)
    if (
        not client
        or __CACHE__["base_url"] != base_url
        or __CACHE__["api_key"] != api_key
    ):
        client = OpenAI(base_url=base_url, api_key=api_key)
        __CACHE__["openai_client"] = client
        __CACHE__["base_url"] = base_url
        __CACHE__["api_key"] = api_key
    return client


def extract_openai_response_text(response: ChatCompletion) -> str:
    """Return only the final-answer text from an OpenAI chat completion."""
    if not response.choices:
        return ""
    return response.choices[0].message.content or ""


def extract_openai_thinking_trace(response: ChatCompletion) -> str | None:
    """Return the reasoning content, if the OpenAI-compatible API returned it."""
    if not response.choices:
        return None
    message = response.choices[0].message
    trace = getattr(message, "reasoning_content", None)
    if trace is None:
        extra = getattr(message, "model_extra", None) or {}
        trace = extra.get("reasoning_content") or extra.get("reasoning")
    return trace or None


def save_openai_thinking_trace(
    dp: Dict[str, Any],
    output_key: str,
    response: ChatCompletion,
    index: int | None = None,
) -> None:
    """
    Attach an OpenAI thinking trace to a datapoint.

    Single-call outputs are stored as:
        dp["openai_thinking_trace"][output_key] = trace
    Multi-call outputs are stored as a list aligned with output_key.
    """
    traces = dp.setdefault(OPENAI_THINKING_TRACE_KEY, {})
    trace = extract_openai_thinking_trace(response)
    if index is None:
        traces[output_key] = trace
        return
    values = traces.get(output_key)
    if not isinstance(values, list):
        values = []
    while len(values) <= index:
        values.append(None)
    values[index] = trace
    traces[output_key] = values


def _encode_metadata(metadata: Dict[Any, Any]) -> str:
    serialized = json.dumps(metadata, separators=(",", ":"), sort_keys=True).encode()
    return base64.urlsafe_b64encode(serialized).decode().rstrip("=")


def _decode_metadata(custom_id: str) -> Dict[str, Any]:
    padding = "=" * (-len(custom_id) % 4)
    return json.loads(base64.urlsafe_b64decode(custom_id + padding))


def message2openai_request(
    metadata: Dict[Any, Any],
    messages: List[Dict[str, str]],
    model: str,
    temperature: float = 0.0,
    thinking_level: str = None,
    web_search: bool = False,
) -> Dict[str, Any]:
    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if thinking_level is not None:
        body["reasoning_effort"] = thinking_level
    if web_search:
        body["web_search_options"] = {}
    return {
        "custom_id": _encode_metadata(metadata),
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": body,
    }


def call_openai_one_by_one_api(
    messages: List[Dict[str, Any]],
    model: str,
    max_new_tokens: int | None = None,
    thinking_level: str = None,
    web_search: bool = False,
    base_url: str = DEFAULT_OPENAI_BASE_URL,
    api_key: str | None = DEFAULT_OPENAI_API_KEY,
) -> ChatCompletion:
    client = _get_client(base_url=base_url, api_key=api_key)
    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": 0.0,
    }
    if thinking_level is not None:
        kwargs["reasoning_effort"] = thinking_level
    if max_new_tokens is not None:
        kwargs["max_completion_tokens"] = max_new_tokens
    if web_search:
        kwargs["web_search_options"] = {}
    try:
        response = client.chat.completions.create(**kwargs)
    except (InternalServerError, RateLimitError) as err:
        print(err)
        print("Sleep for 1 minute and retry...")
        time.sleep(60)
        return call_openai_one_by_one_api(
            messages=messages,
            model=model,
            max_new_tokens=max_new_tokens,
            thinking_level=thinking_level,
            web_search=web_search,
            base_url=base_url,
            api_key=api_key,
        )
    return response


def submit_openai_job(
    requests: List[Dict[str, Any]],
    model: str = "gpt-oss-120b",
    base_url: str = DEFAULT_OPENAI_BASE_URL,
    api_key: str | None = DEFAULT_OPENAI_API_KEY,
):
    """
    Submit an OpenAI batch job with the given requests. Return the job information.
    Returns None if the requests list is empty (i.e., no API call is needed).
    """
    client = _get_client(base_url=base_url, api_key=api_key)
    if len(requests) == 0:
        print("No requests to submit for OpenAI batch job.")
        return None
    for request in requests:
        request["body"]["model"] = model
    contents = "\n".join(json.dumps(request) for request in requests).encode()
    batch_file = io.BytesIO(contents)
    batch_file.name = "openai_batch_requests.jsonl"
    try:
        input_file = client.files.create(file=batch_file, purpose="batch")
        batch_job = client.batches.create(
            input_file_id=input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )
    except (InternalServerError, RateLimitError) as err:
        print(err)
        print("Sleep for 10 minutes and retry...")
        time.sleep(600)
        batch_job = submit_openai_job(
            requests=requests,
            model=model,
            base_url=base_url,
            api_key=api_key,
        )
        return batch_job
    return batch_job


def checkback(
    job_name: str,
    base_url: str = DEFAULT_OPENAI_BASE_URL,
    api_key: str | None = DEFAULT_OPENAI_API_KEY,
) -> List[Dict[str, Any]]:
    """
    Check back an OpenAI batch job and return the list of responses.
    Args:
        job_name: the ID of the OpenAI batch job returned by submit_openai_job
    Returns:
        A list of dicts containing the response and metadata for each request.
    """
    client = _get_client(base_url=base_url, api_key=api_key)
    job = client.batches.retrieve(job_name)
    if job.status == "completed":
        contents = client.files.content(job.output_file_id).text
        responses = []
        for line in contents.splitlines():
            item = json.loads(line)
            item["metadata"] = _decode_metadata(item["custom_id"])
            responses.append(item)
        return responses
    elif job.status in {"cancelled", "cancelling", "expired", "failed"}:
        raise RuntimeError(f"OpenAI batch job {job_name} failed with state {job.status}.")
    else:
        raise RuntimeError(
            f"OpenAI batch job {job_name} is not completed yet. Current state: {job.status}."
        )
