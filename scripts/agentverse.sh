#!/bin/bash

MAS="agentverse"
MAX_WORKERS=8

SUITES=("benign" "hijacking" "disruption" "disclosure")

TASK_DOMAINS=("code")

MALICIOUS_AGENTS=("solver")

defense=sandwich

for suite in "${SUITES[@]}"; do
  for task_domain in "${TASK_DOMAINS[@]}"; do
    for agent in "${MALICIOUS_AGENTS[@]}"; do
      echo "Running: suite=$suite, task_domain=$task_domain, malicious_agent=$agent"
      python3 benchmark.py \
        --mas "$MAS" \
        --suite "$suite" \
        --task_domain "$task_domain" \
        --malicious_agents "$agent" \
        --max_workers "$MAX_WORKERS" \
        --defense "$defense"
    done
  done
done