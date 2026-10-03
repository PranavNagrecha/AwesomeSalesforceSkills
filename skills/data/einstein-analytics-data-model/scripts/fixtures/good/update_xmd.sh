#!/bin/sh
# Reads the current version, then writes the complete user XMD.
curl -s "$INSTANCE/services/data/v67.0/wave/datasets/$DATASET_ID" -H "Authorization: Bearer $TOKEN"
curl -s -X PUT "$INSTANCE/services/data/v67.0/wave/datasets/$DATASET_ID/versions/$VERSION_ID/xmds/user" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" --data @user_xmd.json
