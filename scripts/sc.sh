#!/bin/bash

MAS="sc"
MAX_WORKERS=8

SUITES=("benign")

TASK_DOMAINS=("math" "code")

MALICIOUS_AGENTS=("sc1" "sc2" "sc3" "sc4" "sc5" "aggregate")

for suite in "${SUITES[@]}"; do
  for task_domain in "${TASK_DOMAINS[@]}"; do
      echo "Running: suite=$suite, task_domain=$task_domain, malicious_agent=$agent"
      python3 benchmark.py \
        --mas "$MAS" \
        --suite "$suite" \
        --task_domain "$task_domain" \
        --max_workers "$MAX_WORKERS" 
    done
  done
done