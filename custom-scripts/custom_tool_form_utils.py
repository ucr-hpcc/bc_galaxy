import os
import subprocess
import logging
from typing import(
    List,
    Tuple,
)

log = logging.getLogger(__name__)
FAILURE_MESSAGE = 'This tool could not be run because of a misconfiguration in the Galaxy job running system, please report this error to support@hpcc.ucr.edu'

# Function which custom module tool wrappers call to determine which runner to use for job
def determine_runner() -> List[Tuple[str, str, bool]]:
    try:
        # Check value of enviornment variable set during OnDemand start up phase
        if os.environ.get("RUNNER") == "slurm":
            log.info('Slurm avaible, selecting slurm as primary job runner for configured tool...')
            return [("Yes", "slurm", True)]
        # Return selected runner in the following format
        return [("No", "local", True)]
    except Exception as error:
        log.error(error)
        log.error(FAILURE_MESSAGE)
        return [("Error", "error", True)]

# Function which displays all partitions available to the user
def partitions_available() -> List[Tuple[str, str, bool]]:
    try:
        # Lanuch a process with the following command and capture it's output as text
        get_partition = subprocess.run(["sinfo", "-O", "partitionname"], capture_output=True, text=True)

        # Split output by newlines
        get_partition = str(get_partition.stdout).split('\n')

        # First value with have unnecessary information
        get_partition.pop(0)

        # The last value is just an empty line so pop it
        get_partition.pop()
        partitions = []

        # Store partitions in a triple format ('label', 'value', selected or not: True or False)
        for i in range(len(get_partition)):
            name = get_partition[i].strip()
            # Set hpcc_default as the default partition
            if name == "hpcc_default":
                partitions.append((name, name, True))
            else:
                partitions.append((name, name, False))
        return partitions
    except Exception as error:
        log.error(error)
        log.error(FAILURE_MESSAGE)
        return [("Error", "error", True)]

