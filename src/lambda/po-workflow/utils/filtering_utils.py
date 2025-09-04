import csv


def get_unique_purchasing_categories(csv_path: str) -> list[str]:
    unique = set()
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            unique.add(row["Purchasing Category"])
    return sorted(unique)
