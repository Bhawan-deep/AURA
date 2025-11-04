import os
from typing import Optional, Tuple, Dict

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.runnables import RunnableMap, RunnablePassthrough

# Load local HuggingFace model via LangChain
# Replace with your actual model name or endpoint
MODEL_ID = os.getenv("AURA_LOCAL_MODEL", "mistralai/Mistral-7B-Instruct-v0.1")
HF_API_KEY = os.getenv("HUGGINGFACEHUB_API_TOKEN")  # Required if using HuggingFace Hub

llm = HuggingFaceEndpoint(
    repo_id=MODEL_ID,
    temperature=0.3,
    max_new_tokens=512,
    huggingfacehub_api_token=HF_API_KEY,
)

# Output parser
parser = JsonOutputParser()

# Prompt template
prompt = PromptTemplate.from_template(
    """You are an intent parser for a local automation assistant. Your job is to extract:
1. The script name to run
2. The arguments to pass to that script

Respond ONLY in JSON format using this structure:
{{
  "script": "<script_name>.py",
  "args": {{
    "arg1": "value1",
    "arg2": "value2"
  }}
}}

User command: {input}
{format_instructions}
"""
).partial(format_instructions=parser.get_format_instructions())

# Chain
chain = prompt | llm | parser

def parse_command(user_input: str) -> Optional[Tuple[str, Dict]]:
    """
    Parse user command into (script_name, args) using LangChain + HuggingFace.
    Returns None if parsing fails.
    """
    try:
        result = chain.invoke({"input": user_input})
        script = result.get("script")
        args = result.get("args", {})
        if not script or not script.endswith(".py"):
            return None
        return script, args
    except Exception as e:
        import traceback
        print(f"[intent_parser] Failed to parse command: {e}")
        traceback.print_exc()
        return None