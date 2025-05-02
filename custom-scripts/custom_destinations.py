import logging

log = logging.getLogger(__name__)

FAILURE_MESSAGE = 'This tool could not be run because of a misconfiguration in the Galaxy job running system, please report this error to support@hpcc.ucr.edu'


def dynamic_cores_time(app,
                       tool,
                       job,
                       user):
    try:
        # Set default runner and parse the selected runner
        default_runner = app.job_config.get_destination('local')
        selected_runner = app.job_config.dynamic_params['runner']


        # This holds the necessary values to pass in!!!
        # Check if user is running custom module wrapper tool. The tool should have a parameter called "selected_runner"
        if tool.get_param("selected_runner") != None:
            params = job.get_param_values(app)

            # Get selected_runner from params dictonary
            runner = params['selected_runner']

            # Check if job runner is slurm
            if runner['runner'] == "slurm":

                # Extract selected values
                cores = runner['core']
                mem = runner['memory']
                runtime = runner['runtime']
                partition_selected = runner['partition']

                log.info('Returning slurm runner with defined configurations set...')

                # Create the actual job runner object for slurm
                slurm_runner = app.job_config.get_destination('slurm')

                # Check if walltime was defined
                if runtime != None:
                    slurm_runner.params['nativeSpecification'] = f"--cpus-per-task={cores} --mem={mem} --partition={partition_selected} --time={runtime} --job_name={user.username}/{tool.id}"
                else:
                    slurm_runner.params['nativeSpecification'] = f"--cpus-per-task={cores} --mem={mem} --partition={partition_selected} --job_name={user.username}/{tool.id}"

                return slurm_runner

        # If user is not running custom module wrapper tool, check if the selected runner is slurm
        elif selected_runner == 'slurm':
            log.info('Returning slurm runner with default configurations set...')
            slurm_runner = app.job_config.get_destination('slurm')

            # Return slurm with default parameters
            slurm_runner.params['nativeSpecification'] = f"--cpus-per-task=8 --mem=16000 --job_name={user.username}/{tool.id}"
            return slurm_runner

        log.info('Returning local runner...')
        return default_runner
    except Exception as error:
        log.info(FAILURE_MESSAGE)
        log.error(error)
        return None

