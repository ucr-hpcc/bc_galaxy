#!/bin/bash

API_KEY=$1
if ! galaxy-wait --g "http://0.0.0.0:${port}/node/${HOSTNAME}/${port}" -a "${API_KEY}" --ensure-admin --timeout 60 -v; then
	echo "Invalid API key!"
	exit 1
fi


git clone https://github.com/ucr-hpcc/bc_galaxy.git
if [[ ! -d ${DATAROOT}/workflows ]]; then
	echo "Workflow directory not found. Installing workflows..."
	mv bc_galaxy/workflows ${DATAROOT}
	WORKFLOWS_TO_INSTALL=( $(ls ${DATAROOT}/workflows/*.ga) )
	for wf in "${WORKFLOWS_TO_INSTALL[@]}"; do
		echo "Installing: ${wf}"
		workflow-to-tools -w "${wf}" -o temp.yml
		shed-tools install --tools-file temp.yml --install-tool-dependencies --verbose --galaxy "http://0.0.0.0:${port}/node/${HOSTNAME}/${port}"  --api-key ${API_KEY}
		workflow-install --verbose --galaxy "http://0.0.0.0:${port}/node/${HOSTNAME}/${port}" --api-key ${API_KEY} -w "${wf}" --publish-workflows
		rm temp.yml
	done
	exit 0
fi

mv bc_galaxy/workflows temp_workflows

WORKFLOWS_TO_INSTALL=( $(comm -23 <(basename -a temp_workflows/*) <(basename -a $DATAROOT/workflows/*)) )
echo "Updating missing workflows..."
for wf in "${WORKFLOWS_TO_INSTALL[@]}"; do
	echo "Installing: ${wf}"
	workflow-to-tools -w "temp_workflows/${wf}" -o temp.yml
	shed-tools install --tools-file temp.yml --install-tool-dependencies --verbose --galaxy "http://0.0.0.0:${port}/node/${HOSTNAME}/${port}" --api-key ${API_KEY}
	workflow-install --verbose --galaxy "http://0.0.0.0:${port}/node/${HOSTNAME}/${port}" --api-key ${API_KEY} -w "temp_workflows/${wf}" --publish-workflows
	cp temp_workflows/${wf} ${DATAROOT}/workflows
	rm temp.yml
done
echo "All workflows update to date!"
exit 0
