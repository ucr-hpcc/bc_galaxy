import logging
from galaxy.jobs.mapper import JobMappingException
from galaxy.jobs import JobDestination

log = logging.getLogger(__name__)

FAILURE_MESSAGE = 'This tool could not be run because of a misconfiguration in the Galaxy job running system, please report this error'


def dynamic_cores_time(app, tool, job, user_email, resource_params):
    # handle job resource parameters
    if not resource_params.get("cores") and not resource_params.get("time"):
        default_destination_id = app.job_config.get_destination(None)
        log.warning('(%s) has no input parameter cores or time. Run with default runner: %s' % (job.id, default_destination_id.runner))
        return default_destination_id
    
    try:
        cores = resource_params.get("cores")
        time = resource_params.get("time")
        resource_list = 'walltime=%s:00:00,nodes=1:ppn=%s' % (time, cores)
    except:
        default_destination_id = app.job_config.get_destination(None)
        log.warning('(%s) failed to run with customized configuration. Run with default runner: %s' % (job.id, default_destination_id.runner))
        return default_destination_id

    log.info('returning pbs runner with configuration %s', resource_list)
    return JobDestination(runner="pbs", params={"Resource_List": resource_list})
