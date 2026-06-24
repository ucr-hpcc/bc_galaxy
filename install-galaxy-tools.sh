VERSION="25.0.3"

module purge -f
module load workspace

cd $VERSION

# Export necessary environment variables
export GALAXY_CONFIG_FILE="$PWD/bootstrap/config/galaxy.yml"
export GALAXY_ROOT_DIR="$PWD"

# Get api key from config file
BOOTSTRAP_KEY="$(grep 'bootstrap_admin_api_key:' ${GALAXY_CONFIG_FILE} | cut -d " " -f4)"

source $PWD/.venv/bin/activate

cd bootstrap

# Wait for Galaxy server to start
echo "Waiting for galaxy response"
if ! galaxy-wait -g http://localhost:8080 -v --timeout 180; then
	echo "Unable to access Galaxy server..."
	exit 1
fi

TOOLS_TO_INSTALL=( $(ls $PWD/usegalaxy-tools/usegalaxy.org/*.yml.lock) )
for tool in "${TOOLS_TO_INSTALL[@]}"; do
	echo "Installing: ${tool}"
	shed-tools install --tools-file ${tool} --latest --verbose --galaxy 'http://localhost:8080' --api-key ${BOOTSTRAP_KEY}
done

# Install tool dependencies. This installs any missing tool dependencies via conda
install-tool-deps --tool $PWD/config/bootstrap_tools_conf.xml --verbose --galaxy 'http://localhost:8080' --api-key ${BOOTSTRAP_KEY}

echo "Bootstrap tools initialized! Please shut down the Galaxy server..."
echo "Once the server is shutdown, remove the following directories/files:

       bootstrap/cache
       bootstrap/container_cache
       bootstrap/control.sqlite
       bootstrap/gravity
       bootstrap/object_store_cache
       bootstrap/tmp
       bootstrap/config/galaxy.yml
       bootstrap/tool_search_index
       bootstrap/universe.sqlite
       bootstrap/results.sqlite
       bootstrap/config/galaxy.yml

After the listed directories/files are removed, update the permissions of the bootstrap/config directory to make it readable for all users:

	chmod -R a+r bootstrap/config

Once all these changes are made, Galaxy is ready for public use!!!"
