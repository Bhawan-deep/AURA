import os
import pickle
import subprocess
import sys
from typing import List, Tuple, Optional

# Embedding model name (pin here)
EMBED_MODEL = "all-MiniLM-L6-v2"
SCRIPTS_DIR = "scripts"
INDEX_FILE = "script_index.txt"
EMBED_FILE = "embeddings/script_embeddings.pkl"


def _read_module_docstring(path: str) -> str:
    """Return the module-level docstring or the first comment block if docstring absent."""
    with open(path, "r", encoding="utf-8") as fh:
        src = fh.read()
    # naive detection of triple-quoted module docstring
    src_strip = src.lstrip()
    if src_strip.startswith(('"""', "'''")):
        quote = src_strip[:3]
        end = src_strip.find(quote, 3)
        if end != -1:
            return src_strip[3:end].strip()
    # fallback: collect top consecutive comment lines
    lines = src.splitlines()
    comments = []
    for ln in lines:
        s = ln.strip()
        if s.startswith("#"):
            comments.append(s.lstrip("#").strip())
        elif s == "":
            # allow a single blank line in header comments
            if comments:
                break
            continue
        else:
            break
    return " ".join(comments) or os.path.basename(path)


def index_scripts(script_folder: str = SCRIPTS_DIR, index_file: str = INDEX_FILE) -> None:
    """Write a whitelist of scripts (filenames) present in script_folder."""
    os.makedirs(os.path.dirname(index_file) or ".", exist_ok=True)
    entries = []
    for file in sorted(os.listdir(script_folder)):
        if file.endswith(".py"):
            entries.append(file)
    with open(index_file, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(e + "\n")


def generate_embeddings(index_file: str = INDEX_FILE, embed_file: str = EMBED_FILE) -> None:
    """Generate embeddings from each script's module docstring and persist (scripts, docs, embeddings)."""
    os.makedirs(os.path.dirname(embed_file) or ".", exist_ok=True)
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBED_MODEL)

    with open(index_file, "r", encoding="utf-8") as f:
        scripts = [ln.strip() for ln in f if ln.strip()]

    docs = []
    paths = []
    for script in scripts:
        path = os.path.join(SCRIPTS_DIR, script)
        if not os.path.isfile(path):
            docs.append("")  # preserve alignment
            paths.append(path)
            continue
        docs.append(_read_module_docstring(path))
        paths.append(path)

    embeddings = model.encode(docs, show_progress_bar=True)
    with open(embed_file, "wb") as fh:
        pickle.dump({"scripts": scripts, "paths": paths, "docs": docs, "embeddings": embeddings}, fh)


def match_command(user_input: str, embed_file: str = "embeddings/script_embeddings.pkl") -> Tuple[str, float, str]:
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    from sentence_transformers import SentenceTransformer

    with open(embed_file, "rb") as fh:
        data = pickle.load(fh)

    scripts: List[str] = data["scripts"]
    docs: List[str] = data["docs"]
    embeddings = data["embeddings"]

    model = SentenceTransformer("all-MiniLM-L6-v2")
    input_emb = model.encode([user_input])
    scores = cosine_similarity(input_emb, embeddings)[0]
    best_idx = int(scores.argmax())
    best_score = float(scores[best_idx])
    return scripts[best_idx], best_score, docs[best_idx]


def run_script(script_name: str, args: Optional[List[str]] = None, index_file: str = INDEX_FILE,
               dry_run: bool = False, timeout: Optional[int] = None) -> Tuple[bool, str]:
    """
    Securely run a whitelisted script via subprocess.
    Returns (success, output_or_error).
    """
    args = args or []
    # validate script against index whitelist
    with open(index_file, "r", encoding="utf-8") as f:
        allowed = {ln.strip() for ln in f if ln.strip()}
    if script_name not in allowed:
        return False, f"Script not allowed: {script_name}"

    script_path = os.path.join(SCRIPTS_DIR, script_name)
    if not os.path.isfile(script_path):
        return False, f"Script not found: {script_path}"

    if dry_run:
        return True, f"[dry-run] Would run: {sys.executable} {script_path} {' '.join(args)}"

    cmd = [sys.executable, script_path] + args
    try:
        completed = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=timeout)
        out = completed.stdout.strip() or "<no output>"
        return True, out
    except subprocess.CalledProcessError as e:
        err = e.stderr.strip() or str(e)
        return False, f"Script failed: {err}"
    except Exception as e:
        return False, f"Execution error: {e}"
    
def run_callable(script_name: str, args: dict, index_file: str = INDEX_FILE) -> Tuple[bool, str]:
    """Attempt to run a whitelisted script via direct Python import and function call."""
    import importlib.util
    import inspect

    # Validate whitelist
    with open(index_file, "r", encoding="utf-8") as f:
        allowed = {ln.strip() for ln in f if ln.strip()}
    if script_name not in allowed:
        return False, f"Script not allowed: {script_name}"

    script_path = os.path.join(SCRIPTS_DIR, script_name)
    if not os.path.isfile(script_path):
        return False, f"Script not found: {script_path}"

    try:
        # Load module dynamically
        spec = importlib.util.spec_from_file_location("target_module", script_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Find callable entry point
        entry = getattr(mod, "main", None) or getattr(mod, "run", None)
        if not callable(entry):
            return False, f"No callable entry point found in {script_name}"

        # Validate signature
        sig = inspect.signature(entry)
        bound = sig.bind_partial(**args)
        bound.apply_defaults()

        # Execute
        result = entry(**bound.arguments)
        return True, str(result) if result is not None else "<no output>"
    except Exception as e:
        return False, f"Callable execution error: {e}"