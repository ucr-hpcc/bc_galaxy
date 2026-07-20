import logging, json, os

log = logging.getLogger(__name__)

FAILURE_MESSAGE = 'This tool could not be run because of a misconfiguration in the Galaxy job running system, please report this error to support@hpcc.ucr.edu'


def dynamic_cores_time(app,
                       tool,
                       user,
                       job,
                       workflow_invocation_uuid):
    try:
        # Set default runner and parse the selected runner
        default_runner = app.job_config.get_destination('local')
        selected_runner = app.job_config.dynamic_params['runner']

        # If the selected runner chosen via OnDemand is slurm
        if selected_runner == 'slurm':
            slurm_runner = app.job_config.get_destination('slurm')
            data_root = os.environ.get('DATAROOT')

            # Check if job is part of Workflow by checking uuid
            if workflow_invocation_uuid != None:

                # Find custom Workflow slurm parameters set
                wf_id = job.workflow_invocation_step.workflow_invocation.workflow.stored_workflow_id
                wf_id_encoding = app.security.encode_id(wf_id)
                wf_cache_path = os.path.join(data_root, f'cache/{wf_id_encoding}.json')

                # If Workflow cache file exists
                if os.path.exists(wf_cache_path):
                    step_index = job.workflow_invocation_step.workflow_step.order_index + 1
                    with open(wf_cache_path, 'r') as f: step_slurm_settings = json.load(f)

                    # Check if Workflow step exists in file
                    if f'{step_index}' in step_slurm_settings:
                        cores = step_slurm_settings[f'{step_index}']['cores']
                        mem = step_slurm_settings[f'{step_index}']['memory']
                        runtime = step_slurm_settings[f'{step_index}']['runtime']
                        partition_selected = step_slurm_settings[f'{step_index}']['partition']
                        args = step_slurm_settings[f'{step_index}']['args']

                        if runtime != '':
                            slurm_runner.params['nativeSpecification'] = f"--cpus-per-task={cores} --mem={mem} --partition={partition_selected} --time={runtime} --job_name={user.username}/{tool.id} {args}"
                        else:
                            slurm_runner.params['nativeSpecification'] = f"--cpus-per-task={cores} --mem={mem} --partition={partition_selected} --job_name={user.username}/{tool.id} {args}"
                        log.info('Returning slurm runner for workflow step...')
                        return slurm_runner
                    else:
                        pass

            # Check if slurm job settings set via Webhook plugin
            cache_path = os.path.join(data_root, 'cache/slurm_settings.json')

            # Return default parameters if slurm job settings not set
            if not os.path.exists(cache_path):
                slurm_runner.params['nativeSpecification'] = f"--cpus-per-task=2 --mem=2048 --job_name={user.username}/{tool.id}"
                return slurm_runner

            with open(cache_path, 'r') as f: slurm_settings = json.load(f)
            cores = slurm_settings['cores']
            mem = slurm_settings['memory']
            runtime = slurm_settings['runtime']
            partition_selected = slurm_settings['partition']
            args = slurm_settings['args']

            # Check if walltime was defined
            if runtime != '':
                slurm_runner.params['nativeSpecification'] = f"--cpus-per-task={cores} --mem={mem} --partition={partition_selected} --time={runtime} --job_name={user.username}/{tool.id} {args}"
            else:
                slurm_runner.params['nativeSpecification'] = f"--cpus-per-task={cores} --mem={mem} --partition={partition_selected} --job_name={user.username}/{tool.id} {args}"
            log.info('Returning slurm runner...')
            return slurm_runner

        log.info('Returning local runner...')
        return default_runner
    except Exception as error:
        log.info(FAILURE_MESSAGE)
        log.error(error)
        return None
