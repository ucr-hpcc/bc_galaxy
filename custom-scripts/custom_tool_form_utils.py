import os
import subprocess
import logging
from typing import(
    List,
    Tuple,
)

log = logging.getLogger(__name__)
def determine_runner() -> List[Tuple[str, str, bool]]:
    try:
        if os.environ.get("RUNNER") == "slurm":
            log.info('Slurm avaible, selecting slurm as primary job runner for configured tool...')
            return [("Yes", "slurm", True)]
        return [("No", "local", True)]
    except Exception as error:
        log.info(error)
        return [("Error", "error", True)]

def partitions_available() -> List[Tuple[str, str, bool]]:
    try:
        get_partition = subprocess.run(["sinfo", "-O", "partitionname"], capture_output=True, text=True)
        get_partition = str(get_partition.stdout).split('\n')
        get_partition.pop(0)
        get_partition.pop(len(get_partition)-1)
        partitions = []
        for i in range(len(get_partition)):
            name = get_partition[i].strip()
            if name == "hpcc_default":
                partitions.append((name, name, True))
            else:
                partitions.append((name, name, False))
        return partitions
    except Exception as error:
        log.info(error)
        return [("Error", "error", True)]

