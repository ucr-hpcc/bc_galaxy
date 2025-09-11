import logging
import json

log = logging.getLogger(__name__)

FAILURE_MESSAGE = 'This tool could not be run because of a misconfiguration in the Galaxy job running system, please report this error to support@hpcc.ucr.edu'


def dynamic_cores_time(app,
                       tool,
                       user):
    try:
        # Set default runner and parse the selected runner
        default_runner = app.job_config.get_destination('local')
        selected_runner = app.job_config.dynamic_params['runner']

        # Check if user is running custom module wrapper tool. The tool should have a parameter called "selected_runner"
        if selected_runner == 'slurm':
            slurm_runner = app.job_config.get_destination('slurm')
            if 'slurm' not in user.preferences:
                slurm_runner.params['nativeSpecification'] = f"--cpus-per-task=2 --mem=2048 --job_name={user.username}/{tool.id}"
                return slurm_runner

            runner = json.loads(user.preferences["slurm"])
            cores = runner['cores']
            mem = runner['memory']
            runtime = runner['runtime']
            partition_selected = runner['partition']
            args = runner['args']

            # Check if walltime was defined
            if runtime != '':
                slurm_runner.params['nativeSpecification'] = f"--cpus-per-task={cores} --mem={mem} --partition={partition_selected} --time={runtime} --job_name={user.username}/{tool.id} {args}"
            else:
                slurm_runner.params['nativeSpecification'] = f"--cpus-per-task={cores} --mem={mem} --partition={partition_selected} --job_name={user.username}/{tool.id} {args}"

            return slurm_runner

        log.info('Returning local runner...')
        return default_runner
    except Exception as error:
        log.info(FAILURE_MESSAGE)
        log.error(error)
        return None

