#!/bin/bash
# Based on kizbitz/dockerhub-v2-api-organization.sh at https://gist.github.com/kizbitz/175be06d0fbbb39bc9bfa6c0cb0d4721

# Example for the Docker Hub V2 API
# Returns all images and tags associated with a Docker Hub organization account.
# Requires 'jq': https://stedolan.github.io/jq/

# set username, password, and organization
UNAME=$1
UPASS=$2
ORG=$3
REPO=$4
MAX_IMAGE=$5
# -------

set -e

# get token
echo "Retrieving token ..."
TOKEN=$(curl -s -H "Content-Type: application/json" -X POST -d '{"username": "'${UNAME}'", "password": "'${UPASS}'"}' https://hub.docker.com/v2/users/login/ | jq -r .token)

# get list of repositories
IMAGE_TAGS=$(curl -s -H "Authorization: JWT ${TOKEN}" https://hub.docker.com/v2/repositories/${ORG}/${REPO}/tags/?ordering=last_updated | jq -r '.results[].name')
TOTAL_COUNT=$(curl -s -H "Authorization: JWT ${TOKEN}" https://hub.docker.com/v2/repositories/${ORG}/${REPO}/tags/?ordering=last_updated | jq -r '.count')
count=0
count_all=0
echo ${IMAGE_TAGS}
for j in ${IMAGE_TAGS}
do
  count_all=$((count_all + 1))
  if [[ ${j} == *"dev_"* ]]; then
    count=$((count + 1))
    # Keep the first max_image.
    if [ ${MAX_IMAGE} -lt ${count} ]; then
      # Do not delete the last item. For some reason, the latest item is put to last!
      if [ ${count_all} -lt ${TOTAL_COUNT} ]; then
        echo -n "  - ${j} ... "
#        curl -X DELETE -s -H "Authorization: JWT ${TOKEN}" https://hub.docker.com/v2/repositories/${ORG}/${REPO}/tags/${j}/
        echo "DELETED"
      fi
    fi
  fi
done
