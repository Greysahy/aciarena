#!/bin/bash

MAS="metagpt"
MAX_WORKERS=8

SUITES=("disclosure")

TASK_DOMAINS=("code")

defense=sandwich

for suite in "${SUITES[@]}"; do
  for task_domain in "${TASK_DOMAINS[@]}"; do
    
    # 根据suite类型设置对应的恶意agent
    case $suite in
      "hijacking")
        malicious_agent="engineer"
        ;;
      "disruption")
        malicious_agent="architect"
        ;;
      "disclosure")
        malicious_agent="qa_engineer"
        ;;
      "benign")
        # benign suite不设置恶意agent
        echo "Running: suite=$suite, task_domain=$task_domain"
        python3 benchmark.py \
          --mas "$MAS" \
          --suite "$suite" \
          --task_domain "$task_domain" \
          --max_workers "$MAX_WORKERS" \
          --defense "$defense"
        continue
        ;;
    esac
    
    echo "Running: suite=$suite, task_domain=$task_domain, malicious_agent=$malicious_agent"
    python3 benchmark.py \
      --mas "$MAS" \
      --suite "$suite" \
      --task_domain "$task_domain" \
      --malicious_agents "$malicious_agent" \
      --max_workers "$MAX_WORKERS" \
      --defense "$defense"
  done
done