import sys
import json

def write(j, fpipe, who, name):
    print("[{}]: Send a {}".format(who, name), file=sys.stderr, end="... ", flush=True)
    with open(fpipe,'w') as fd:
        fd.write(j)
    print("OK", file=sys.stderr)
    if __debug__:
        print(j, file=sys.stderr)

def read(fpipe, who, name):
    print("[{}]: Read the {}".format(who, name), file=sys.stderr, end="... ", flush=True)
    with open(fpipe,'r') as fd:
        ans = fd.read()
    print("OK",file=sys.stderr)
    r = json.loads(ans)
    if __debug__:
        print(json.dumps(r, indent=4))
    return r


class solver:

    @staticmethod
    def send(jq, fquery):
        write(jq, fquery, "solver", "query")

    @staticmethod
    def receive(freply):
        return read(freply, "solver", "reply")

    @staticmethod
    def query(jq, fquery, freply):
        solver.send(jq, fquery)
        return solver.receive(freply)

    @staticmethod
    def call(sol, fquery, freply):
        jq = json.dumps( {"query_type":"call", "solution":sol}, indent=4 )
        reply = solver.query(jq, fquery, freply)
        if not solver.is_error(reply):
            return reply["value"]
        else:
            print("[solver]: ERROR:",reply["message"])
            return None

    @staticmethod
    def is_error(jr):
        if "reply_type" not in jr:
            return True
        elif jr["reply_type"] == "error":
            return True
        else:
            return False


class problem:

    @staticmethod
    def ack(freply):
        r = json.dumps( {"reply_type":"ack"} )
        write(r, freply, "problem", "ack")

