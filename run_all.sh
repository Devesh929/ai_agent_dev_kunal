#!/usr/bin/env bash
set -euo pipefail

# ========= CONFIG =========
INPUT_CSV="models.csv"     # your input CSV (columns: model_id,task)
OUTPUT_CSV="results.csv"   # output CSV with results
BASE_URL="https://dh1-genwizardllm.accenture.com/testsrivarshan1/llm"

# Read token from environment (recommended).
# Usage: export TOKEN='YOUR_BEARER_TOKEN' before running the script.
: "${TOKEN:?ERROR: Please set your bearer token first, e.g.  export TOKEN='YOUR_BEARER_TOKEN'}"

# ========= HELPERS =========
# URL-encode model_id for safe inclusion in query string.
# We handle common reserved characters. Add more if you need.
urlencode_model_id() {
  local s="$1"
  s="${s//%/%25}"   # must encode % first
  s="${s// /%20}"
  s="${s//\//%2F}"
  s="${s//:/%3A}"
  s="${s//+/%2B}"
  s="${s//?/%3F}"
  s="${s//#/%23}"
  s="${s//&/%26}"
  s="${s//=/%3D}"
  echo -n "$s"
}

# Escape JSON/newlines/quotes so the response fits cleanly as one CSV cell
csv_escape() {
  local s="$1"
  s="${s//$'\r'/ }"
  s="${s//$'\n'/ }"
  s="${s//\"/\"\"}"
  echo -n "\"$s\""
}

# ========= INIT OUTPUT =========
echo "model_id,task,http_code,response" > "$OUTPUT_CSV"

# ========= MAIN LOOP =========
# CSV: model_id,task (skip header)
tail -n +2 "$INPUT_CSV" | while IFS=, read -r model_id task; do
  # Trim whitespace
  model_id="${model_id#"${model_id%%[![:space:]]*}"}"; model_id="${model_id%"${model_id##*[![:space:]]}"}"
  task="${task#"${task%%[![:space:]]*}"}";         task="${task%"${task##*[![:space:]]}"}"

  [[ -z "$model_id" || -z "$task" ]] && continue

  # Payload switch by task
  if [[ "$task" == "/embeddings" ]]; then
    # Adjust "input" as needed for your embeddings endpoint
    PAYLOAD='{"input":"What is computing?"}'
  else
    # Default to chat-style payload
    PAYLOAD='{"messages":[{"role":"user","content":"What is computing? one sentence"}]}'
  fi

  enc_model_id="$(urlencode_model_id "$model_id")"
  url="${BASE_URL}${task}?model_id=${enc_model_id}"

  resp_and_code="$(curl -sS -X POST "$url" \
    -H 'Content-Type: application/json' \
    -H "Authorization: Bearer $TOKEN" \
    --data "$PAYLOAD" \
    -w $'\n%{http_code}')"

  http_code="$(printf '%s\n' "$resp_and_code" | tail -n 1)"
  body="$(printf '%s\n' "$resp_and_code" | sed '$d')"

  echo "${model_id},${task},${http_code},$(csv_escape "$body")" >> "$OUTPUT_CSV"
  echo "[$http_code] $model_id  $task"
done

echo "Done → $OUTPUT_CSV"
