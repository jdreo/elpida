#!/usr/bin/env python3
import json
import elpida

def f(x):
    v = 0
    for xi in x:
        v += xi * xi
    return v

if __name__ == "__main__":
    import sys

    # Those two named pipes FIFO must exist:
    fquery = "query"
    freply = "reply"

    while True:

        # You may just read from the named pipe FIFO...
        print("[problem]: Waiting for a query", file=sys.stderr, end="... ", flush=True)
        with open(fquery,'r') as fd:
            query = fd.read()
        print("OK", file=sys.stderr)

        jq = json.loads(query)
        if __debug__:
            print(json.dumps(jq, indent=4))

        qtype = jq["query_type"]
        if qtype == "call":
            x = jq["solution"]
            v = [f(x)]

            # ... or use a low-level function to write a reply...
            r = json.dumps( {"reply_type":"value", "value":v} )
            elpida.write(r, freply, "problem", "value")

        elif qtype == "new_run":
            # ... or use a high-level function.
            elpida.problem.ack(freply)
            
        else:
            r = json.dumps( {"reply_type":"error", "code":134, "message":"Unsupported message type"} )
            elpida.write(r, freply, "problem", "error")
            sys.exit(134)

