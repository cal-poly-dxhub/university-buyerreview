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
