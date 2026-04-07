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