import json

math_500 = []
gsm8k = []
math = []

# 加载打分后的题目数据
with open("gsm8k_problem_scores.json", "r") as f:
    gsm8k = json.load(f)
    math.extend(gsm8k)

with open("math_problem_scores.json", "r") as f: 
    math_500 = json.load(f)
    math.extend(math_500)

print("Total problems:", len(math))

# ⭐️策略一：高挑战、高可分解、部分模糊（推荐策略）
# 要求：
# - complexity >= 4
# - decomposability >= 4
# - ambiguity >= 3

def select_by_rule(problem):
    scores = problem.get("scores", {})
    return (
        scores.get("complexity", 0) >= 4 and
        scores.get("decomposability", 0) >= 4 and
        scores.get("ambiguity", 0) <= 1
    )

# 进行筛选
selected_math = [item for item in math if select_by_rule(item)]

print("Selected problems:", len(selected_math))

for item in selected_math:
    if '####' in item["answer"]:
        item["answer"] = item["answer"].split("####")[-1].strip()
    if 'level' in item:
        del item["level"]
    del item['scores']

# 保存为新文件（可选）
with open("mathpi_math.json", "w") as f:
    json.dump(selected_math, f, indent=2)
