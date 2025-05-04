#!/usr/bin/env python3

import os
import requests
from pymongo import MongoClient, TEXT

def fetch_nobel_prizes():
    url = "https://api.nobelprize.org/v1/prize.json"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json().get("prizes", [])


def normalize_laureates(prize):
    year = int(prize["year"])
    category = prize["category"]
    docs = []

    for laureate in prize.get("laureates", []):
        first = laureate.get("firstname", "").strip()
        last = laureate.get("surname", "").strip()
        name = f"{first} {last}".strip()
        motivation = laureate.get("motivation", "").strip().strip('"')

        docs.append({
            "name": name,
            "year": year,
            "category": category,
            "motivation": motivation
        })

    return docs


def main():
    # debug: check MongoURI
    mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
    print(f"[DEBUG] Connecting to MongoDB at {mongo_uri} …")

    client = MongoClient(mongo_uri)
    db = client.nobel
    laureates = db.laureates

    laureates.create_index(
        [("name", TEXT), ("category", TEXT), ("motivation", TEXT)],
        name="text_search"
    )

    # debug: fetch and report prize entry count
    prizes = fetch_nobel_prizes()
    print(f"[DEBUG] Fetched {len(prizes)} prize entries from API.")

    upserted = 0
    for prize in prizes:
        for doc in normalize_laureates(prize):
            result = laureates.replace_one(
                {
                    "name": doc["name"],
                    "year": doc["year"],
                    "category": doc["category"]
                },
                doc,
                upsert=True
            )
            if result.upserted_id or result.modified_count:
                upserted += 1

    # debug: no. documents created / updated
    print(f"[DEBUG] Upserted or updated {upserted} laureate documents.")


if __name__ == "__main__":
    main()
