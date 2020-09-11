# FINDHOST-CONSOLIDATOR

This is the main Findhost consolidator script that merges all the files in the collections folder into a single output file.

## RUN THE SCRIPT

This script should be run by the findhost-populate.sh script however it can be run seperately as well.

If the environment variable FINDHOST_VALIDATOR is not set then the local .env file will be loaded, if it exists.

```
bash findhost-consolidator.sh
```


## ENVIRONMENT VARIABLES

```
# enable if you want verbose python debugging info
#PYTHONVERBOSE=1

# enable more verbose logging
VERBOSE=False

# location of the findhost-consolidator.sh script
CONSOLIDATORDIR="."

# location of the log folder
LOGDIR="log"

# location of the findhost collections
COLLECTIONSDIR="../collections"

# location where all the frontix files can be found
NISFOLDER="$COLLECTIONSDIR/frontix"

# folder to be used by the script to store temp data
TEMPFOLDER="tmp"

# folder where the output result is stored
CONSOLIDATOR_OUTPUT_FOLDER="output"
```

