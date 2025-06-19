import os
import pandas as pd

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

def get_uc_cost(job_title: str) -> str:
    df, _ = load_union_job_data()
    df["__normalized_title__"] = df[TITLE_COLUMN].astype(
        str).str.strip().str.lower()
    title_norm = job_title.strip().lower()
    match = df[df["__normalized_title__"] == title_norm]
    if not match.empty:
        return str(match.iloc[0][COST_COLUMN])
    return "N/A"
