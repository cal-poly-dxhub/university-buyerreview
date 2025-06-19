import os
import json
import pandas as pd

from utils import query_bedrock_with_multiple_pdfs, try_parse_json_like
from prompt_loader import TASK_PROMPT_REGISTRY
from model_registry import ModelRegistry
from state import PipelineState

# === CONFIGURATION ===
TITLE_COLUMN = "Deciphered Job Code Description"
COST_COLUMN = "Total UC Cost"
CSV_PATH = os.path.join("Data", "union_job_titles.csv")


def load_union_job_data(filepath=CSV_PATH, title_col=TITLE_COLUMN):
    df = pd.read_csv(filepath)
    df.columns = df.columns.str.strip()  # Clean column names
    if title_col not in df.columns:
        raise ValueError(f"Missing required column: '{title_col}' in CSV.")
    titles = df[title_col].dropna().astype(str).tolist()
    return df, titles


def union_job_check(state: PipelineState) -> PipelineState:
    parsed = state.get("parsed_data", {})
    if not parsed:
        return {
            "union_job_check": {
                "error": "❌ No parsed data available"
            }
        }

    try:
        df, job_titles = load_union_job_data(
            filepath=CSV_PATH, title_col=TITLE_COLUMN)
        if TITLE_COLUMN not in df.columns:
            return {
                "union_job_check": {
                    "error": f"❌ Missing required column: '{TITLE_COLUMN}' in CSV.",
                }
            }
        if COST_COLUMN not in df.columns:
            return {
                "union_job_check": {
                    "error": f"❌ Missing required column: '{COST_COLUMN}' in CSV.",
                }
            }

        df[COST_COLUMN] = pd.to_numeric(df[COST_COLUMN], errors="coerce")
        df["__normalized_title__"] = df[TITLE_COLUMN].astype(
            str).str.strip().str.lower()

        union_list_str = ", ".join(sorted(set(job_titles)))
        prompt_template = TASK_PROMPT_REGISTRY["UNION_JOB_CLASSIFICATION"]
        doc_text = json.dumps(parsed, indent=2)
        prompt = (
            prompt_template.replace("{doc_text}", doc_text)
            .replace("{union_job_list}", union_list_str)
        )

        response = query_bedrock_with_multiple_pdfs(
            prompt=prompt,
            files=[],
            model_id=ModelRegistry.haiku_3_5,
        )

        raw_output = try_parse_json_like(response)
        if raw_output is None:
            return {
                "union_job_check": {
                    "error": "❌ Could not parse valid JSON from LLM response.",
                    "llm_response": response,
                    "matched_row": None
                }
            }

        matched_title_raw = raw_output.get("matched_union_title")
        matched_title = matched_title_raw.strip().lower() if matched_title_raw else ""

        match_df = df[df["__normalized_title__"] == matched_title]
        matched_row = None

        if matched_title and not match_df.empty:
            records = match_df.to_dict(orient="records")
            matched_row = records[0] if records else None
        elif matched_title:
            matched_row = {
                "note": f"No match found in union job list for title '{matched_title}'"
            }

        return {
            "union_job_check": {
                **raw_output,
                "matched_row": matched_row
            }
        }

    except Exception as e:
        return {
            "union_job_check": {
                "error": str(e)
            }
        }
