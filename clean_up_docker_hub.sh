#!/bin/bash
# Based on kizbitz/dockerhub-v2-api-organization.sh at https://gist.github.com/kizbitz/175be06d0fbbb39bc9bfa6c0cb0d4721

# Example for the Docker Hub V2 API
# Returns all images and tags associated with a Docker Hub organization account.
# Requires 'jq': https://stedolan.github.io/jq/

# set username, password, and organization
UNAME=$1
UPASS=$2
ORG=$3

# -------

set -e

# get token
echo Username is ${UNAME}
echo Organization is ${ORG}
echo "Retrieving token ..."
TOKEN=$(curl -s -H "Content-Type: application/json" -X POST -d '{"username": "'${UNAME}'", "password": "'${UPASS}'"}' https://hub.docker.com/v2/users/login/ | jq -r .token)

# get list of repositories
echo "Retrieving repository list ..."
REPO_LIST=$(curl -s -H "Authorization: JWT ${TOKEN}" https://hub.docker.com/v2/repositories/${ORG}/?page_size=200 | jq -r '.results|.[]|.name')

# delete images and/or tags
echo "Deleting images and tags for organization: ${ORG}"
for i in ${REPO_LIST}
do
  # Delete repo (all)
  echo -n "${i}: "
#  curl -X DELETE -s -H "Authorization: JWT ${TOKEN}" https://hub.docker.com/v2/repositories/${ORG}/${i}/
  echo "DELETED"

  # Delete by tags (TODO: filter)
  #IMAGE_TAGS=$(curl -s -H "Authorization: JWT ${TOKEN}" https://hub.docker.com/v2/repositories/${ORG}/${i}/tags/?page_size=300 | jq -r '.results|.[]|.name')
  #for j in ${IMAGE_TAGS}
  #do
  #   echo -n "  - ${j} ... "
  #   curl -X DELETE -s -H "Authorization: JWT ${TOKEN}" https://hub.docker.com/v2/repositories/${ORG}/${i}/tags/${j}/
  #   echo "DELETED"
  #done
done