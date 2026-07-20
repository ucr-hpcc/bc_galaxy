import sys
import os
import json
import logging

log = logging.getLogger(__name__)
FAILURE_MESSAGE = 'This tool could not be run because of a misconfiguration in the Galaxy job running system, please report this error to support@hpcc.ucr.edu'

# This script should only ever by run Galaxy

try:
    # Set cache directory
    data_root = os.environ.get('DATAROOT')
    path = f"cache/{sys.argv[1]}.json"
    cache_path = os.path.join(data_root, path)

    # Extract parameters given
    params = {
                'cores' : sys.argv[2],
                'memory' : sys.argv[3],
                'runtime' : sys.argv[4],
                'partition' : sys.argv[5],
                'args' : sys.argv[6]
                }

    # Map step to parameters
    step = {sys.argv[7] : params}

    # If Workflow file doesn't exist then make it and dump contents
    if not os.path.exists(cache_path):
        with open(cache_path, "w") as f: json.dump(step, f)
    else:
        # Otherwise then open the cache file and update it
        with open(cache_path, "r") as f: merge = json.load(f)
        merge.update(step)
        with open(cache_path, "w") as f: merge = json.dump(merge, f)
except Exception as error:
        log.error(error)
        log.error(FAILURE_MESSAGE)

