#!/bin/bash
# Format Python files after agent edits
# Runs: isort -> ruff format -> ruff fix

input=$(cat)
file_path=$(echo "$input" | jq -r '.file_path')

# Only process Python files
if [[ "$file_path" != *.py ]]; then
  echo '{"status": "skipped", "reason": "not a python file"}'
  exit 0
fi

# Run isort to sort imports
output=$(isort "$file_path" 2>&1)
if [[ $? -ne 0 ]]; then
  echo "{\"status\": \"error\", \"tool\": \"isort\", \"output\": $(echo "$output" | jq -Rs .)}"
  exit 1
fi

# Run ruff format
output=$(ruff format "$file_path" 2>&1)
if [[ $? -ne 0 ]]; then
  echo "{\"status\": \"error\", \"tool\": \"ruff format\", \"output\": $(echo "$output" | jq -Rs .)}"
  exit 1
fi

# Run ruff fix (auto-fix linting issues)
output=$(ruff check --fix "$file_path" 2>&1)
if [[ $? -ne 0 ]]; then
  echo "{\"status\": \"error\", \"tool\": \"ruff check\", \"output\": $(echo "$output" | jq -Rs .)}"
  exit 1
fi

echo '{"status": "okay"}'
exit 0
