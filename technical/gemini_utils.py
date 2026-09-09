from typing import List, Dict, Any
from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError
from constant.constant import GEMINI_THINKING_TRACE_KEY, GEMINI_VISITED_WEBSITES_KEY
import time

__CACHE__ = {
    "genai_client": None,
}

def extract_gemini_response_text(response: types.GenerateContentResponse) -> str:
    """
    Return only the non-thought text from a Gemini response.

    response.text can hide the distinction between final-answer parts and
    thought parts. When parts are available, use their thought flag so parsing
    code never sees the thinking trace as model output.
    """
    texts = []
    for candidate in getattr(response, "candidates", None) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", None) or []:
            if getattr(part, "thought", False):
                continue
            text = getattr(part, "text", None)
            if text:
                texts.append(text)
    if texts:
        return "".join(texts)
    return response.text or ""

def extract_gemini_thinking_trace(response: types.GenerateContentResponse) -> str | None:
    """Return the concatenated Gemini thought parts, if the API returned any."""
    thoughts = []
    for candidate in getattr(response, "candidates", None) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", None) or []:
            if not getattr(part, "thought", False):
                continue
            text = getattr(part, "text", None)
            if text:
                thoughts.append(text)
    return "".join(thoughts) if thoughts else None

def extract_gemini_visited_websites(
    response: types.GenerateContentResponse,
) -> List[Dict[str, str]]:
    """Return the unique websites reported by Gemini's search grounding metadata."""
    websites = []
    seen_uris = set()
    for candidate in getattr(response, "candidates", None) or []:
        grounding_metadata = getattr(candidate, "grounding_metadata", None)
        for chunk in getattr(grounding_metadata, "grounding_chunks", None) or []:
            web = getattr(chunk, "web", None)
            uri = getattr(web, "uri", None)
            if not uri or uri in seen_uris:
                continue
            seen_uris.add(uri)
            websites.append({
                "title": getattr(web, "title", None) or "",
                "uri": uri,
            })
    return websites

def save_gemini_visited_websites(
    dp: Dict[str, Any],
    output_key: str,
    response: types.GenerateContentResponse,
    index: int | None = None,
) -> None:
    """Attach search-grounding websites to a datapoint when Gemini reports them."""
    websites = extract_gemini_visited_websites(response)
    if len(websites) == 0:
        return
    sources = dp.setdefault(GEMINI_VISITED_WEBSITES_KEY, {})
    if index is None:
        sources[output_key] = websites
        return
    values = sources.get(output_key)
    if not isinstance(values, list):
        values = []
    while len(values) <= index:
        values.append(None)
    values[index] = websites
    sources[output_key] = values

def save_gemini_thinking_trace(
    dp: Dict[str, Any],
    output_key: str,
    response: types.GenerateContentResponse,
    index: int | None = None
) -> None:
    """
    Attach a Gemini thinking trace to a datapoint.

    Single-call outputs are stored as:
        dp["gemini_thinking_trace"][output_key] = trace
    Multi-call outputs are stored as a list aligned with output_key.
    """
    save_gemini_visited_websites(dp, output_key, response, index=index)
    traces = dp.setdefault(GEMINI_THINKING_TRACE_KEY, {})
    trace = extract_gemini_thinking_trace(response)
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

def message2gemini_request(
    metadata: Dict[Any, Any],
    messages: List[Dict[str, str]],
    model: str,
    temperature: float = 0.0,
    thinking_level: str = None,
    web_search: bool = False
) -> Dict[str, Any]:
    config = {
        "system_instruction": messages[0]['content'],
        "temperature": temperature,
        "response_modalities": ["text"]
    }
    if thinking_level is not None:
        config["thinking_config"] = {
            "thinking_level": thinking_level,
            "include_thoughts": True
        }
    if web_search:
        config["tools"] = [{"google_search": {}}]
    return {
        "model": model,
        "contents": [
            {
                "role": message['role'],
                "parts": [
                    {"text": message['content']}
                ]
            } for message in messages[1:]
        ],
        "config": config,
        "metadata": metadata
    }
    
