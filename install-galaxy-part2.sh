VERSION="25.0.3"

module purge -f
module load workspace

cd $VERSION


# Check if bootstrap directory exists
if [[ ! -d "$PWD/bootstrap" ]]; then
	echo "Creating bootstrap directory..."
	mkdir -p "bootstrap/shed_tools_data" "bootstrap/config" "bootstrap/dependencies/_conda"
	echo "Cloning usegalaxy-tools repo"
	git clone https://github.com/galaxyproject/usegalaxy-tools.git
	echo "Installing requirements.txt..."
	$PWD/.venv/bin/python -m pip install -r usegalaxy-tools/requirements.txt
	mv usegalaxy-tools bootstrap/
	touch $PWD/bootstrap/install_tool_sheds.sqlite
fi

# Export necessary environment variables
export GALAXY_CONFIG_FILE="$PWD/bootstrap/config/galaxy.yml"
export GALAXY_ROOT_DIR="$PWD/"

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
  log_destination: $PWD/bootstrap/galaxy-bootstrap.log
  shed_tool_data_path: $PWD/bootstrap/shed_tools_data
  shed_tool_config_file: $PWD/bootstrap/config/bootstrap_tools_conf.xml
EOL
)

echo "Initializating empty sqlite database for bootstrap instance. This may take a bit..."
source $PWD/.venv/bin/activate
cd $PWD/bootstrap/
python $GALAXY_ROOT_DIR/scripts/db.py -c ${GALAXY_CONFIG_FILE} init


echo "Launching Galaxy in daemon mode..."
# Run galaxy in background
sh $GALAXY_ROOT_DIR/run.sh --daemon --no-create-venv --skip-client-build --skip-wheels

# Wait until galaxy is accessible
galaxy-wait -g http://localhost:8080 -v --timeout 180

echo "Installing tools from usegalaxy-tools repo. This may take awhile..."

TOOLS_TO_INSTALL=( $(ls $PWD/usegalaxy-tools/usegalaxy.org/*.yml.lock) )
for tool in "${TOOLS_TO_INSTALL[@]}"; do
	echo "Installing: ${tool}"
	shed-tools install --tools-file ${tool} --install-tool-dependencies --verbose --galaxy 'http://localhost:8080' --api-key ${RANDOM_KEY}
done

# Install tool dependencies. This installs any missing tools via conda
install-tool-deps --tool $PWD/config/shed_tool_conf.xml --verbose --galaxy 'http://localhost:8080' --api-key ${RANDOM_KEY}

sh $GALAXY_ROOT_DIR/run.sh --stop-daemon --no-create-venv --skip-client-build --skip-wheels

cd ..

echo "Removing unnecessary files from bootstrap initialization..."

rm -rf bootstrap/cache \
       bootstrap/container_cache \
       bootstrap/control.sqlite \
       bootstrap/gravity \
       bootstrap/object_store_cache \
       bootstrap/tmp \
       bootstrap/config/galaxy.yml \
       bootstrap/tool_search_index \
       bootstrap/universe.sqlite \
       bootstrap/results.sqlite \
       bootstrap/config/galaxy.yml

echo "Finished! Check galaxy-bootstrap.log in bootstrap/ for any errors..."
