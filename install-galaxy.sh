cd "$(dirname "$0")"

# Set current version
VERSION="25.0.0"

# Check if custom scripts directory exists
if [[ ! -d "custom-scripts/$VERSION" ]]; then
	mkdir -p "custom-scripts/$VERSION"
fi


# Install Galaxy
if [[ ! -e v$VERSION ]]; then
    echo "Cloning Galaxy version v${VERSION}..."
    git clone -b v${VERSION} https://github.com/galaxyproject/galaxy.git


    echo "Downloading custom galaxy scripts from UCR HPCC repo..."
# Get custom scripts from UCR HPCC github
    wget -O "custom-scripts/$VERSION/custom_remote_user.py" "https://raw.githubusercontent.com/ucr-hpcc/bc_galaxy/refs/heads/dev/custom-scripts/custom_remote_user.py"
    wget -O "custom-scripts/$VERSION/custom_destinations.py" "https://raw.githubusercontent.com/ucr-hpcc/bc_galaxy/refs/heads/dev/custom-scripts/custom_destinations.py"
    wget -O "custom-scripts/$VERSION/custom_tool_form_utils.py" "https://raw.githubusercontent.com/ucr-hpcc/bc_galaxy/refs/heads/dev/custom-scripts/custom_tool_form_utils.py"
fi


# Rename galaxy directory to version number
mv galaxy $VERSION

cd $VERSION

# Create virtualenv
module purge


# Load in miniconda and create virtual environment
module load miniconda3

python -m venv .venv

echo "Building Galaxy..."
# Install dependencies without creating virtual env, as this was created in the step before
# Retrieved from line 1-54 in https://github.com/galaxyproject/galaxy/blob/release_19.09/run.sh
. ./scripts/common_startup_functions.sh --no-create-venv

# If there is a file that defines a shell environment specific to this instance of Galaxy, source the file.
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
    echo "Running galaxy with test tools..."
    export GALAXY_CONFIG_OVERRIDE_TOOL_CONFIG_FILE="test/functional/tools/sample_tool_conf.xml"
    export GALAXY_CONFIG_ENABLE_BETA_WORKFLOW_MODULES="true"
    export GALAXY_CONFIG_OVERRIDE_ENABLE_BETA_TOOL_FORMATS="true"
    export GALAXY_CONFIG_INTERACTIVETOOLS_ENABLE="true"
    export GALAXY_CONFIG_OVERRIDE_WEBHOOKS_DIR="test/functional/webhooks"
    export GALAXY_CONFIG_OVERRIDE_PANEL_VIEWS_DIR="test/integration/panel_views_1/"
fi


if [ -n "$GALAXY_UNIVERSE_CONFIG_DIR" ]; then
    echo "Building galaxy universe config..."
    python ./scripts/build_universe_config.py "$GALAXY_UNIVERSE_CONFIG_DIR"
fi

set_galaxy_config_file_var

# Install slurm drmaa python package into galaxy virtual environment
$PWD/.venv/bin/python -m pip install drmaa

# Remove .git directory
rm -rf .git

cd ..

# Add custom scripts to configure Galaxy for ondemand use
echo "Configuring custom scripts..."
ln -s $PWD/custom-scripts/$VERSION/custom_destinations.py $PWD/$VERSION/lib/galaxy/jobs/rules/destinations.py
mkdir -p $PWD/$VERSION/custom-scripts
ln -s $PWD/custom-scripts/$VERSION/custom_tool_form_utils.py $PWD/$VERSION/custom-scripts/custom_tool_form_utils.py

# Remove galaxy remote user and replace with custom remote user
rm $VERSION/lib/galaxy/web/framework/middleware/remoteuser.py
ln -s $PWD/custom-scripts/$VERSION/custom_remote_user.py $PWD/$VERSION/lib/galaxy/web/framework/middleware/remoteuser.py

echo "Setup finished..."
