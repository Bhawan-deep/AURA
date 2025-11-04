import os
import logging
from typing import Tuple

from task_matcher import match_command, run_script, INDEX_FILE

# Configuration
CONFIDENCE_THRESHOLD = float(os.getenv("AURA_CONF_THRESH", "0.75"))
DRY_RUN_DEFAULT = True
LOG_PATH = os.getenv("AURA_DISPATCH_LOG", "logs/dispatch.log")

# Logging
os.makedirs(os.path.dirname(LOG_PATH) or ".", exist_ok=True)
logger = logging.getLogger("dispatcher")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(LOG_PATH)
handler.setFormatter(logging.Formatter("%(asctime)s\t%(levelname)s\t%(message)s"))
logger.addHandler(handler)


def _prompt_confirm(prompt: str) -> bool:
    """Blocking typed confirmation. Returns True if user confirms."""
    try:
        resp = input(f"{prompt} Type YES to confirm: ").strip()
        return resp.upper() == "YES"
    except KeyboardInterrupt:
        return False


def dispatch(user_input: str) -> Tuple[bool, str]:
    """
    Resolve an intent to a whitelisted script and execute it safely.
    Returns (success, message).
    Behavior:
      - Uses module docstring embeddings via match_command(...)
      - If confidence < CONFIDENCE_THRESHOLD, requires explicit confirmation
      - Performs a dry-run description first, then asks for typed confirmation
      - Executes script using run_script(...) which validates whitelist and runs via subprocess
    """
    try:
        script_name, score, doc = match_command(user_input)
        logger.info("Matched user_input=%r -> script=%s score=%.4f", user_input, script_name, score)
    except Exception as e:
        logger.exception("Matcher error for input=%r: %s", user_input, e)
        return False, f"Matcher error: {e}"

    # Inform user what was matched
    print(f"Matched: {script_name} (score={score:.3f})")
    if doc:
        print(f"Description: {doc}")

    # If low confidence, require explicit confirmation
    if score < CONFIDENCE_THRESHOLD:
        print("Low confidence for this match.")
        ok = _prompt_confirm("This action has low confidence. Confirm running the matched script?")
        if not ok:
            logger.info("User aborted low-confidence match for %s", script_name)
            return False, "Aborted by user (low confidence)."

    # Dry-run first (describe exact command)
    ok, msg = run_script(script_name, args=[], dry_run=True)
    logger.info("Dry-run for %s -> %s (ok=%s)", script_name, msg, ok)
    print(msg)

    # Require explicit confirmation before real run
    ok = _prompt_confirm("Proceed with executing the script?")
    if not ok:
        logger.info("User aborted execution for %s", script_name)
        return False, "Execution aborted by user."

    # Execute for real
    success, out = run_script(script_name, args=[], dry_run=False)
    if success:
        logger.info("Script executed: %s", script_name)
        print("Script executed successfully.\n")
        print(out)
        return True, out
    else:
        logger.error("Script execution failed: %s -> %s", script_name, out)
        print(f"Script failed: {out}")
        return False, out