def call_gemini_one_by_one_api(
    messages: List[Dict[str, Any]],
    model: str,
    max_new_tokens: int = None,
    thinking_level: str = None,
    web_search: bool = False
) -> types.GenerateContentResponse:
    client = __CACHE__.get("genai_client", None)
    if not client:
        client = genai.Client()
        __CACHE__["genai_client"] = client
    config = types.GenerateContentConfig(
        temperature=0.0,
        max_output_tokens=max_new_tokens,
        system_instruction=messages[0]['content'],
        thinking_config=types.ThinkingConfig(
            thinking_level=thinking_level,
            include_thoughts=True
        ) if thinking_level is not None else None,
        tools=[types.Tool(google_search=types.GoogleSearch())] if web_search else None
    )
    try:
        response = client.models.generate_content(
            model=model,
            contents=[{"role": message["role"], "parts": [{"text": message["content"]}]} for message in messages[1:]],
            config=config
        )
    except ServerError as err:
        if err.code == 503:
            print(err)
            print("Sleep for 1 minute and retry...")
            time.sleep(60)
            return call_gemini_one_by_one_api(
                messages=messages,
                model=model,
                max_new_tokens=max_new_tokens,
                thinking_level=thinking_level,
                web_search=web_search
            )
        elif err.code == 429:
            print(err)
            print("Sleep for 1 minute and retry...")
            time.sleep(60)
            return call_gemini_one_by_one_api(
                messages=messages,
                model=model,
                max_new_tokens=max_new_tokens,
                thinking_level=thinking_level,
                web_search=web_search
            )
        else:
            raise err
    return response

def submit_gemini_job(
    requests: List[Dict[str, Any]],
    model: str
) -> types.BatchJob | None:
    """
    Submit a Gemini batch job with the given requests. Return the job information.
    Returns None if the requests list is empty (i.e., no API call is needed).
    """
    client = __CACHE__.get("genai_client", None)
    if not client:
        client = genai.Client()
        __CACHE__["genai_client"] = client
    if len(requests) == 0:
        print("No requests to submit for Gemini batch job.")
        return None
    try:
        batch_job = client.batches.create(
            model=model,
            src=requests,
        )
    except ClientError as err:
        if err.code == 503:
            print(err)
            print("Sleep for 10 minutes and retry...")
            time.sleep(600)
            batch_job = submit_gemini_job(
                requests=requests,
                model=model
            )
            return batch_job
        elif err.code == 429:
            print(err)
            print("Sleep for 10 minutes and retry...")
            time.sleep(600)
            batch_job = submit_gemini_job(
                requests=requests,
                model=model
            )
            return batch_job
        else:
            raise err
    return batch_job

def checkback(job_name: str) -> List[Dict[str, Any]]:
    """
    Checkback a Gemini batch job and return the list of responses.
    Args:
        job_name: the name of the Gemini batch job returned by submit_gemini_job
    Returns:
        A list of dicts containing the responses for each request.
    """
    client = __CACHE__.get("genai_client", None)
    if not client:
        client = genai.Client()
        __CACHE__["genai_client"] = client
    job = client.batches.get(name=job_name)
    if job.state == types.JobState.JOB_STATE_SUCCEEDED:
        responses = []
        for response in job.dest.inlined_responses:
            responses.append(response)
        return responses
    elif job.state in {types.JobState.JOB_STATE_CANCELLED, types.JobState.JOB_STATE_PAUSED, types.JobState.JOB_STATE_FAILED}:
        raise RuntimeError(f"Gemini batch job {job_name} failed with state {job.state}.")
    else:
        raise RuntimeError(f"Gemini batch job {job_name} is not completed yet. Current state: {job.state}.")
