#!/bin/sh
while IFS=, read -r ext name; do
  curl -s -X POST "$BASE/services/data/v67.0/sobjects/Account/" -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" -d "{\"Name\":\"$name\"}"
done < accounts.csv
