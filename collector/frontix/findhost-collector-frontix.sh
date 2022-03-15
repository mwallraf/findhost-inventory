#!/bin/bash

# Execute a python environment which has the module cx_Oracle
# then run the python script frontix-modinput-connector.py
# to connect to Oracle Frontix and return the result
# to a CSV file
#
# Expected parameters:
#   source folder = list of files containing SQL
#   dump folder = folder where the result will be saved, same filename as the source
#   filter query, only files that match this filter will be processed
#
# Prerequisites::
#    - cx_oracle python library
#    - oracle instantclient 11.2
#   

# somehow required for the cx_oracle module otherwise it uses the global
# python folders instead of venv
#unset LD_LIBRARY_PATH
#unset PYTHONPATH

#QUERY_SQL_DIR="/opt/splunk/etc/apps/TA-frontix/bin/isc_dump_queries"
#QUERY_OUTPUT_DIR="/opt/splunk/etc/apps/TA-frontix/bin/isc_dump_output"

echo "start frontix collector script"

if [ -z "$RUN_COLLECTOR_FRONTIX" ]
then
    echo "findhost-collector-frontix.sh: use local .env file"
    . .env
fi

# export variables to be used within the python script
export PYTHONVERBOSE
export QUERY_LIMIT
export QUERY_SQL_DIR
export QUERY_OUTPUT_DIR
export LOGDIR

# VARIABLES USED FOR CONNECTIONS TO MES FRONTIX
export FTX_HOSTNAME
export FTX_PORT
export FTX_SERVICE
export FTX_USER
export FTX_PWD
export FTX_POSTPROCESSOR

# VARIABLES USED FOR CONNECTIONS TO OBE FRONTIX
export FTX_OBE_HOSTNAME
export FTX_OBE_PORT
export FTX_OBE_SID
export FTX_OBE_USER
export FTX_OBE_PWD

python $COLLECTOR_FRONTIX_FOLDER/frontix-collector.py $QUERY_SQL_DIR $QUERY_OUTPUT_DIR $@ > $LOGDIR/findhost-collector-frontix.log 2>&1

echo "end frontix collector script"

