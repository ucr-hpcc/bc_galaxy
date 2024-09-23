cd "$(dirname "$0")"

VERSION="release_24.1"

# Install Galaxy
if [[ ! -e galaxy ]]; then
    git clone git@github.com:galaxyproject/galaxy.git
fi

ln -s custom-scripts galaxy/custom-scripts

cd galaxy
git checkout ${VERSION}


# Add custom scripts to configure Galaxy for ondemand use
ln -s $PWD/custom-scripts/custom_destinations.py $PWD/lib/galaxy/jobs/rules/destinations.py

#Remove galaxy remote user and replace with custom remote user
rm -r $PWD/lib/galaxy/web/framework/middleware/remoteuser.py
ln -s $PWD/custom-scripts/custom_remote_user.py $PWD/lib/galaxy/web/framework/middlewware/remoteuser.py


# Install dependencies
# Retrieved from line 1-54 in https://github.com/galaxyproject/galaxy/blob/release_19.09/run.sh
. ./scripts/common_startup_functions.sh

# If there is a file that defines a shell environment specific to this
# instance of Galaxy, source the file.
if [ -z "$GALAXY_LOCAL_ENV_FILE" ];
then
    GALAXY_LOCAL_ENV_FILE='./config/local_env.sh'
fi

if [ -f "$GALAXY_LOCAL_ENV_FILE" ];
then
    . "$GALAXY_LOCAL_ENV_FILE"
fi

GALAXY_PID=${GALAXY_PID:-galaxy.pid}
GALAXY_LOG=${GALAXY_LOG:-galaxy.log}
PID_FILE=$GALAXY_PID
LOG_FILE=$GALAXY_LOG

parse_common_args $@

run_common_start_up

setup_python

if [ ! -z "$GALAXY_RUN_WITH_TEST_TOOLS" ];
then
    export GALAXY_CONFIG_OVERRIDE_TOOL_CONFIG_FILE="test/functional/tools/sample_tool_conf.xml"
    export GALAXY_CONFIG_ENABLE_BETA_WORKFLOW_MODULES="true"
    export GALAXY_CONFIG_OVERRIDE_ENABLE_BETA_TOOL_FORMATS="true"
    export GALAXY_CONFIG_INTERACTIVETOOLS_ENABLE="true"
    export GALAXY_CONFIG_OVERRIDE_WEBHOOKS_DIR="test/functional/webhooks"
    export GALAXY_CONFIG_OVERRIDE_PANEL_VIEWS_DIR="test/integration/panel_views_1/"
fi


if [ -n "$GALAXY_UNIVERSE_CONFIG_DIR" ]; then
    python ./scripts/build_universe_config.py "$GALAXY_UNIVERSE_CONFIG_DIR"
fi

set_galaxy_config_file_var

if [ "$INITIALIZE_TOOL_DEPENDENCIES" -eq 1 ]; then
    # Install Conda environment if needed.
    python ./scripts/manage_tool_dependencies.py init_if_needed
fi


