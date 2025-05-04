#!/usr/bin/env bash
set -euo pipefail

echo "Building & starting containers…"
docker-compose up --build -d

echo "Waiting 10s for services to become healthy…"
sleep 10

echo "Testing: name search (Einstein)…"
curl -s "http://localhost:5000/search/name?q=Einstein" 

echo "Testing: category search (physics)…"
curl -s "http://localhost:5000/search/category?q=physics" 

echo "Testing: motivation search (photoelectric)…"
curl -s "http://localhost:5000/search/motivation?q=photoelectric" 

echo "'upsert' Jane Doe…"
curl -s \
  -X POST "http://localhost:5000/laureate" \
  -H "Content-Type: application/json" \
  -d @payload.json 

echo "Verify 'test' by name search…"
curl -s "http://localhost:5000/search/name?q=Jane%20Doe" 



