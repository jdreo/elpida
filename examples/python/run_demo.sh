#!/bin/sh

# Create named pipe FIFOs
mkfifo query reply

# Start the problem server.
# NOTE: in case of an error, the server may keep running,
#       and you will have to `kill` it.
python3 -O ./problem_server.py &

# Start the solver client.
# NOTE: if you want to see the message payload,
#       just remove the `-O` argument.
python3 -O ./solver_client.py

