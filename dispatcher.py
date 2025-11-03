import os #s
from task_matcher import match_command

def dispatch(user_input):
    script = match_command(user_input)
    os.system(f"python scripts/{script}")