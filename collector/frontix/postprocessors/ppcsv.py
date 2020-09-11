# Default post-processor
# this just returns a json representation of:
#   { "column": "value", .. }

import json

def post_processor(cols, row, header=False, delim=";", altdelim=","):
    rows = []
    if header:
       rows.append(delim.join(cols)) 
    row = [ "" if not c else str(c).replace(delim, altdelim) for c in row ]
    rows.append(delim.join(row))
    return "\n".join(rows)

