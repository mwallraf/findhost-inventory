#!/bin/bash

# Run all the seperate findhost collector scripts
# Use the .env file to define the necessary environment variables


echo "start findhost collector"

if [ -z "$FINDHOST_COLLECTOR" ]
then
    echo "findhost-collector.sh: use local .env file"
    . .env
fi

if [ "${RUN_COLLECTOR_FRONTIX}" == 1 ]; then

  # export frontix variables
  export COLLECTOR_FRONTIX_FOLDER
  export QUERY_SQL_DIR
  export QUERY_OUTPUT_DIR
  export LOGDIR

  # VARIABLES USED FOR CONNECTIONS TO MES FRONTIX
  export FTX_HOSTNAME
  export FTX_PORT
  export FTX_SERVICE
  export FTX_USER
  export FTX_PWD

  # VARIABLES USED FOR CONNECTIONS TO OBE FRONTIX
  export FTX_OBE_HOSTNAME
  export FTX_OBE_PORT
  export FTX_OBE_SID
  export FTX_OBE_USER
  export FTX_OBE_PWD

  . $COLLECTOR_FRONTIX_FOLDER/findhost-collector-frontix.sh

fi


echo "end findhost collector"
