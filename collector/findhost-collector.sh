#!/bin/bash

# Run all the seperate findhost collector scripts
# Use the .env file to define the necessary environment variables


echo "start findhost collector"

if [ -z "$FINDHOST_COLLECTOR" ]
then
    echo "findhost-collector.sh: use local .env file"
    . .env
fi

if [ ${RUN_COLLECTOR_FRONTIX} == 1 ]; then

  # export frontix variables
  export COLLECTOR_FRONTIX_FOLDER
  export QUERY_SQL_DIR
  export QUERY_OUTPUT_DIR
  export LOGDIR
  export FTX_HOSTNAME
  export FTX_PORT
  export FTX_SERVICE
  export FTX_USER
  export FTX_PWD

  . $COLLECTOR_FRONTIX_FOLDER/findhost-collector-frontix.sh

fi


echo "end findhost collector"
