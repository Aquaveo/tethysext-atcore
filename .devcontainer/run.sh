#!/bin/bash

echo_status() {
  local args="${@}"
  tput setaf 4
  tput bold
  echo -e "- $args"
  tput sgr0
}

db_max_count=24;
db_engine=${TETHYS_DB_ENGINE} # Get the DB engine from environment variable
USAGE="USAGE: . run.sh [options]
OPTIONS:
--db-max-count <INT>      \t number of attempt to connect to the database. Default is at 24.
"

while [[ $# -gt 0 ]]; do
  case $1 in
    --db-max-count)
      shift # shift from key to value
      db_max_count=$1;
    ;;
    *)
      echo -e "${USAGE}"
      return 0
  esac
  shift
done

echo_status "Starting up..."

# Check if the database is ready
echo_status "Checking if DB is ready"
db_check_count=0
until ${CONDA_HOME}/envs/${CONDA_ENV_NAME}/bin/pg_isready -h ${TETHYS_DB_HOST} -p ${TETHYS_DB_PORT} -U postgres; do
  if [[ $db_check_count -gt $db_max_count ]]; then
    >&2 echo "DB was not available in time - exiting"
    exit 1
  fi
  >&2 echo "DB is unavailable - sleeping"
  db_check_count=`expr $db_check_count + 1`
  sleep 5
done

# Run Salt
if ! grep -q "^postgres.host:" /etc/salt/minion; then
  echo "postgres.host: '${TETHYS_DB_HOST}'" >> /etc/salt/minion
  echo "postgres.port: '${TETHYS_DB_PORT}'" >> /etc/salt/minion
  echo "postgres.user: '${TETHYS_DB_USERNAME}'" >> /etc/salt/minion
  echo "postgres.pass: '${TETHYS_DB_PASSWORD}'" >> /etc/salt/minion
  echo "postgres.bins_dir: '${CONDA_HOME}/envs/${CONDA_ENV_NAME}/bin'" >> /etc/salt/minion
fi
echo_status "Enforcing start state... (This might take a bit)"
salt-call --local state.apply

# Keep the container running indefinitely with minimal CPU usage
echo_status "Initialization complete. Keeping the container running..."
while true; do sleep 3600; done