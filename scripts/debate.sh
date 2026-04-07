MAS="llm_debate"
MAX_WORKERS=8

SUITES=("hijacking" "disruption" "disclosure")

TASK_DOMAINS=( "code" "math")

MALICIOUS_AGENTS=("debater_0" "debater_1" "debater_2" "aggregator")

for suite in "${SUITES[@]}"; do
  for task_domain in "${TASK_DOMAINS[@]}"; do
    for agent in "${MALICIOUS_AGENTS[@]}"; do
      echo "Running: suite=$suite, task_domain=$task_domain, malicious_agent=$agent"
      python3 benchmark.py \
        --mas "$MAS" \
        --suite "$suite" \
        --task_domain "$task_domain" \
        --malicious_agents "$agent" \
        --max_workers "$MAX_WORKERS" 
    done
  done
done
