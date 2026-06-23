#!/bin/bash
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

# Create an account on local Galaxy server to upload workflows
RANDOM_PASS="$(openssl rand -base64 8)"
USER_ID=$(curl -s -X POST "http://localhost:8080/api/users" \
  -H "X-API-Key: ${BOOTSTRAP_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"workflow\", \"email\": \"workflow@ondemand.ucr\", \"password\": \"$RANDOM_PASS\"}" | cut -d , -f 4 | cut -d : -f 2 | sed 's/"//g')


USER_API_KEY=$(curl -s -X GET "http://localhost:8080/api/users/${USER_ID}/api_key" \
	-H "X-API-Key: ${BOOTSTRAP_KEY}" | sed 's/"//g')

# Install workflows
WORKFLOWS_TO_INSTALL=( $(ls workflows/*.ga) )
for wf in "${WORKFLOWS_TO_INSTALL[@]}"; do
	echo "Installing: ${wf}"
	workflow-install --verbose --galaxy 'http://localhost:8080' --api-key ${USER_API_KEY} -w "${wf}" --publish-workflows
	workflow-to-tools -w "${wf}" -o "$(echo ${wf} | sed 's/.ga/.yml/g')"
	shed-tools install --tools-file "$(echo ${wf} | sed 's/.ga/.yml/g')"  --verbose --galaxy 'http://localhost:8080' --api-key ${BOOTSTRAP_KEY}
done

# Install any missing workflow tool dependencies
install-tool-deps --tool $PWD/bootstrap/config/bootstrap_tools_conf.xml --verbose --galaxy 'http://localhost:8080' --api-key ${BOOTSTRAP_KEY}

# Extract rows from universe.sqlite containing workflow information
sqlite3 universe.sqlite <<EOF
.headers off
.output workflow_sqlite_data.out

.mode insert stored_workflow
SELECT * FROM stored_workflow;

.mode insert workflow
SELECT * FROM workflow;

.mode insert workflow_step
SELECT * FROM workflow_step;

.mode insert workflow_step_input
SELECT * FROM workflow_step_input;

.mode insert workflow_step_connection
SELECT * FROM workflow_step_connection;
EOF

echo "Bootstrap workflows tools initialized!"
echo "If you're done configuring Galaxy then shut down the Galaxy server manually using CTRL-C..."
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
