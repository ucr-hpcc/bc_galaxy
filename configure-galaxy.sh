VERSION="25.0.3"

module purge -f
module load workspace

cd $VERSION

# Check if bootstrap directory exists
if [[ ! -d "$PWD/bootstrap" ]]; then
	echo "Creating bootstrap directory..."
	mkdir -p "bootstrap/shed_tools_data" \
		 "bootstrap/shed_tools_data_manager" \
		 "bootstrap/config" \
		 "bootstrap/dependencies/_conda"
	echo "Cloning usegalaxy-tools repo"
	git clone https://github.com/galaxyproject/usegalaxy-tools.git
	echo "Installing requirements.txt..."
	$PWD/.venv/bin/python -m pip install -r usegalaxy-tools/requirements.txt
	mv usegalaxy-tools bootstrap/
	rm -rf usegalaxy-tools/.git
	touch $PWD/bootstrap/install_tool_sheds.sqlite
else
	echo "Delete or move old bootstrap directory and rerun the script!"
	exit 1
fi

# Export necessary environment variables
export GALAXY_CONFIG_FILE="$PWD/bootstrap/config/galaxy.yml"
export GALAXY_ROOT_DIR="$PWD"

# Generate bootstrap api key
RANDOM_KEY="$(openssl rand -base64 8)"

# Generate Galaxy configuration file
(
umask 077
cat > "${GALAXY_CONFIG_FILE}" << EOL
gravity:
  galaxy_user : ${USER}
  gunicorn:
    enable: true
    bind: localhost:8080

galaxy:
  data_dir: $PWD/bootstrap
  config_dir: $PWD/config
  tool_dependency_dir: $PWD/bootstrap/dependencies
  managed_config_dir: $PWD/bootstrap/config
  bootstrap_admin_api_key: ${RANDOM_KEY}
  install_database_connection: sqlite:///$PWD/bootstrap/install_tool_sheds.sqlite
  conda_auto_init: true
  conda_prefix: $PWD/bootstrap/dependencies/_conda
  tool_data_path: $PWD/bootstrap/shed_tools_data
  shed_tool_data_path: $PWD/bootstrap/shed_tools_data
  galaxy_data_manager_data_path: $PWD/bootstrap/shed_tools_data_manager
  shed_tool_config_file: $PWD/bootstrap/config/bootstrap_tools_conf.xml
EOL
)

echo "Initializating empty sqlite database for bootstrap instance. This may take a bit..."
source $PWD/.venv/bin/activate
cd $PWD/bootstrap/
python $GALAXY_ROOT_DIR/scripts/db.py -c ${GALAXY_CONFIG_FILE} init


echo "Launching Galaxy..."
sh $GALAXY_ROOT_DIR/run.sh --no-create-venv --skip-client-build --skip-wheels
