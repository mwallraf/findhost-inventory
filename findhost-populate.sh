#!/bin/bash -e
#
# Generic Shell Script Skeleton.
# Copyright (c) {{ YEAR }} - {{ AUTHOR }} <{{ AUTHOR_EMAIL }}>
#
# Built with shell-script-skeleton v0.0.3 <http://github.com/z017/shell-script-skeleton>

readonly SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Import common utilities
source "$SCRIPTDIR/functions/common.sh"

#######################################
# SCRIPT CONSTANTS & VARIABLES
#######################################

# Script version
readonly VERSION=0.0.1

# List of required tools, example: REQUIRED_TOOLS=(git ssh)
readonly REQUIRED_TOOLS=()

# Long Options. To expect an argument for an option, just place a : (colon)
# after the proper option flag.
readonly LONG_OPTS=(help version consolidate collect venv)

# Short Options. To expect an argument for an option, just place a : (colon)
# after the proper option flag.
readonly SHORT_OPTS=hv

# Script name
readonly SCRIPT_NAME=${0##*/}


#######################################
# SCRIPT CONFIGURATION CONSTANTS
#######################################

# read a local .env file if it exists
if [ -f "$SCRIPTDIR/.env" ]; then
  . $SCRIPTDIR/.env
fi

# Put here configuration constants
declare RUNCOLLECTOR=false
declare RUNCONSOLIDATOR=false
declare RUNVENV=false
declare FINDHOST_COLLECTOR=true
declare FINDHOST_VALIDATOR=true

# dir containing all data collections
if [ -z $COLLECTIONSDIR ]; then
  COLLECTIONSDIR="$SCRIPTDIR/collections"
fi

# dir containing the collector script
if [ -z $COLLECTORDIR ]; then
  COLLECTORDIR="$SCRIPTDIR/collector"
fi

# dir containing the collector script
if [ -z $COLLECTORSCRIPT ]; then
  COLLECTORSCRIPT="$COLLECTORDIR/findhost-collector.sh"
fi

# dir containing the consolidator script
if [ -z $CONSOLIDATORDIR ]; then
  CONSOLIDATORDIR="$SCRIPTDIR/consolidator"
fi

# dir containing the consolidator script
if [ -z $CONSOLIDATORSCRIPT ]; then
  CONSOLIDATORSCRIPT="$CONSOLIDATORDIR/findhost-consolidator.sh"
fi

# dir containing the log files
if [ -z $LOGDIR ]; then
  LOGDIR="$SCRIPTDIR/log"
fi

# dir containing the findhost output files
if [ -z $OUTPUTDIR ]; then
  OUTPUTDIR="$SCRIPTDIR/output"
fi

#######################################
# help command
#######################################
function help_command() {
  cat <<END;

USAGE:
  $SCRIPT_NAME [options] <command>

OPTIONS:
  --help, -h              Alias help command
  --version, -v           Alias version command
  --collect               Enable the findhost collector (disabled by default)
  --consolidate           Enable the consolidator (disabled by default)
  --venv                  Enable the python virtualenv (disabled by default)
  --                      Denotes the end of the options.  Arguments after this
                          will be handled as parameters even if they start with
                          a '-'.

COMMANDS:
  help                    Display detailed help
  version                 Print version information.
  run                     Run the findhost-populate script

END
  exit 1
}

#######################################
# version command
#######################################
function version_command() {
  echo "$SCRIPT_NAME version $VERSION"
}

#######################################
# default command
#######################################
function default_command() {
  # set default command here
  help_command
}


#######################################
# run the collector script
#######################################
function run_collector() {
  . $COLLECTORSCRIPT
}


#######################################
# run the consolidator script
#######################################
function run_consolidator() {
  . $CONSOLIDATORSCRIPT
}

#######################################
# main findhost-populate function
#######################################
function run_findhost_populate() {
  echo "start findhost-populate at: "`date +"%Y-%m-%d %H:%M"`

  if [ $RUNVENV == "true" ]; then
    source "$SCRIPTDIR/venv/bin/activate"
  fi

  if [ $RUNCOLLECTOR == "true" ]; then
    run_collector
  fi

  if [ $RUNCONSOLIDATOR == "true" ]; then
    run_consolidator
  fi

  echo "end findhost-populate at: "`date +"%Y-%m-%d %H:%M"`" ($SECONDS secs runtime)"
}

#######################################
#
# MAIN
#
#######################################
function main() {
  # Required tools
  required $REQUIRED_TOOLS

  # Parse options
  while [[ $# -ge $OPTIND ]] && eval opt=\${$OPTIND} || break
        [[ $opt == -- ]] && shift && break
        if [[ $opt == --?* ]]; then
          opt=${opt#--}; shift

          # Argument to option ?
          OPTARG=;local has_arg=0
          [[ $opt == *=* ]] && OPTARG=${opt#*=} && opt=${opt%=$OPTARG} && has_arg=1

          # Check if known option and if it has an argument if it must:
          local state=0
          for option in "${LONG_OPTS[@]}"; do
            [[ "$option" == "$opt" ]] && state=1 && break
            [[ "${option%:}" == "$opt" ]] && state=2 && break
          done
          # Param not found
          [[ $state = 0 ]] && OPTARG=$opt && opt='?'
          # Param with no args, has args
          [[ $state = 1 && $has_arg = 1 ]] && OPTARG=$opt && opt=::
          # Param with args, has no args
          if [[ $state = 2 && $has_arg = 0 ]]; then
            [[ $# -ge $OPTIND ]] && eval OPTARG=\${$OPTIND} && shift || { OPTARG=$opt; opt=:; }
          fi

          # for the while
          true
        else
          getopts ":$SHORT_OPTS" opt
        fi
  do
    case "$opt" in
      # List of options
      v|version)    version_command; exit 0; ;;
      h|help)       help_command ;;
      consolidate)  RUNCONSOLIDATOR=true ;;
      collect)      RUNCOLLECTOR=true ;;
      venv)         RUNVENV=true ;;
      # Errors
      ::) err "Unexpected argument to option '$OPTARG'"; exit 2; ;;
      :)  err "Missing argument to option '$OPTARG'"; exit 2; ;;
      \?) err "Unknown option '$OPTARG'"; exit 2; ;;
      *)  err "Internal script error, unmatched option '$opt'"; exit 2; ;;
    esac
  done
  readonly RUNCONSOLIDATOR
  readonly RUNCOLLECTOR
  readonly RUNVENV
  shift $((OPTIND-1))

  # No more arguments -> call default command
  [[ -z "$1" ]] && default_command

  # Set command and arguments
  command="$1" && shift
  args="$@"

  # Execute the command
  case "$command" in
    # help
    help)     help_command ;;

    # version
    version)  version_command ;;

    # version
    run)  run_findhost_populate ;;

    # Unknown command
    *)  err "Unknown command '$command'"; exit 2; ;;
  esac
}
#######################################
# Run the script
#######################################
main "$@"
