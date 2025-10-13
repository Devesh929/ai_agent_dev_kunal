#!/usr/bin/env python3
# debug_runner.py
import csv, json, time, sys
from pathlib import Path
import requests

# ======= HARD-CODED INPUTS =======
BASE_ROOT    = "https://dh1-genwizardllm.accenture.com/testsrivarshan1/llm"
# ACCESS_TOKEN = "PASTE_YOUR_BEARER_TOKEN_HERE"          # <-- check expiry & audience
USECASE_ID   = "Internaldev"

# If your APIM uses a subscription key (common):
APIM_SUBSCRIPTION_KEY = ""  # e.g. "xxxxxxxxxxxxxxxxxxxxxxxxxx" or leave blank

# If your gateway needs a tenant/org header, set it here (or leave blank):
EXTRA_HEADERS = {
    # "X-Tenant-Id": "your-tenant-id",
}

INPUT_CSV    = "models.csv"   # columns: model_id,path
OUTPUT_CSV   = "results.csv"

CHAT_PROMPT  = "what is computing? in one sentence"
EMBED_INPUT  = "hello world"

TIMEOUT_SEC  = 45

# If your CSV has plain names (e.g. "gpt-4o-standard") but the API expects
# "azure/gpt-4o-standard" or "openai/gpt-4o-standard", set try_prefixes:
TRY_PREFIXES = [""]  # order matters; "" means try as-is
# =================================

BASE_HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "UseCaseId": USECASE_ID,
    "Content-Type": "application/json",
}
if APIM_SUBSCRIPTION_KEY:
    BASE_HEADERS["Ocp-Apim-Subscription-Key"] = APIM_SUBSCRIPTION_KEY
BASE_HEADERS.update(EXTRA_HEADERS)

def payload_for_path(path: str):
    p = (path or "").lower()
    if "/embed" in p:
        return {"input": EMBED_INPUT}
    return {"messages": [{"role": "user", "content": CHAT_PROMPT}]}

def load_rows(csv_path: str):
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            mid = (row.get("model_id") or row.get("model") or "").strip()
            path = (row.get("path") or "/chat/completions").strip()
            if not mid:
                continue
            if not path.startswith("/"):
                path = "/" + path
            rows.append((mid, path))
    if not rows:
        sys.exit("No rows found in models_with_paths.csv (need headers model_id,path).")
    return rows

def try_one(url: str, model_id: str, body: dict):
    """Return (status_code, latency_ms, text, headers)"""
    start = time.perf_counter()
    print(url)
    resp = requests.post(url, params={"model_id": model_id},
                         headers=BASE_HEADERS, json=body, timeout=TIMEOUT_SEC,verify=False)
    latency = int((time.perf_counter() - start) * 1000)
    return resp.status_code, latency, resp.text, dict(resp.headers)

def extract_snippet(text: str) -> str:
    try:
        j = json.loads(text)
        for keys in [
            ("choices", 0, "message", "content"),
            ("data", 0, "embedding"),
            ("error",),
            ("message",),
            ("detail",),
        ]:
            cur = j
            ok = True
            for k in keys:
                if isinstance(k, int):
                    if isinstance(cur, list) and len(cur) > k:
                        cur = cur[k]
                    else:
                        ok = False; break
                else:
                    if isinstance(cur, dict) and k in cur:
                        cur = cur[k]
                    else:
                        ok = False; break
            if ok and cur is not None:
                return str(cur).replace("\n", " ")[:180]
    except Exception:
        pass
    return (text or "").replace("\n", " ")[:180]

def run_all():
    rows = load_rows(INPUT_CSV)
    Path(OUTPUT_CSV).write_text("model_id,path,final_model_id,status,http_code,latency_ms,snippet\n", encoding="utf-8")

    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as out:
        w = csv.writer(out)
        for original_mid, path in rows:
            url = f"{BASE_ROOT}{path}"
            body = payload_for_path(path)

            last_status = 0
            last_text = ""
            last_headers = {}
            final_mid_used = original_mid

            # Try with optional prefixes if 403/404 (namespace mismatch)
            for prefix in TRY_PREFIXES:
                candidate_mid = original_mid if original_mid.startswith(prefix) or not prefix else prefix + original_mid
                try:
                    status, latency, text, headers = try_one(url, candidate_mid, body)
                    snippet = extract_snippet(text)
                    if 200 <= status < 400:
                        print(f"{original_mid} [{path}] -> {candidate_mid}: ok ({status}) {latency} ms")
                        w.writerow([original_mid, path, candidate_mid, "ok", status, latency, snippet])
                        break
                    else:
                        print(f"{original_mid} [{path}] -> {candidate_mid}: fail ({status}) {latency} ms | {snippet}")
                        last_status, last_text, last_headers, final_mid_used = status, text, headers, candidate_mid
                        # Only keep trying alternatives if it's likely a namespace/path issue
                        if status not in (403, 404):
                            # unlikely to succeed with other prefixes; stop trying
                            w.writerow([original_mid, path, candidate_mid, "fail", status, latency, snippet])
                            break
                except requests.RequestException as e:
                    print(f"{original_mid} [{path}] -> {candidate_mid}: network error {str(e)[:160]}")
                    last_status, last_text, final_mid_used = 0, str(e), candidate_mid
            else:
                # loop exhausted (all prefixes tried) and none succeeded
                snippet = extract_snippet(last_text)
                w.writerow([original_mid, path, final_mid_used, "fail", last_status, "", snippet])

            # On first persistent failure, dump debug once so you can see policy text
            if last_status and last_status >= 400:
                print("\n--- DEBUG (first failure for this row) ---")
                print(f"URL: {url}")
                print(f"model_id: {final_mid_used}")
                print("Headers sent:", BASE_HEADERS)
                print("Response status:", last_status)
                # Print a short response body and a couple of headers
                print("Response body (first 800 chars):")
                print(last_text[:800])
                print("Response headers (subset):", {k: last_headers.get(k) for k in ["content-type","www-authenticate","x-apim-trace-location","date"]})
                print("--- END DEBUG ---\n")

if __name__ == "__main__":
    run_all()
    print(f"\nResults → {OUTPUT_CSV}")
