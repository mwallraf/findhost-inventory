# FINDHOST-COLLECTOR

This is the main Findhost collector script that executes all individual collector scripts, ex. the frontix collector.

Multiple collector scripts can be added, see the individual collector scripts for more information what input is required and where output is stored.

## RUN THE SCRIPT

This script should be run by the findhost-populate.sh script however it can be run seperately as well.

If the environment variable FINDHOST_COLLECTOR is not set then the local .env file will be loaded, if it exists.

```
bash findhost-collector.sh
```

## ENVIRONMENT VARIABLES

```

# ENABLE OR DISABLE THE FRONTIX COLLECTOR
RUN_COLLECTOR_FRONTIX=1

# LOCATION OF THE FRONTIX COLLECTOR
COLLECTOR_FRONTIX_FOLDER="frontix"

# the location of the frontix queries
QUERY_SQL_DIR="$COLLECTOR_FRONTIX_FOLDER/frontix_dump_queries"
QUERY_SQL_DIR="$COLLECTOR_FRONTIX_FOLDER/frontix_dump_queries_test"

# the location of the query results
QUERY_OUTPUT_DIR="$COLLECTOR_FRONTIX_FOLDER/frontix_dump_output"

# the location of the log file
LOGDIR="../log"

# VARIABLES USED FOR CONNECTIONS TO THE MES FRONTIX DATABASE
FTX_HOSTNAME="<HOSTNAME>"
FTX_PORT="<PORT>"
FTX_SERVICE="<SERVICE>"
FTX_USER="<USERNAME>"
FTX_PWD="<PASSWORD>"

# VARIABLES USED FOR CONNECTIONS TO OBE FRONTIX DATABASE
FTX_OBE_HOSTNAME="<HOSTNAME>"
FTX_OBE_PORT="<PORT>"
FTX_OBE_SID="<SERVICE>"
FTX_OBE_USER="<USERNAME>"
FTX_OBE_PWD="<PASSWORD>"
```
