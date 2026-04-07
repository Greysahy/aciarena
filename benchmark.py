from aciarena.utils import build_suite
import argparse
import json
import os
import yaml

def main(args):
    model_config = yaml.safe_load(open("configs/model.yaml"))
    model_name = model_config.get("model_name", "unknown").replace("/", "_")

    save_dir = f"logs/{model_name}/{args.task_domain}/{args.mas}/{args.suite}"
    os.makedirs(save_dir, exist_ok=True)

    suite = build_suite(args)
    result = suite.eval()
    print("Evaluation Results:", result)

    save_path = os.path.join(save_dir, "result.json")

    # 如果文件已存在，先加载内容
    if os.path.exists(save_path):
        with open(save_path, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []  # 如果文件损坏/为空，初始化为空列表
    else:
        data = []

    # 追加新的结果
    data.append({
        "meta_data": vars(args),
        "result": result
    })

    # 写回文件
    with open(save_path, "w") as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="aciarena Configuration")
    parser.add_argument(
        "--mas",
        type=str,
        default="autogen",
        help="The structure of the multi-agent system. Options typically include 'linear', 'tree', or custom topologies."
    )
    parser.add_argument(
        "--suite",
        type=str,
        default="hijacking",
        help="Specifies the evaluation suite."
    )
    parser.add_argument(
        "--attack_mode",
        type=str,
        default="continuous",
        help="Specifies how the attack is executed."
    )
    parser.add_argument(
        "--defense",
        type=str,
        default="none",
        help="Specifies the defense."
    )
    parser.add_argument(
        "--task_domain",
        type=str,
        default="code",
        help="Benign task domain."
    )
    parser.add_argument(
        "--max_workers",
        type=int,
        default=4,
        help="The max workers for evaluation."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="logs",
        help="Directory to save output files such as logs, results, or checkpoints."
    )
    parser.add_argument(
        "--malicious_agents",
        nargs='+',
        type=str,
        default=[],
        help="A list of agent names to target in the attack (e.g., 'agent_1', 'agent_2'). You can specify multiple agents separated by space."
    )
    args = parser.parse_args()
    main(args)
    