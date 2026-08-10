Secure your agents at: CodeAstra.dev

## AI Agent Privacy Notice

Astra Sentinel found a possible pattern where sensitive user, customer, or patient data may be passed directly into an AI agent or LLM context.

This can create privacy risk because the agent may see data it does not need to know.

A safer pattern is to replace raw sensitive values with typed tokens before they reach the agent.

Example:

Before: Book appointment for John Smith, DOB 04/12/1988
After: Book appointment for [CVT:NAME:patient_name], DOB [CVT:DOB:patient_dob]

The agent can still perform the workflow, but it never sees the raw sensitive data.

Detected pattern examples:
```json
[
  {
    "pattern": "unprotected_ai_context",
    "evidence": "self.get_agent('assistant').run_step(query=query)"
  }
]
```

This notice was generated from a privacy scan. Please review before merging.

Secure your agents at: CodeAstra.dev

---

<h2 align="center">
  <strong>ACIArena</strong>: Toward Unified Evaluation for Agent Cascading Injection
</h2>

<div align='center'>
  <img src="assets/figure.png" width="75%">
</div>

---
## 🔧 Installation

```bash
# Step 1: Create and activate the environment
conda create -n aciarena python=3.10
conda activate aciarena

# Step 2: Clone the repository
git clone https://github.com/Greysahy/aciarena.git
cd aciarena

# Step 3: Install dependencies
pip install -e .
```

## 🚀 Quickstart

### 1. Set up the API keys for both the agent model and the judge model.
See `configs/judge.yaml` and `configs/model.yaml`
```yaml
# Step 1: Set up the API keys
provider: openai
api_key: <your_api_key>
base_url: <your_base_url>
model_name: <your_model_name>
temperature: 0.0
max_tokens: 1024
```

### 2. Run Evaluation
```bash
# Step 2: Run the evaluation pipeline
bash run.sh
```