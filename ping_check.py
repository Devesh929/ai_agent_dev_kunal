import os
import csv
import json
import requests
from typing import Tuple

# ==== CONFIG ====
# Base; we will append the path from the CSV (e.g., "/chat/completions" or "/embeddings")
BASE_URL = "https://dh1-genwizardllm.accenture.com/testsrivarshan1/llm"

# Read your bearer from env var (recommended). Falls back to the hardcoded token ONLY if present.
TOKEN = os.getenv("GW_BEARER", "REPLACE_ME_WITH_ENV_VAR_GW_BEARER")

# Files
INPUT_CSV = "models_tasks.csv"    # <-- put your CSV here
OUTPUT_CSV = "results.csv"

# Common request settings
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}",
}
TIMEOUT = 30

# ==== HELPERS ====

def clean_path(task: str) -> str:
    """Normalize task -> path (e.g., '/chat/completions' or '/embeddings')."""
    task = (task or "").strip()
    if not task.startswith("/"):
        task = "/" + task
    return task

def build_url(path: str, model_id: str) -> str:
    return f"{BASE_URL}{path}?model_id={model_id}"

def make_payload(path: str) -> dict:
    """
    Provide minimal, valid payloads for each supported path.
    - For /chat/completions: send a simple user message.
    - For /embeddings: send a simple input string.
    Adjust here if your API expects additional fields.
    """
    if path == "/chat/completions":
        return {
            "messages": [
                {"role": "user", "content": "What is computing? one sentence"}
            ]
        }
    elif path == "/embeddings":
        return {
            "input": "Hello world"
        }
    else:
        # If an unexpected path shows up, still try echo payload
        return {"input": "health-check"}

def extract_response_text(path: str, data: dict) -> str:
    """
    Try to extract a concise 'response' string from the JSON payload.
    For chat: take the first completion content.
    For embeddings: report the vector length (too big to store raw).
    Fallback: return compact JSON.
    """
    try:
        if path == "/chat/completions":
            # Common schema: choices[0].message.content
            choices = data.get("choices") or []
            if choices:
                msg = choices[0].get("message") or {}
                content = msg.get("content")
                if content:
                    return content
            # Titan-style variants: data.get("output")?
            # Fallback to compact JSON
        elif path == "/embeddings":
            # Many embedding APIs return {"data": [{"embedding": [...]}], ...}
            arr = data.get("data") or []
            if arr and isinstance(arr, list):
                emb = arr[0].get("embedding")
                if isinstance(emb, list):
                    return f"embedding_length={len(emb)}"
                # Some return {"embedding": {...}} or different shapes
            # Fallback to compact JSON

        # Fallback: compact JSON (capped)
        txt = json.dumps(data, separators=(",", ":"))
        return txt if len(txt) <= 2000 else txt[:2000] + " ...[truncated]"

    except Exception:
        # Absolute fallback to raw compact JSON if parsing fails
        txt = json.dumps(data, separators=(",", ":"))
        return txt if len(txt) <= 2000 else txt[:2000] + " ...[truncated]"

def call_row(model_id: str, task: str) -> Tuple[str, bool]:
    """
    Returns (response_text, success_flag).
    On HTTP errors, returns the error text and success_flag=False.
    """
    path = clean_path(task)
    url = build_url(path, model_id)
    payload = make_payload(path)

    try:
        resp = requests.post(url, headers=HEADERS, json=payload, timeout=TIMEOUT, verify=False)
        # If your environment requires SSL verification, flip verify=True and ensure certs are set up.
        resp.raise_for_status()
        data = resp.json()
        return extract_response_text(path, data), True
    except requests.HTTPError as e:
        body = getattr(e.response, "text", "")
        return f"HTTP {e.response.status_code if e.response else ''}: {body}", False
    except requests.RequestException as e:
        return f"REQUEST_ERROR: {str(e)}", False
    except Exception as e:
        return f"UNEXPECTED_ERROR: {str(e)}", False

# ==== MAIN ====

def main():
    if not TOKEN or TOKEN == "REPLACE_ME_WITH_ENV_VAR_GW_BEARER":
        print("WARNING: No token in GW_BEARER. Set it via environment variable for real calls.")

    total = 0
    failures = 0
    rows_out = []

    # Read input
    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Expecting columns: model_id, task
        for row in reader:
            model_id = (row.get("model_id") or "").strip()
            task = (row.get("task") or "").strip()
            if not model_id or not task:
                # Skip malformed row
                continue

            total += 1
            path = clean_path(task)
            resp_text, ok = call_row(model_id, task)
            if not ok:
                failures += 1

            rows_out.append({
                "model_id": model_id,
                "path": path,
                "response": resp_text
            })

    # Write output
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["model_id", "path", "response"])
        writer.writeheader()
        writer.writerows(rows_out)

    print(f"Total attempted: {total}")
    print(f"Total failed:    {failures}")
    print(f"Wrote results to: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
