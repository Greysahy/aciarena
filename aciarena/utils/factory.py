import yaml
import datetime
import typing
import inspect
import re
from .logger import MASLogger

DATASET_PIPELINE_MAPPING = {
    "gsm8k": "math",
    "math500": "math",
    "humaneval": "code",
    "mbpp": "code",
    "mmlu": "knowledge",
    "mmlu-pro": "knowledge",
    "gpqa": "knowledge",
}

MAS_CLASS_REGISTRY = {}
TASK_CLASS_REGISTRY = {}
ATTACK_CLASS_REGISTRY = {}
PIPELINE_CLASS_REGISTRY = {}
EXECUTOR_CLASS_REGISTRY = {}
EVALUATION_SUITE_CLASS_REGISTRY = {}
TOOL_REGISTRY = {}
TOOL_SCHEMAS = []


def register_mas(name: str):
    def decorator(cls):
        MAS_CLASS_REGISTRY[name.lower()] = cls
        return cls
    return decorator

def register_executor(name: str):
    def decorator(cls):
        EXECUTOR_CLASS_REGISTRY[name.lower()] = cls
        return cls
    return decorator

def register_task(name: str):
    def decorator(cls):
        TASK_CLASS_REGISTRY[name.lower()] = cls
        return cls
    return decorator

def register_attack_goal(name: str):
    def decorator(cls):
        cls_name = name.lower()
        if cls_name not in ATTACK_CLASS_REGISTRY:
            ATTACK_CLASS_REGISTRY[cls_name] = []
        ATTACK_CLASS_REGISTRY[cls_name].append(cls)
        return cls

    return decorator

def register_pipeline(name: str):
    def decorator(cls):
        PIPELINE_CLASS_REGISTRY[name.lower()] = cls
        return cls
    return decorator

def register_suite(name: str):
    def decorator(cls):
        EVALUATION_SUITE_CLASS_REGISTRY[name.lower()] = cls
        return cls
    return decorator

def register_tool():
    def decorator(func):
        sig = inspect.signature(func)
        type_hints = typing.get_type_hints(func)
        docstring = inspect.getdoc(func) or ""
        arg_descriptions = parse_google_style_args(docstring)

        properties = {}
        required = []
        for param_name, param in sig.parameters.items():
            param_type = type_hints.get(param_name, str)
            json_type = python_type_to_json_type(param_type)
            properties[param_name] = {
                "type": json_type,
                "description": arg_descriptions.get(param_name, f"Parameter {param_name}")
            }
            if param.default is inspect.Parameter.empty:
                required.append(param_name)

        tool_schema = {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": docstring.strip().split("\n")[0],
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }

        TOOL_REGISTRY[func.__name__.lower()] = func
        TOOL_SCHEMAS.append(tool_schema)
        return func
    return decorator

def parse_google_style_args(docstring: str) -> dict[str, str]:
    param_docs = {}
    if not docstring:
        return param_docs   
    
    args_section = re.search(r"Args:\s*(.*)", docstring, re.DOTALL)
    if not args_section:
        return param_docs

    lines = args_section.group(1).splitlines()
    current_param = None
    current_desc = []
    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = re.match(r"(\w+)\s*\([^)]+\):\s*(.*)", line)
        if match:
            if current_param:
                param_docs[current_param] = " ".join(current_desc).strip()
            current_param = match.group(1)
            current_desc = [match.group(2)]
        elif current_param:
            current_desc.append(line)

    if current_param:
        param_docs[current_param] = " ".join(current_desc).strip()

    return param_docs

def python_type_to_json_type(tp):
    origin = typing.get_origin(tp) or tp
    if origin in [str]:
        return "string"
    elif origin in [int]:
        return "integer"
    elif origin in [float]:
        return "number"
    elif origin in [bool]:
        return "boolean"
    elif origin in [list, typing.List]:
        return "array"
    elif origin in [dict, typing.Dict]:
        return "object"
    else:
        return "string"  # fallback

def build_mas(args, llm_config, logger):
    mas_name = args.mas.lower()
    mas_class = MAS_CLASS_REGISTRY.get(mas_name)

    if mas_class is None:
        raise ValueError(f"Unsupported MAS type: '{mas_name}'. Available types: {list(MAS_CLASS_REGISTRY.keys())}")
    
    kwargs = {
        "llm_config": llm_config,
        "logger": logger,
    }

    if len(args.malicious_agents) > 0:
        kwargs["malicious_agents"] = args.malicious_agents

    return mas_class(**kwargs)

def build_suite(args):
    suite_class = EVALUATION_SUITE_CLASS_REGISTRY.get(args.suite.lower())
    if suite_class is None:
        raise ValueError(f"Unsupported evaluation suite: '{args.suite.lower()}'. Available suites: {list(EVALUATION_SUITE_CLASS_REGISTRY.keys())}")

    return suite_class(args=args)

def build_attacks(args, llm_config):
    if args.suite.lower() == 'benign':
        attack_classes = ATTACK_CLASS_REGISTRY.get('none')
    else:
        attack_classes = ATTACK_CLASS_REGISTRY.get(args.suite.lower())
    # if attack_classes is None:
    #     raise ValueError(f"Unsupported attack goal: '{args.suite.lower()}'. Available goals: {list(ATTACK_CLASS_REGISTRY.keys())}")
    
    domain_attack_classes = ATTACK_CLASS_REGISTRY.get(f"{args.suite.lower()}_{args.task_domain.lower()}")
    # if domain_attack_classes is None:
        # raise ValueError(f"Unsupported attack goal with task domain: '{args.suite.lower()}'. Available goals: {list(ATTACK_CLASS_REGISTRY.keys())}")

    attacks = []
    if attack_classes:
        for attack_class in attack_classes:
            attacks.append(attack_class(args=args, llm_config=llm_config))

    if domain_attack_classes:
        for attack_class in domain_attack_classes:
            attacks.append(attack_class(args=args, llm_config=llm_config))

    if len(attacks) == 0:
        raise ValueError("No valid attack!")

    return attacks

def build_executor(args, llm_config):
    executor_name = args.attack_mode.lower()
    executor_class = EXECUTOR_CLASS_REGISTRY.get(executor_name)

    if executor_class is None:
        raise ValueError(f"Unsupported EXECUTOR type: '{executor_name}'. Available types: {list(EXECUTOR_CLASS_REGISTRY.keys())}")

    attacks = build_attacks(args, llm_config)
    return executor_class(attacks=attacks)

def build_logger(args):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%]S")
    log_name = f"{args.mas}_{args.suite}_{timestamp}"
    logger = MASLogger(
        meta_data=vars(args),
        name=log_name,
        log_dir=args.output_dir,
    )

    return logger

def execute_tool(tool_info: dict):
    name = tool_info.get("name", "empty_tool")
    args = tool_info.get("arguments", {})
    tool = TOOL_REGISTRY.get(name.lower())
    if tool is None:
        return f"Unknown tool: {name}"
    try:
        return tool(**args)
    except Exception as e:
        return f"Error: {e}"