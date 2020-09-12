# FINDHOST

The findhost script has 3 parts:

* the datasource collector (findhost-collector) which collects all data and stores in the collections folder
* the consolidator (findhost-consolidator) which consolidates all collections into a single file
* the findhost client script which is a frontend grep tool to parse the consolidated findhost file 

## DOCKER

Build process:

```
docker build --tag mwallraf/findhost-inventory:latest .
```

Start Docker:

```
docker run --detach --name findhost-inventory \
  -v /opt/findhost-inventory/output:/opt/findhost-inventory/output \
  -v /opt/findhost-inventory/log:/opt/findhost-inventory/log \
  -v /opt/findhost-inventory/collections:/opt/findhost-inventory/collections \
  -v /opt/findhost-inventory/etc/env-findhost-inventory:/opt/findhost-inventory/.env \
  -v /opt/findhost-inventory/etc/env-findhost-consolidator:/opt/findhost-inventory/consolidator/.env \
  -v /opt/findhost-inventory/etc/env-findhost-collector:/opt/findhost-inventory/collector/.env \
  -v /opt/findhost-inventory/etc/env-findhost-collector-frontix:/opt/findhost-inventory/collector/frontix/.env \
  mwallraf/findhost-inventory:latest
```


## RUN THE SCRIPT

Run the script without any options to see the help functions. See the individual collector and consolidator scripts for all the options.
Each script can be run individually as well for testing and debugging

```
bash findhost-populate.sh --collect --consolidate run
bash findhost-populate.sh archive
```

## ENVIRONMENT VARIABLES

```
# ENABLE EXTRA PYTHON DEBUGGING
#PYTHONVERBOSE=0

# ENABLE MORE VERBOSE LOGGING
VERBOSE=False

# GLOBAL LOG DIR, ALL SCRIPTS WILL LOG HERE
LOGDIR="$SCRIPTDIR/log"

# THE FINDHOST COLLECTIONS DIR
COLLECTIONSDIR="$SCRIPTDIR/collections"

# THE MAIN OUTPUT FOLDER WHERE THE FINDHOST DATA IS STORED
OUTPUTDIR="$SCRIPTDIR/output"

# THE MAIN FOLDER WHERE THE COLLECTOR SCRIPT CAN BE FOUND
COLLECTORDIR="$SCRIPTDIR/collector"

# THE MAIN FOLDER WHERE THE CONSOLIDATOR SCRIPT CAN BE FOUND
CONSOLIDATORDIR="$SCRIPTDIR/consolidator"



###########################################
## COLLECTOR VARIABLES
###########################################

# ENABLE THE FRONTIX COLLECTOR
RUN_COLLECTOR_FRONTIX=1

# FRONTIX COLLECTOR FOLDER
COLLECTOR_FRONTIX_FOLDER="$COLLECTORDIR/frontix"

# FRONTIX COLLECTOR QUERY FOLDER
QUERY_SQL_DIR="$COLLECTOR_FRONTIX_FOLDER/frontix_dump_queries"
#QUERY_SQL_DIR="$COLLECTOR_FRONTIX_FOLDER/frontix_dump_queries_test"

# FRONTIX COLLECTOR OUTPUT FOLDER
QUERY_OUTPUT_DIR="$COLLECTIONSDIR/frontix"

# FRONTIX COLLECTOR LIMIT QUERY RESULTS
#QUERY_LIMIT=10

# INCLUDE FRONTIX DB PARAMETERS
# EX USERNAME, DB, SERVER, ..
if [ -f "/etc/mydb-parameters" ]; then
    . /etc/mydb-parameters
else
    # VARIABLES USED FOR CONNECTIONS TO FRONTIX
    FTX_HOSTNAME="<HOSTNAME>"
    FTX_PORT="<PORT>"
    FTX_SERVICE="<SERVICE>"
    FTX_USER="<USERNAME>"
    FTX_PWD="<PASSWORD>"
fi



###########################################
## CONSOLIDATOR VARIABLES
###########################################

# FOLDER WHERE THE FRONTIX DATA CAN BE FOUND
NISFOLDER="$COLLECTIONSDIR/frontix"

# folder to be used by the script to store temp data
TEMPFOLDER="$CONSOLIDATORDIR/tmp"

# folder where the output result is stored
CONSOLIDATOR_OUTPUT_FOLDER="$OUTPUTDIR"
```
