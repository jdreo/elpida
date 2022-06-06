#!/usr/bin/env python3
import json
import elpida

if __name__ == "__main__":
    import random
    import sys

    dimension = 10

    # Those two named pipes FIFO must exist:
    fquery = "query"
    freply = "reply"

    for i in range(5):

        if i == 3:
            # You may forge a message directly from JSON...
            jq = json.dumps( {"query_type":"new_run"} )
            elpida.solver.query(jq, fquery, freply)
 
        sol = [random.randint(0,1) for j in range(dimension)]

        # ... or you may use a high-level interface.
        val = elpida.solver.call(sol, fquery, freply)
        print("f({}) = {}".format(sol,val))

    # Nicely ask the server to stop.
    print("[solver]: Send an EXIT query", file=sys.stderr, end="... ", flush=True)
    jq = json.dumps( {"query_type":"stop"}, indent=4)
    elpida.solver.query(jq, fquery, freply)

