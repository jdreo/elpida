#!/usr/bin/env python3
"""
Minimal implementation of wrapper for an Elpida problem server,
following the Command Line Interface of SMAC3 for "Target Algorithm Evaluator".

This is what SMAC3 is calling, and this is just a thin wrapper
to call an Elpida problem server and format back the results
so that SMAC3 can read them.

You can use this solver cilent along with the example problem server in elpida/examples/python/problem_server.py
e.g. on Linux:
    ../python/problem_server.py &
    ./smac3-elpida-cli.py 0 1 2 3 4 -x 2 -y 3
"""

import json

# Common base class for all exceptions here.
class AbortError(RuntimeError):
    def __init__(self, message, json_payload = {}):
        self.message = message
        self.payload = json_payload
        super(AbortError, self).__init__(self.message)
    pass

# Errors we may raise.
errors = {
    ("NoFile", 2),
    ("InvalidArgument", 22),
    ("NotFIFO", 60),
    ("Unreadable", 77),
    ("MissingArg", 132),
    ("PayloadError", 133),
    ("PayloadTypeError", 134),
    ("PayloadIncomplete", 135),
    ("DimensionMismatch", 134),
    ("SolutionMismatch", 134),
    ("NotSupported", 134),
    ("ServerError",254),
}

# Actual holder of exception classes.
exceptions = {}

# Declare exceptions classes we may use.
for name,code in errors:
    exceptions[name] = type(name, (AbortError,), {"code":code})


def check_fifo( name ):
    """Check if the given filename is a FIFO named pipe and create it if necessary."""
    
    is_fifo = True
    exists = True
    
    try:
        is_fifo = stat.S_ISFIFO(os.stat(name).st_mode)
        
    except FileNotFoundError:
        exists = False

    except BaseException as e:
        print("Unexpected ", type(e)," error:", e, file=sys.stderr)
        print("Result for SMAC: ABORT")
        raise

    if not exists:
        try:
            os.mkfifo(name)
            is_fifo = True

        except BaseException as e:
            print("Unexpected ", type(e)," error:", e, file=sys.stderr)
            print("Result for SMAC: ABORT")
            raise

    if not is_fifo:
        print("Result for SMAC: ABORT")
        raise exceptions["NotFIFO"](f"`{name}` file is not a FIFO named pipe")
    

def call_elpida_problem_server(x, y, query="query", reply="reply"):
    """
    Call a problem server, using the Elpida protocol.

    Input:
        config (Configuration): Configuration object derived from ConfigurationSpace.

    Return:
        cost (float): Performance measure.
    """
 
    # Forge a JSON `call` query:
    squery = json.dumps( {"query_type":"call", "solution":[x,y]} )

    # Send it to the server:
    with open(query,'w') as fd:
        fd.write(squery)

    # Wait for the answer and read it when it's available:
    with open(reply,'r') as fd:
        sreply = fd.read()
        
    # Decode the JSON:
    jreply = json.loads(sreply)

    if "reply_type" not in jreply:
        raise exceptions["PayloadTypeError"]("Missing `reply_type` field", jreply)
        
    elif jreply["reply_type"] == "error":
        if "message" not in jreply:
            raise exceptions["PayloadIncomplete"]("Problem Server returned an error, but without a message", jreply)
        raise exceptions["ServerError"](f"Problem server error: {jreply['message']}", jreply)
        
    elif jreply["reply_type"] == "value":
        qualities = jreply["value"]

    else:
        raise exceptions["PayloadTypeError"]("Problem server returned a message of unknown type: `{jreply['reply_type']}`", jreply)

    return qualities[0]


if __name__ == "__main__":
    import os
    import stat
    import sys
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("instance", metavar="INS", type=int, help="UNSUPPORTED")
    parser.add_argument("instance-specific", metavar="SPE", type=int, help="UNSUPPORTED")
    parser.add_argument("cutoff-time", metavar="CUT", type=float, help="UNSUPPORTED")
    parser.add_argument("runlength", metavar="RUN", type=float, help="UNSUPPORTED")
    parser.add_argument("seed", metavar="SEED", type=int, help="UNSUPPORTED")

    parser.add_argument("-x", metavar="X", type=float, help="A variable")
    parser.add_argument("-y", metavar="Y", type=float, help="Another variable")

    parser.add_argument("--query", metavar="FIFO", default="query", type=str,
        help="Name of the FIFO named pipe to use to pass queries to the problem server")
    parser.add_argument("--reply", metavar="FIFO", default="reply", type=str,
        help="Name of the FIFO named pipe to use to read replies from the problem server")
    
    the = parser.parse_args()

    # Double check FIFO named pipes (and create them if necessary).
    check_fifo(the.query)
    check_fifo(the.reply)

    try:
        quality = call_elpida_problem_server(the.x, the.y, the.query, the.reply)
        
    except AbortError as e:
        print("Call to problem server raised the following error:", file=sys.stderr)
        print(e.message, file=sys.stderr)
        if __debug__:
            print(e.payload, file=sys.stderr)
        print("Result for SMAC: ABORT")
        sys.exit(e.code)
        
    except BaseException as e:
        print("Unexpected ", type(e)," error:", e, file=sys.stderr)
        print("Result for SMAC: ABORT")
        raise

    # We do not support some of those variables at the moment, but SMAC expect them.
    run_time = -1
    run_length = -1
    seed = -1
    print(f"Result for SMAC: SUCCESS, {run_time}, {run_length}, {quality}, {seed}")

