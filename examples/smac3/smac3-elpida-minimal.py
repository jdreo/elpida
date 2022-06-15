#!/usr/bin/env python3
"""
Minimal implementation of SMAC3 calling an Elpida problem server,
following the minimal example from SMAC3’s documentation.

You can use this solver cilent along with the example problem server in elpida/examples/python/problem_server.py
providing that you created the `query` and `reply` named FIFO pipes.
e.g. on Linux:
    mkfifo query reply
    ../python/problem_server.py &
    ./smac3-elpida-minimal.py
"""

import json

from ConfigSpace import ConfigurationSpace
from ConfigSpace.hyperparameters import UniformIntegerHyperparameter
from smac.facade.smac_bb_facade import SMAC4BB
from smac.scenario.scenario import Scenario

def call_elpida_problem_server(config):
    """
    Call a problem server, using the Elpida protocol.

    Input:
        config (Configuration): Configuration object derived from ConfigurationSpace.

    Return:
        cost (float): Performance measure.
    """

    x = config["x"]
    
    # Forge a JSON `call` query:
    squery = json.dumps( {"query_type":"call", "solution":[x]} )

    # Send it to the server:
    with open("query",'w') as fd:
        fd.write(squery)

    # Wait for the answer and read it when it's available:
    with open("reply",'r') as fd:
        sreply = fd.read()
        
    # Decode the JSON:
    jreply = json.loads(sreply)

    # Extract the objective function value:
    quality = jreply["value"]

    return quality


if __name__ == "__main__":
    # Define your hyperparameters
    configspace = ConfigurationSpace()
    configspace.add_hyperparameter(UniformIntegerHyperparameter("x", 2, 100))

    # Provide meta data for the optimization
    scenario = Scenario({
        "run_obj": "quality",  # Optimize quality (alternatively runtime)
        "runcount-limit": 10,  # Max number of function evaluations (the more the better)
        "cs": configspace,
    })

    smac = SMAC4BB(scenario=scenario, tae_runner=call_elpida_problem_server)
    best_found_config = smac.optimize()
