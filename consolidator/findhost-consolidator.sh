#!/bin/bash

# Shell script to start the findhost-consolidator script
# 
# To run the script as standalone then make sure the correct
# envvars exist in the .env file in the same folder
# The local .env file is only imported if the FINDHOST_VALIDATOR
# does not exist.
# If it exists then it's set by the parent script
#

echo "start findhost consolidator at: "`date +"%Y-%m-%d %H:%M"`

if [ -z "$FINDHOST_VALIDATOR" ]
then
    . .env
    echo "using local .env file"

    # export variables to be used within the python script
    SCRIPTDIR=$(dirname "${BASH_SOURCE[0]}")
fi

# export variables to be used by the python script
export VERBOSE
export SCRIPTDIR
export LOGDIR
export TEMPFOLDER
export NISFOLDER
export CONSOLIDATOR_OUTPUT_FOLDER
export COLLECTIONSDIR

python $CONSOLIDATORDIR/findhost-consolidator.py

echo "end findhost consolidator at: "`date +"%Y-%m-%d %H:%M"`
