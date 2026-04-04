# Prompt Templates

This directory stores editable prompt templates used by tracks.

Contract for v1:

- one file per track, named `track_<key>.txt`
- template variables use Python `str.format(...)` placeholders
- Track A requires `{question}`
- Track B requires `{question}` and `{schema}`

Initial template files:

- `track_a.txt`
- `track_b.txt`
