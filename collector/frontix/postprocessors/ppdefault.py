# Default post-processor
# this just returns a json representation of:
#   { "column": "value", .. }

import json

def post_processor(cols, row):
    j = {}
    for idx, col in enumerate(cols):
        j[str(col)] = str(row[idx])
    return json.dumps(j)
