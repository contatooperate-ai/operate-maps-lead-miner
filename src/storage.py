"""Backup local dos leads qualificados em JSON (lista) e CSV, com deduplicação por maps_url."""
import csv
import json
from pathlib import Path


def save_json(lead: dict, path: Path) -> None:
    data = []
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = []

    if any(item.get("maps_url") == lead.get("maps_url") for item in data):
        return

    data.append(lead)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def save_csv(lead: dict, path: Path) -> None:
    existing_urls = set()
    file_exists = path.exists()
    if file_exists:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                existing_urls.add(row.get("maps_url"))

    if lead.get("maps_url") in existing_urls:
        return

    write_header = not file_exists
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(lead.keys()))
        if write_header:
            writer.writeheader()
        writer.writerow(lead)
