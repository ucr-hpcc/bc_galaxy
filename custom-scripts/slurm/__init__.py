import logging
import subprocess
import json
from typing import(
    List,
)
log = logging.getLogger(__name__)

# Function which displays all partitions available to the user
def partitions_available() -> List[str]:
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
            # Set epyc as the default partition
            if name == "epyc":
                partitions.append(name)
            else:
                partitions.append(name)
        return partitions
    except Exception as error:
        log.error(error)
        return ["Error"]

def main(trans, webhook, params):
    # Return list of available partitions
    if 'getPartitions' in params:
        partition_list = partitions_available()
        return {"partitions": partition_list}

    # Copy user
    update_user = trans.user
    # Add slurm parameters to new user preference 'slurm'
    update_user.preferences["slurm"] = json.dumps(params)
    # Add new change and commit to current session
    trans.sa_session.add(update_user)
    trans.sa_session.commit()

    return {"message": "Slurm parameters updated."}
