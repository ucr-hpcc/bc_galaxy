import subprocess
import logging
from typing import(
    List,
    Tuple,
)

log = logging.getLogger(__name__)
FAILURE_MESSAGE = 'This tool could not be run because of a misconfiguration in the Galaxy job running system, please report this error to support@hpcc.ucr.edu'

def modules_avail() -> List[Tuple[str, str, bool]]:
    try:
        # Lanuch a process with the following command and capture it's output as text
        get_modules = subprocess.run(["module avail -t --no-pager -o alias"], shell=True, capture_output=True, text=True)

        # Split output by newlines
        get_modules = str(get_modules.stderr).split('\n')

        # The last value is just an empty line so pop it
        get_modules.pop()
        modules = []

        for i in range(1, len(get_modules)):
            name = get_modules[i]
            modules.append((name, name, False))
        return modules
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

        # First value will have unnecessary information
        get_partition.pop(0)

        # The last value is just an empty line so pop it
        get_partition.pop()
        partitions = []

        # Store partitions in a triple format ('label', 'value', selected or not: True or False)
        for i in range(len(get_partition)):
            name = get_partition[i].strip()
            # Set short as the default partition
            if name == "short":
                partitions.append((name, name, True))
            else:
                partitions.append((name, name, False))
        return partitions
    except Exception as error:
        log.error(error)
        log.error(FAILURE_MESSAGE)
        return [("Error", "error", True)]

