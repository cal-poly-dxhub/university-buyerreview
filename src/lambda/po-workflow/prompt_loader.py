import os

PARSER_PROMPTS_DIR = "Parser_Prompts"
TASK_PROMPTS_DIR = "Task_Prompts"

def load_prompts_from_dir(path: str) -> dict:
    prompts = {}
    for filename in os.listdir(path):
        if filename.endswith(".txt"):
            key = filename.replace(".txt", "").upper()
            with open(os.path.join(path, filename), "r") as f:
                prompts[key] = f.read()
    return prompts

PARSER_PROMPT_REGISTRY = load_prompts_from_dir(PARSER_PROMPTS_DIR)
TASK_PROMPT_REGISTRY = load_prompts_from_dir(TASK_PROMPTS_DIR)