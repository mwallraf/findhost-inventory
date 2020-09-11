# FINDHOST-COLLECTOR-FRONTIX

This is the Findhost collector that executes Frontix DB queries. Queries are stored in seperate files in teh frontix_dump_queries folder by default, a single file per query.

Output is stored in the frontix_dump_queries folder by default, a single output file per query.

## RUN THE SCRIPT

This script should be run by the findhost-populate.sh script or by the findhost-collector.sh scripts however it can be run seperately as well.

If the environment variable RUN_COLLECTOR_FRONTIX is not set then the local .env file will be loaded, if it exists.

```
bash findhost-consolidator-frontix.sh
```

## ENVIRONMENT VARIABLES

```
# enable if you want verbose python debugging info
#PYTHONVERBOSE=1

# limit the result of each query to max 10 rows, for testing purposes usually
QUERY_LIMIT=10

# the location of the findhost-collector-frontix script
COLLECTOR_FRONTIX_FOLDER="."

# the location of the frontix queries
QUERY_SQL_DIR="frontix_dump_queries"
#QUERY_SQL_DIR="frontix_dump_queries_test"

# the location of the query results
QUERY_OUTPUT_DIR="frontix_dump_output"

# the location of the log file
LOGDIR="log"

# The default postprocessor to use, check the 
# postprocessors folder for other options
#FTX_POSTPROCESSOR=ppcsv

# VARIABLES USED FOR CONNECTIONS TO THE DATABASE
FTX_HOSTNAME="<HOSTNAME>"
FTX_PORT="<PORT>"
FTX_SERVICE="<SERVICE>"
FTX_USER="<USERNAME>"
FTX_PWD="<PASSWORD>"
```

