#!/usr/bin/env python3

import os
from flask import Flask, request, jsonify
from pymongo import MongoClient, TEXT
from rapidfuzz import process, fuzz
from pydantic import BaseModel, Field, ValidationError

app = Flask(__name__)

# mongo connection
mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
client = MongoClient(mongo_uri)
db = client.nobel
laureates = db.laureates

laureates.create_index(
    [("name", TEXT), ("category", TEXT), ("motivation", TEXT)],
    name="text_search"
)

all_names = [d["name"] for d in laureates.find({}, {"name": 1, "_id": 0})]

class LaureateModel(BaseModel):
    name: str = Field(..., min_length=1)
    year: int = Field(..., ge=1901)
    category: str = Field(..., min_length=1)
    motivation: str = Field(..., min_length=1)


# Endpoints 
@app.route("/search/name")
def search_name():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([]), 400

    matches = process.extract(q, all_names, scorer=fuzz.WRatio, limit=5)
    results = []
    for name, score, _ in matches:
        doc = laureates.find_one({"name": name}, {"_id": 0})
        doc["score"] = score
        results.append(doc)
    return jsonify(results)


@app.route("/search/category")
def search_category():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([]), 400

    cursor = laureates.find(
        {"category": {"$regex": q, "$options": "i"}},
        {"_id": 0}
    ).limit(20)
    return jsonify(list(cursor))


@app.route("/search/motivation")
def search_motivation():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([]), 400

    cursor = laureates.find(
        {"$text": {"$search": q}},
        {"score": {"$meta": "textScore"}, "_id": 0}
    ).sort([("score", {"$meta": "textScore"})]).limit(20)
    return jsonify(list(cursor))


@app.route("/laureate", methods=["POST"])
def upsert_laureate():
    try:
        payload = LaureateModel(**request.get_json()).dict()
    except ValidationError as e:
        return jsonify({"errors": e.errors()}), 422

    res = laureates.replace_one(
        {
            "name": payload["name"],
            "year": payload["year"],
            "category": payload["category"]
        },
        payload,
        upsert=True
    )
    return jsonify({
        "upserted_id": str(res.upserted_id) if res.upserted_id else None
    }), 200


# Run app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
