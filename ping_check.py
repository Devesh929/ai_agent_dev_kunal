import os
import csv
import json
import requests
from typing import Tuple, Dict, List
from pathlib import Path

# ==== CONFIG ====
BASE_URL = "https://dh1-genwizardllm.accenture.com/testsrivarshan1/llm"
TOKEN = os.getenv("GW_BEARER", "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6IkhTMj")

# Prefer models_tasks.csv; fall back to models.csv if present
DEFAULT_INPUTS = ["models.csv"]
OUTPUT_CSV = "results.csv"

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}",
}
TIMEOUT = 30


# ==== HELPERS ====

def clean_path(task: str) -> str:
    task = (task or "").strip()
    if not task.startswith("/"):
        task = "/" + task
    return task

def build_url(path: str, model_id: str) -> str:
    return f"{BASE_URL}{path}?model_id={model_id}"

def make_payload(path: str) -> dict:
    if path == "/chat/completions":
        return {"messages": [{"role": "user", "content": "What is computing? one sentence"}]}
    elif path == "/embeddings":
        return {"input": "Hello world"}
    else:
        return {"input": "health-check"}

def extract_response_text(path: str, data: dict) -> str:
    try:
        if path == "/chat/completions":
            choices = data.get("choices") or []
            if choices:
                msg = choices[0].get("message") or {}
                content = msg.get("content")
                if content:
                    return content
        elif path == "/embeddings":
            arr = data.get("data") or []
            if arr and isinstance(arr, list):
                emb = arr[0].get("embedding")
                if isinstance(emb, list):
                    return f"embedding_length={len(emb)}"
        txt = json.dumps(data, separators=(",", ":"))
        return txt if len(txt) <= 2000 else txt[:2000] + " ...[truncated]"
    except Exception:
        txt = json.dumps(data, separators=(",", ":"))
        return txt if len(txt) <= 2000 else txt[:2000] + " ...[truncated]"

def call_row(model_id: str, task: str) -> Tuple[str, bool]:
    path = clean_path(task)
    url = build_url(path, model_id)
    payload = make_payload(path)
    print(f"[DEBUG] CALLING -> url={url} payload={json.dumps(payload)}")
    try:
        resp = requests.post(url, headers=HEADERS, json=payload, timeout=TIMEOUT, verify=False)
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

def normalize(s: str) -> str:
    # strip spaces + BOM, lower, replace inner spaces with underscore
    return (s or "").lstrip("\ufeff").strip().lower().replace(" ", "_")

def detect_header_mapping(fieldnames: List[str]) -> Dict[str, str]:
    """
    Map canonical keys -> actual keys in the file.
    canonical: model_id, task
    accepts synonyms and BOM variants.
    """
    norm_to_actual = {normalize(fn): fn for fn in fieldnames}
    mapping = {}

    # model_id synonyms
    for candidate in ["model_id", "model", "modelname", "model_name", "id"]:
        if candidate in norm_to_actual:
            mapping["model_id"] = norm_to_actual[candidate]
            break

    # task/endpoint/path synonyms
    for candidate in ["task", "endpoint", "path", "api", "route"]:
        if candidate in norm_to_actual:
            mapping["task"] = norm_to_actual[candidate]
            break

    return mapping

def choose_input_file() -> str:
    env_file = os.getenv("GW_INPUT_CSV")
    candidates = [env_file] if env_file else []
    candidates += DEFAULT_INPUTS
    for c in candidates:
        if c and Path(c).is_file():
            return c
    # fall back to the first default even if missing, for a clear error later
    return candidates[0] if candidates else DEFAULT_INPUTS[0]

def print_csv_preview(path: str, limit: int = 200) -> None:
    print(f"\n===== CSV PREVIEW ({path}) =====")
    try:
        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                ln = line.rstrip("\n")
                print(f"{i:04d}: {ln}")
                if i >= limit:
                    print(f"... (truncated preview at {limit} lines)")
                    break
    except UnicodeDecodeError:
        # try fallback encoding
        with open(path, "r", encoding="utf-8-sig") as f:
            for i, line in enumerate(f, start=1):
                ln = line.rstrip("\n")
                print(f"{i:04d}: {ln}")
                if i >= limit:
                    print(f"... (truncated preview at {limit} lines)")
                    break
    print("===== END PREVIEW =====\n")

# ==== MAIN ====

def main():
    if not TOKEN or TOKEN == "REPLACE_ME_WITH_ENV_VAR_GW_BEARER":
        print("[WARN] No token in GW_BEARER. Set it via environment variable for real calls.")

    input_csv = choose_input_file()
    print(f"[INFO] Using input CSV: {input_csv}")
    if not Path(input_csv).is_file():
        print(f"[ERROR] File not found: {input_csv}")
        return

    print_csv_preview(input_csv, limit=200)

    rows_read = 0
    attempted = 0
    failures = 0
    skipped = 0
    skip_reasons = {}

    rows_out = []

    # Read input with DictReader and show actual fieldnames
    with open(input_csv, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        print(f"[INFO] Detected headers: {fieldnames}")

        mapping = detect_header_mapping(fieldnames)
        print(f"[INFO] Header mapping resolved to: {mapping}")

        if "model_id" not in mapping or "task" not in mapping:
            print("[ERROR] Could not find required columns. Need headers for model_id and task (synonyms accepted).")
            print("[HINT] Present headers: ", fieldnames)
            return

        model_key = mapping["model_id"]
        task_key = mapping["task"]

        for line_no, row in enumerate(reader, start=2):  # start=2 accounts for header line at 1
            rows_read += 1
            # Log the raw row
            print(f"[DEBUG] Row {line_no} raw: {row}")

            # Extract and trim
            model_id = (row.get(model_key) or "").strip()
            task = (row.get(task_key) or "").strip()

            # Validate row
            reasons = []
            if not model_id:
                reasons.append("empty model_id")
            if not task:
                reasons.append("empty task")

            # Optional: treat lines with all empty values as blank rows
            if not any((v or "").strip() for v in row.values()):
                reasons.append("blank_line")

            if reasons:
                skipped += 1
                reason_key = ";".join(sorted(reasons))
                skip_reasons[reason_key] = skip_reasons.get(reason_key, 0) + 1
                print(f"[SKIP] Row {line_no} skipped -> {reason_key}")
                continue

            attempted += 1
            path = clean_path(task)
            print(f"[INFO] Row {line_no} attempting -> model_id='{model_id}' path='{path}'")
            resp_text, ok = call_row(model_id, task)
            if not ok:
                failures += 1
                print(f"[FAIL] Row {line_no} request failed")

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

    print("\n===== RUN SUMMARY =====")
    print(f"Rows read:       {rows_read}")
    print(f"Total attempted: {attempted}")
    print(f"Total failed:    {failures}")
    print(f"Total skipped:   {skipped}")
    if skip_reasons:
        print("Skip reasons:")
        for k, v in skip_reasons.items():
            print(f"  - {k}: {v}")
    print(f"Wrote results to: {OUTPUT_CSV}")
    print("===== END SUMMARY =====")

if __name__ == "__main__":
    main()
