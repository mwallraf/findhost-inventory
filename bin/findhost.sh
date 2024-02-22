#!/usr/bin/bash

## TODO:
##  -- exclude related VT's
##  -- append cols in FORMAT_COLS
##  VT90527 -> not in findhost ??

## VERSION:
## 2.0.0 - new findhost version based on output of "consolidate_frontix_files.py"
## 2.0.1 - add VDSL2TYPE in CSV format
## 2.0.2 - 20150811 - add PARTNER field
##                  - add "m" option to exclude the RELATED_KEYS column in searches
## 2.0.3 - 20150815 - add -s option to display the output of a single column
## 2.0.4 - 20150901 - add leased line details to detail output
## 2.0.5 - 20151023 - add "short" format
## 2.0.6 - 20151028 - add LABEL field in detailed output
## 2.0.7 - 20151123 - add extra CPE_ fields in detailed output
## 2.0.8 - 20151228 - update "short" format to include ACCOUNTID
## 2.0.9 - 20160113 - add "AUDIT_RESULT"
## 2.0.10 - 20160316 - add CPE_VDSL_BW_UPLOAD;CPE_VDSL_BW_DOWNLOAD;CPE_VDSL_LP_UPDATED
## 2.0.11 - 20160413 - add SITE_ details
## 2.0.12 - 20160413 - add LL_IPADDRESS
## 2.0.13 - 20161024 - add CPE_APN + CPE_SW_VERSION
## 2.0.14 - 20161025 - change brief output to support 6 digit VT
## 2.0.15 - 20161104 - add TACACS_CUST_* fields
## 2.0.16 - 20161227 - add VDSL_* fields
## 2.0.17 - 20170412 - add CPE_CELLULAR_* fields + add 'mobile' output
## 2.0.18 - 20170814 - add CPE_VDSL_* fields to show the configured QOS + automatic update status
## 2.0.19 - 20171019 - add CES_VLAN_ID
## 2.0.20 - 20180726 - add TIMESLOT
## 2.0.21 - 20181123 - add 'gwos' output
## 2.0.22 - 20190419 - add TACACS_REALM
## 2.0.23 - 20190507 - add TRUVIEW_SITE_AUTOGEN
## 2.0.24 - 20200114 - add TROPS SVLAN and VSWITCH info
## 2.0.25 - 20200911 - add network-discovery fields DISC_
## 2.0.26 - 20210701 - add VT remarks
## 2.0.27 - 20210916 - add NPM columns
## 2.0.28 - 20211109 - add NPM domain columns
## 2.0.29 - 20220201 - add CPE_INTF_ALL_VT field
## 2.0.30 - 20231207 - add LDAP fields

VERSION="2.0.30"

## initalize parameters
SCRIPT="findhost"
BASEDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
FILTEREDFILE="../output/findhost.source.filtered.csv"
UNFILTEREDFILE="../output/findhost.source.csv"
# by default we use a filtered file to speed up the query
BASEFILE="$BASEDIR/$FILTEREDFILE"
# FILTER is the regex we will use, this should be a commandline parameter
FILTER=""
# FILTERCOLUMN is set when -C is used, to filter on a specific column
FILTERCOLUMN=""
GREP_OPTS=""
# EXACT_MATCH indicates if the RELATED_KEYS column is searched as well.  If enabled then this column is not included in searches
EXACT_MATCH=0
EXACT_MATCH_COLUMN=6
OUTPUT_FORMAT="brief"
OUTPUT_FORMAT_OPTIONS=("brief" "detail" "raw" "csv" "single" "short" "mobile")
DELIM=";"
COUNTER=0
# print a messages when running the script
MOTD=""
# count the number of displayed lines
# the output format can be overridden by settings in ~/.findhost
OVERRIDECONFIG=1
RECREATECONFIG=0
USERCONFIG=`echo ~/.findhost`

## columns can have | separator,  in that case the first found column with value will be used
#FORMAT_BRIEF_COLS="SERVICEID SERVICETYPE CPE_HOSTNAME|CPE_HOSTNAME_GUESS|HOSTNAME SERVICETYPE CPE_LOOPBACK|SERVICEID"
#FORMAT_BRIEF="%-6s <%s> %s [%s] %s\n"

FORMAT_BRIEF_COLS="SERVICEID SERVICETYPE CPE_HOSTNAME|CPE_HOSTNAME_GUESS|HOSTNAME CPE_LOOPBACK|OBS_CE_MAN_LOOPBACK|MOBICUSTOMERLOOPBACK|EQUIPMENT_IPADDRESS|MANAGEMENTIP|CPE_WAN_IP|LL_IPADDRESS PE_VAR PE_VAR_INT PE_VAR_INT_STATUS BANDWIDTH|CAPACITY"
FORMAT_BRIEF="%-6s <%s> %s [%s]|%s %s (%s) (%s)"
#FORMAT_BRIEF_POSTPROCESS="awk -F'|' '{printf \"%100s %s\n\",$1,$2}'"
FORMAT_BRIEF_POSTPROCESS="awk -F'|' '{printf \"%-70s %s\n\",\$1,\$2}'"

FORMAT_DETAIL_COLS="SERVICEID GSID SERVICETYPE CPE_INTF_ALL_VT LOOKUP_VALUE PARTNER ACCOUNTNAME ACCOUNTID SITE_ID SITE_SITENAME SITE_STREET SITE_ZIPCODE SITE_CITY SITE_COUNTRY TRUVIEW_SITE_AUTOGEN TRUVIEW_SITE_DESCR_AUTOGEN NPM_BW_DOWN_MB NPM_BW_UP_MB NPM_SITE_DESCR NPM_SITE_NAME DSID MACDREMARK PM_FULLNAME PM_EMAILADDRESS RELATED_KEYS CPE_HOSTNAME|CPE_HOSTNAME_GUESS|HOSTNAME CPE_LOOPBACK|MOBICUSTOMERLOOPBACK CPE_LOOPBACK_PINGABLE EQUIPMENT_IPADDRESS EQUIPMENT_SUBNET EQUIPMENT_IPADDRESS_END MANAGEMENTIP GATEWAYIP COMPONENTID COMPONENTDESCRIPTION EQUIPMENTDESCRIPTION EQUIPMENTLABEL NETWORKELEMENT CIRCUIT_ID CIRCUIT_CAPACITY TIMESLOT TIMESLOT_B STATUS_CIRCUIT PORTLABEL_A PORTLABEL_B CES_SVLAN_ID TDI_ID PORT_UNI STATUS_TDI CAPACITY PROJECTID VDSL2TYPE DSL_SERVICE SERVICE LINEPROFILE VLANPROFILE CPE_VDSL_LP CPE_VDSL_BW_UPLOAD CPE_VDSL_BW_DOWNLOAD CPE_VDSL_LP_UPDATED CPE_VDSL_LP_MESSAGE LEX BANDWIDTH COPPERLINEID ORDERREF MAXDOWNSTREAM MAXUPSTREAM CPE_VENDOR ROUTERTYPE CPE_SW_TYPE CPE_SW_VERSION CPE_CHASSIS CPE_TRANSMISSION CPE_APN CPE_CELLULAR_IMEI CPE_CELLULAR_IMSI CPE_CELLULAR_CELLID CPE_CELLULAR_OPERATOR CPE_INTF_FUNCTION CPE_INFO_FROM DISC_DOMAINNAME DISC_COMMUNITY DISC_VENDOR DISC_HWTYPE DISC_FUNCTION DISC_SERVICE DISC_PROTOCOL PE_VAR PE_VAR_INT PE_VAR_INT_DESCR VRF COMPONENT_VPN_NAME TACACS_REALM VDSL_BW_UPSTREAM VDSL_BW_DOWNSTREAM VDSL_SVLAN_ID VDSL_SVLAN VDSL_BAS VDSL_SVLAN_PURPOSE VDSL_SVLAN_QOS_PBIT VDSL_SVLAN_BW_MBPS VDSL_SVLAN_NBR_CUSTOMERS VDSL_SVLAN_BW_PER_CUSTOMER VDSL_SVLAN_PCT_OVERBOOKING VDSL_SVLAN_NAME VDSL_SVLAN_TRUNK VDSL_LAG VDSL_CPEUSERNAME VDSL_CPEPASSWORD LL_ID LL_LINEID LL_STATUS LL_BW LL_LINETYPE LL_DSID LL_BOFID LL_OLO LL_CONTRACTENDDATE LL_CONTRACTSTARTDATE LL_CONNECTORTYPE_A LL_ZONE LL_SITEID_A LL_LOCATIONNAME_A LL_LOCATIONADDRESS_A LL_LOCATIONNAME_B LL_LOCATIONADDRESS_B LL_CONNECTORTYPE_B LL_REQUESTEDDATE LL_RFSACTUALDATE LL_CANCELDATE LL_ISHALFLINK LL_ISMULTILINK LL_SALESDEPT LABEL AUDIT_RESULT LL_IPADDRESS TACACS_CUST_REALM TACACS_CUST_TACGROUP NPM_LOGIN NPM_PSW NPM_IP NPM_DOMAIN_NAME NPM_DOMAIN_ID SVLAN_CONNECTIONID SVLAN_STATUS SVLAN_LABEL SVLAN_PRT SVLAN_CAPACITY SVLAN_TYPE SVLAN_PROJECTID_A SVLAN_PROJECTID_B SVLAN_LABEL_SHORT VSWITCH_CONNECTIONID VSWITCH_STATUS VSWITCH_LABEL VSWITCH_PRT VSWITCH_CAPACITY VSWITCH_PROJECTID_A VSWITCH_PROJECTID_B VSWITCH_LABEL_SHORT REMARKS_PROVISION REMARKS_SERVICE REMARKS_ACCOUNT REMARKS_CONTRACT LDAP_ACTIVE LDAP_STATUS LDAP_MOBICUSTOMERPOLICING"
FORMAT_DETAIL="%s: %s\n"
FORMAT_DETAIL_POSTPROCESS="cat"

FORMAT_CSV_HEADER="SERVICEID CPE_INTF_ALL_VT SERVICETYPE CUSTOMER CPE_HOSTNAME CPE_LOOPBACK PE_VAR PE_VAR_INT PE_VAR_INT_STATUS BANDWIDTH DSID VDSL2TYPE PARTNER"
FORMAT_CSV_COLS="SERVICEID SERVICETYPE ACCOUNTNAME CPE_HOSTNAME|CPE_HOSTNAME_GUESS|HOSTNAME CPE_LOOPBACK|OBS_CE_MAN_LOOPBACK|MOBICUSTOMERLOOPBACK|MANAGEMENTIP|CPE_WAN_IP|LL_IPADDRESS PE_VAR PE_VAR_INT PE_VAR_INT_STATUS BANDWIDTH|CAPACITY DSID VDSL2TYPE PARTNER"
FORMAT_CSV="%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n"
FORMAT_CSV_POSTPROCESS="cat"

FORMAT_SHORT_COLS="SERVICEID CPE_HOSTNAME|CPE_HOSTNAME_GUESS|HOSTNAME CPE_LOOPBACK|OBS_CE_MAN_LOOPBACK|MOBICUSTOMERLOOPBACK|MANAGEMENTIP|CPE_WAN_IP|LL_IPADDRESS VRF ACCOUNTID PM_FULLNAME PM_EMAILADDRESS"
FORMAT_SHORT="%-5s %s %s %s %s %s\n"
FORMAT_SHORT_POSTPROCESS="cat"

FORMAT_MOBILE_HEADER="SERVICEID SERVICETYPE CUSTOMER CPE_HOSTNAME IMEI IMSI OPERATOR CELLID"
FORMAT_MOBILE_COLS="SERVICEID SERVICETYPE ACCOUNTNAME CPE_HOSTNAME|CPE_HOSTNAME_GUESS|HOSTNAME CPE_CELLULAR_IMEI CPE_CELLULAR_IMSI CPE_CELLULAR_OPERATOR CPE_CELLULAR_CELLID"
FORMAT_MOBILE="%s;%s;%s;%s;%s;%s;%s;%s\n"
FORMAT_MOBILE_POSTPROCESS="cat"

FORMAT_TROPS_HEADER="SERVICEID SERVICETYPE ACCOUNTNAME TDI_ID"
FORMAT_TROPS_COLS="SERVICEID SERVICETYPE ACCOUNTNAME TDI_ID"
FORMAT_TROPS="%s;%s;%s;%s\n"
FORMAT_TROPS_POSTPROCESS="cat"

## BOT FIX IMPLEMENTATION
FORMAT_GWOS_COLS="SERVICEID LOOKUP_VALUE SERVICETYPE ACCOUNTID CPE_HOSTNAME|CPE_HOSTNAME_GUESS|HOSTNAME CPE_LOOPBACK|OBS_CE_MAN_LOOPBACK|MOBICUSTOMERLOOPBACK|MANAGEMENTIP|CPE_WAN_IP|LL_IPADDRESS VRF"
FORMAT_GWOS="%s: %s\n"
FORMAT_GWOS_POSTPROCESS="cat"
## END

#Set fonts for Help.
NORM=`tput sgr0`
BOLD=`tput bold`
REV=`tput smso`

# function to read the private config file
# if no private config file exists then one is created
# the private config file can override the FORMAT_BRIEF and FORMAT_DETAIL info
function GETCONFIG {
    if [ ! -f "$USERCONFIG" ] || [ $RECREATECONFIG == 1 ]; then
        MOTD="$SCRIPT has changed! Timeslot info has been added."
        cat > ${USERCONFIG} << EOF
#
# this file overrides the default ${SCRIPT} output format
# define your own columns and output format, the format syntax is based on "printf"
# remove this file to use the default output format again
#

# "brief" output format
FORMAT_BRIEF_COLS="${FORMAT_BRIEF_COLS}"
FORMAT_BRIEF="${FORMAT_BRIEF}"
FORMAT_BRIEF_POSTPROCESS="awk -F'|' '{printf \"%-70s %s\n\",\\\$1,\\\$2}'"

# "detail" output format
FORMAT_DETAIL_COLS="${FORMAT_DETAIL_COLS}"
FORMAT_DETAIL="${FORMAT_DETAIL}"
FORMAT_DETAIL_POSTPROCESS="cat"

# "csv" output format
FORMAT_CSV_HEADER="${FORMAT_CSV_HEADER}"
FORMAT_CSV_COLS="${FORMAT_CSV_COLS}"
FORMAT_CSV="${FORMAT_CSV}"
FORMAT_CSV_POSTPROCESS="cat"

EOF
    fi

    if [ $OVERRIDECONFIG == 1 ]; then
        source $USERCONFIG
    fi
}


## display the available columns and exit
function displayfields {
    HEADER=`head -n 1 $BASEFILE`
    HEADER_COLS=(${HEADER//$DELIM/ })
    for i in "${!HEADER_COLS[@]}"
    do
        printf "%s => %s\n" ${HEADER_COLS[i]} $i
    done
    exit 0
}


## update the output counter
function updatecounter {
    let COUNTER++
}


## print the message of the day
function motd {
    if [ -n "$MOTD" ]; then
        echo
        echo $MOTD
        echo
    fi
}

# Help function
function HELP {
cat | more <<ENDOFHELP
Help documentation for ${BOLD}${SCRIPT}${NORM}

The ${SCRIPT} script searches in the MES database and returns output in different format types.
The source data is refreshed daily and is based on various NIS queries.
Searches can be done on any field: VT, customer, service, VAR, loopback, SH, VDSL etc.

${REV}default values:${NORM}
    * only the 'Completed' and 'Ongoing' VT's are displayed, to show all VT's use option -a
    * all searches are case sensitive, for case insensitive searches use option -i
    * the default output format is 'brief', use -o <format> to change this
    * searches are done on all fields, use -F <field> to search on one specific field

${REV}Basic usage:${NORM} ${BOLD}$SCRIPT VT89123${NORM}

${REV}Command line switches${NORM} are optional. The following switches are recognized.
${BOLD}-a${NORM}  --Searches for ${BOLD}ALL VT's${NORM} in the NIS database. By default Ongoing and Completed VT's are shown.
${BOLD}-i${NORM}  --Makes the search ${BOLD}case insensitive${NORM}. By default all searches are case sensitive.
${BOLD}-m${NORM}  --Makes the search return ${BOLD}exact matches${NORM} by removing the RELATED_KEYS field.
${BOLD}-o <format>${NORM}  --Sets the ${BOLD}output format${NORM}. The default is 'brief'.
${BOLD}-c${NORM}  --Sets the ${BOLD}csv${NORM} output format. This is the same as '-o brief'
${BOLD}-d${NORM}  --Sets the ${BOLD}detailed${NORM} output format. This is the same as '-o detail'
${BOLD}-g${NORM}  --Sets the ${BOLD}gwos${NORM} output format with exact match.'
${BOLD}-r${NORM}  --Sets the ${BOLD}raw${NORM} output format. This is the same as '-o raw'
${BOLD}-S${NORM}  --Sets the ${BOLD}short${NORM} output format. This is the same as '-o short'
${BOLD}-M${NORM}  --Sets the ${BOLD}mobile${NORM} output format. This is the same as '-o mobile'
${BOLD}-T${NORM}  --Sets the ${BOLD}TROPS${NORM} output format. This is the same as '-o trops'
${BOLD}-s <field>${NORM}  --Only displays the value of the specified field.
${BOLD}-f <field>${NORM}  --Search for the value in ${BOLD}a specific field${NORM}. By default the search is done on all fields.
${BOLD}-F${NORM}  --${BOLD}Display all fields${NORM}. Fields can be used with the -f option.
${BOLD}-R${NORM}  --Recreates the user specific config file (~/.$SCRIPT)
${BOLD}-D${NORM}  --Use the script default settings instead of the user specific config file. Default is to use the user specific config
${BOLD}-h${NORM}  --Displays this help message and exits.

${REV}Examples:${NORM}
    * $SCRIPT -d LL14-03-0002                => show detailed output while searching for a leased line component
    * $SCRIPT -d -i ll14-03-0002             => the same but using a case insensitive search
    * $SCRIPT -o csv "Corporate Internet"    => return all corporate internet VT's in CSV format
    * $SCRIPT -M FIXB2B4G-PR                 => return all VT's with APN FIXB2B4G-PR in mobile format
    * $SCRIPT Inactive                       => returns all inactive VT's, should return nothing by default
    * $SCRIPT -a Inactive                    => returns all inactive VT's based on ALL VT search
    * $SCRIPT -f SERVICETYPE "IP-VPN"        => returns all VT's which have the value "IP-VPN" in the SERVICETYPE field
    * $SCRIPT -f SERVICE dedicated           => returns all "VDSL2 Dedicated" VT's
    * $SCRIPT -f SERVICE internet            => returns all "VDSL2 Shared" VT's
    * $SCRIPT -f PARTNER OBS                 => returns all OBS connected CPE's
    * $SCRIPT -m VT88559                     => returns exact match for VT88559 (without related VT's)
    * $SCRIPT CIRCUIT_CAPACITY E1            => returns all VT's which have an E1 circuit assigned
    * $SCRIPT -f PARTNER -s OBS_CE_MAN_LOOPBACK OBS => returns all loopback IP's for OBS managed CPE's

${REV}Supported format types:${NORM}
    * brief: one line per VT in easy to read format
    * detail: one line per field grouped by VT
    * csv: one line per VT with CSV delimiter and file header
    * raw: displays the output as found in the original database file
    * short: displays one line per VT containing only VT HOSTNAME LOOPBACK
    * mobile: one line per VT with CSV delimiter and file header including  cellular and sim card info
    * trops: one line per VT with CSV delimiter and file header including TDI

${REV}User specific config ~/.$SCRIPT:${NORM}
    It is possible to override the default output format settings for 'brief', 'detail' and 'raw'.
    This is done by changing the settings in the user's home dir '~/.$SCRIPT'.
    After changing these settings your user account will have a customized $SCRIPT output format.
    You can run $SCRIPT with the default settings by specifying option -D.
    By using the option -R your config file will be removed and recreated with default settings.
    You can choose the columns you want to show and customize the output format. The output format should follow the 'printf' standards

---
$SCRIPT v2a - Maarten Wallraf <maarten.wallraf@orange.com> (FIX OPS)
---
ENDOFHELP
  exit 1
}



### Start getopts code ###

#Parse command line flags
#If an option should be followed by an argument, it should be followed by a ":".
#Notice there is no ":" after "h". The leading ":" suppresses error messages from
#getopts. This is required to get my unrecognized option code to work.

while getopts :acdgrio:SRf:Fms:hMT FLAG; do
  case $FLAG in
    a)  #set option "a" = use unfiltered file instead of default filtered
      BASEFILE="$BASEDIR/$UNFILTEREDFILE"
      ;;
    c)  # csv output, shortcut for -o csv
      OUTPUT_FORMAT="csv"
      ;;
    S) # short output format, shortcut for -o short
      OUTPUT_FORMAT="short"
      ;;
    f) # filter on a specific column
      FILTERCOLUMN=$OPTARG
      ;;
    F) # display all fields and exit
      displayfields
      ;;
    d)  # set option "d" - shortcut for -o detail
      OUTPUT_FORMAT='detail'
      ;;
    i) # set grep -i option (case insensitive)
      GREP_OPTS="$GREP_OPTS -i "
      ;;
    s) # single output column
      SINGLECOLUMN=$OPTARG
      OUTPUT_FORMAT='single'
      ;;
    o) # output format (brief, detail, raw, trops, mobile)
      OUTPUT_FORMAT=$OPTARG
      match=0
      for ofo in "${OUTPUT_FORMAT_OPTIONS[@]}"; do
          if [[ $ofo == "$OUTPUT_FORMAT" ]]; then
              match=1
              break
          fi
      done
      if [[ $match == 0 ]]; then
          echo "${BOLD}ERROR: output format '$OUTPUT_FORMAT' is not supported - using 'brief' output${NORM}"
          OUTPUT_FORMAT="brief"
      fi
      ;;
    O) # do not override the output format defined in the user's home dir ~/.findhost
      OVERRIDECONFIG=0
      ;;
    R) # recreate the user's private output format ~/.findhost
      RECREATECONFIG=1
      ;;
    r) # raw output = shortcut for -o raw
      OUTPUT_FORMAT='raw'
      ;;
    M) # mobile output = shortcut for -o mobile
      OUTPUT_FORMAT='mobile'
      ;;
    T) # trops output = shortcut for -o trops
      OUTPUT_FORMAT='trops'
      ;;
    m) # match exact values, do not include RELATED_KEYS column
      EXACT_MATCH=1
      ;;
    g) # groundworks graphs request information for BOT FIX
      EXACT_MATCH=1
      OUTPUT_FORMAT='gwos'
      ;;
    h)  #show help
      HELP
      ;;
    \?) #unrecognized option - show help
      echo -e \\n"Option -${BOLD}$OPTARG${NORM} not allowed."
      HELP
      #If you just want to display a simple error message instead of the full
      #help, remove the 2 lines above and uncomment the 2 lines below.
      #echo -e "Use ${BOLD}$SCRIPT -h${NORM} to see the help documentation."\\n
      #exit 2
      ;;
  esac
done

shift $((OPTIND-1))  #This tells getopts to move on to the next argument.
FILTER="$@"
REGEX="^.*$FILTER.*$"

## a filter is needed, otherwise exit
if [ -z "$FILTER" ]; then
    echo ""
    echo "${BOLD}ERROR: you must provide a filter${NORM}"
    echo ""
    HELP
fi

### End getopts code ###


## start main code ##

## GET USER CONFIG
GETCONFIG

## parse the header and make column mappings
## filter out the "RELATED_KEYS" column when needed
if [ $EXACT_MATCH == 1 ]; then
    HEADER=`head -n 1 $BASEFILE | cut -d";" -f$EXACT_MATCH_COLUMN --complement`
else
    HEADER=`head -n 1 $BASEFILE`
fi

# make a new list of the header columns
HEADER_COLS=(${HEADER//$DELIM/ })

# map the column id to the column name and store in variable C_column
for i in "${!HEADER_COLS[@]}"
do
    declare -x "C_${HEADER_COLS[i]}"=$i
done


## if -C is provided then check if the column exists
FILTERCOL=C_$FILTERCOLUMN
if [ -n "$FILTERCOLUMN" ] && [ -z ${!FILTERCOL} ]; then
    echo ""
    echo "${BOLD}ERROR: the column '$FILTERCOLUMN' does not exist${NORM}"
    echo ""
    exit 0
fi

## print the message of the day
motd


## create the grep function
## filter out the "RELATED_KEYS" column when needed
if [ $EXACT_MATCH == 1 ]; then
    ## TODO: make this dynamic somehow
    GREP_COMMAND="cut -d\";\" -f$EXACT_MATCH_COLUMN --complement $BASEFILE | grep $GREP_OPTS -e '$FILTER'"
else
    GREP_COMMAND="grep $GREP_OPTS -e '$FILTER' $BASEFILE"
fi

#echo $GREP_COMMAND

## print raw format
case $OUTPUT_FORMAT in
   'raw') # raw output
       #echo "raw output"
       echo $HEADER
       while read -r line; do
           echo $line
           echo
           updatecounter
       done < <(eval ${GREP_COMMAND})
       ;;
   'csv') # csv output
       printf "$FORMAT_CSV" $FORMAT_CSV_HEADER
       while read -r line ; do
           declare AWKPARAM=()
           IFS=$DELIM read -a SPLITLINE <<<"$line"
           # see if we need to filter on a column, if no match then skip line
           if [ -n "$FILTERCOLUMN" ]; then
               F="${SPLITLINE[$FILTERCOL]}"
               if [ -n "$F" ]; then
                   MATCHCOLUMN=`echo "$F" | grep $GREP_OPTS -e "$FILTER"`
                   if [ -z "$MATCHCOLUMN" ];then
                       continue
                   fi
               else
                   continue
               fi
           fi
           for c in $FORMAT_CSV_COLS
           do
               ## we can have multiple columns defined delimited by |
               ## the first column for which a value is found will be printed
               declare ALLKEYS=()
               IFS=\| read -a ALLKEYS <<<"$c"
               FOUNDVALUE=0
               for akey in ${ALLKEYS[@]}
               do
                   key=C_$akey
                   colid=${!key}
                   value="${SPLITLINE[$colid]}"
                   if [ -n "$value" ]; then
                       AWKPARAM=("${AWKPARAM[@]}" "$value")
                       FOUNDVALUE=1
                       break
                   fi
               done
               if [ $FOUNDVALUE == 0 ]; then
                   AWKPARAM=("${AWKPARAM[@]}" "")
               fi
           done
           printf "$FORMAT_CSV" "${AWKPARAM[@]}" | eval ${FORMAT_CSV_POSTPROCESS}
           updatecounter
       done < <(eval ${GREP_COMMAND})
       ;;
   'mobile') # mobile output
       printf "$FORMAT_MOBILE" $FORMAT_MOBILE_HEADER
       while read -r line ; do
           declare AWKPARAM=()
           IFS=$DELIM read -a SPLITLINE <<<"$line"
           # see if we need to filter on a column, if no match then skip line
           if [ -n "$FILTERCOLUMN" ]; then
               F="${SPLITLINE[$FILTERCOL]}"
               if [ -n "$F" ]; then
                   MATCHCOLUMN=`echo "$F" | grep $GREP_OPTS -e "$FILTER"`
                   if [ -z "$MATCHCOLUMN" ];then
                       continue
                   fi
               else
                   continue
               fi
           fi
           for c in $FORMAT_MOBILE_COLS
           do
               ## we can have multiple columns defined delimited by |
               ## the first column for which a value is found will be printed
               declare ALLKEYS=()
               IFS=\| read -a ALLKEYS <<<"$c"
               FOUNDVALUE=0
               for akey in ${ALLKEYS[@]}
               do
                   key=C_$akey
                   colid=${!key}
                   value="${SPLITLINE[$colid]}"
                   if [ -n "$value" ]; then
                       AWKPARAM=("${AWKPARAM[@]}" "$value")
                       FOUNDVALUE=1
                       break
                   fi
               done
               if [ $FOUNDVALUE == 0 ]; then
                   AWKPARAM=("${AWKPARAM[@]}" "")
               fi
           done
           printf "$FORMAT_MOBILE" "${AWKPARAM[@]}" | eval ${FORMAT_MOBILE_POSTPROCESS}
           updatecounter
       done < <(eval ${GREP_COMMAND})
       ;;
   'trops') # trops output
       printf "$FORMAT_TROPS" $FORMAT_TROPS_HEADER
       while read -r line ; do
           declare AWKPARAM=()
           IFS=$DELIM read -a SPLITLINE <<<"$line"
           # see if we need to filter on a column, if no match then skip line
           if [ -n "$FILTERCOLUMN" ]; then
               F="${SPLITLINE[$FILTERCOL]}"
               if [ -n "$F" ]; then
                   MATCHCOLUMN=`echo "$F" | grep $GREP_OPTS -e "$FILTER"`
                   if [ -z "$MATCHCOLUMN" ];then
                       continue
                   fi
               else
                   continue
               fi
           fi
           for c in $FORMAT_TROPS_COLS
           do
               ## we can have multiple columns defined delimited by |
               ## the first column for which a value is found will be printed
               declare ALLKEYS=()
               IFS=\| read -a ALLKEYS <<<"$c"
               FOUNDVALUE=0
               for akey in ${ALLKEYS[@]}
               do
                   key=C_$akey
                   colid=${!key}
                   value="${SPLITLINE[$colid]}"
                   if [ -n "$value" ]; then
                       AWKPARAM=("${AWKPARAM[@]}" "$value")
                       FOUNDVALUE=1
                       break
                   fi
               done
               if [ $FOUNDVALUE == 0 ]; then
                   AWKPARAM=("${AWKPARAM[@]}" "")
               fi
           done
           printf "$FORMAT_TROPS" "${AWKPARAM[@]}" | eval ${FORMAT_TROPS_POSTPROCESS}
           updatecounter
       done < <(eval ${GREP_COMMAND})
       ;;
   'detail') # detailed output
       #echo "detailed output"
       while read -r line ; do
           NEWLINE=""
           IFS=$DELIM read -a SPLITLINE <<<"$line"
           # see if we need to filter on a column, if no match then skip line
           if [ -n "$FILTERCOLUMN" ]; then
               F="${SPLITLINE[$FILTERCOL]}"
               if [ -n "$F" ]; then
                   MATCHCOLUMN=`echo "$F" | grep $GREP_OPTS -e "$FILTER"`
                   if [ -z "$MATCHCOLUMN" ];then
                       continue
                   fi
               else
                   continue
               fi
           fi
           for c in $FORMAT_DETAIL_COLS
           do
               ## we can have multiple columns defined delimited by |
               ## the first column for which a value is found will be printed
               declare ALLKEYS=()
               IFS=\| read -a ALLKEYS <<<"$c"
               FOUNDVALUE=0
               for akey in ${ALLKEYS[@]}
               do
                   key=C_$akey
                   colid=${!key}
                   value=${SPLITLINE[$colid]}
                   ## only print out if the column has a value
                   if [ -n "$value" ]; then
                       printf "$FORMAT_DETAIL" "$akey" "$value" | eval $FORMAT_DETAIL_POSTPROCESS
                       updatecounter
                       break
                   fi
               done
           done
           echo
       done < <(eval ${GREP_COMMAND})
       ;;
   'short') # short output
       #echo "short output"
       #eval ${GREP_COMMAND} | while read -r line ; do
       while read -r line ; do
           declare AWKPARAM=()
           IFS=$DELIM read -a SPLITLINE <<<"$line"
           # see if we need to filter on a column, if no match then skip line
           if [ -n "$FILTERCOLUMN" ]; then
               F="${SPLITLINE[$FILTERCOL]}"
               if [ -n "$F" ]; then
                   MATCHCOLUMN=`echo "$F" | grep $GREP_OPTS -e "$FILTER"`
                   if [ -z "$MATCHCOLUMN" ];then
                       continue
                   fi
               else
                   continue
               fi
           fi
           for c in $FORMAT_SHORT_COLS
           do
               ## we can have multiple columns defined delimited by |
               ## the first column for which a value is found will be printed
               declare ALLKEYS=()
               IFS=\| read -a ALLKEYS <<<"$c"
               FOUNDVALUE=0
               for akey in ${ALLKEYS[@]}
               do
                   key=C_$akey
                   colid=${!key}
                   value="${SPLITLINE[$colid]}"
                   if [ -n "$value" ]; then
                       AWKPARAM=("${AWKPARAM[@]}" "$value")
                       FOUNDVALUE=1
                       break
                   fi
               done
               if [ $FOUNDVALUE == 0 ]; then
                   AWKPARAM=("${AWKPARAM[@]}" "-")
               fi
           done
           printf "$FORMAT_SHORT" "${AWKPARAM[@]}" | eval ${FORMAT_SHORT_POSTPROCESS}
           updatecounter
       done < <(eval ${GREP_COMMAND})
       ;;
   'single') # single column output
       #echo "single column output"
       while read -r line ; do
           NEWLINE=""
           IFS=$DELIM read -a SPLITLINE <<<"$line"
           # see if we need to filter on a column, if no match then skip line
           if [ -n "$FILTERCOLUMN" ]; then
               F="${SPLITLINE[$FILTERCOL]}"
               if [ -n "$F" ]; then
                   MATCHCOLUMN=`echo "$F" | grep $GREP_OPTS -e "$FILTER"`
                   if [ -z "$MATCHCOLUMN" ];then
                       continue
                   fi
               else
                   continue
               fi
           fi
           key=C_$SINGLECOLUMN
           colid=${!key}
           value=${SPLITLINE[$colid]}
           if [ -n "$value" ]; then
               printf "$value\n"
               updatecounter
           fi
       done < <(eval ${GREP_COMMAND})
       ;;

    'gwos') # groundworks output
       #echo "groundworks output"
       while read -r line ; do
           NEWLINE=""
           IFS=$DELIM read -a SPLITLINE <<<"$line"
           # see if we need to filter on a column, if no match then skip line
           if [ -n "$FILTERCOLUMN" ]; then
               F="${SPLITLINE[$FILTERCOL]}"
               if [ -n "$F" ]; then
                   MATCHCOLUMN=`echo "$F" | grep $GREP_OPTS -e "$FILTER"`
                   if [ -z "$MATCHCOLUMN" ];then
                       continue
                   fi
               else
                   continue
               fi
           fi
           for c in $FORMAT_GWOS_COLS
           do
               ## we can have multiple columns defined delimited by |
               ## the first column for which a value is found will be printed
               declare ALLKEYS=()
               IFS=\| read -a ALLKEYS <<<"$c"
               FOUNDVALUE=0
               for akey in ${ALLKEYS[@]}
               do
                   key=C_$akey
                   colid=${!key}
                   value=${SPLITLINE[$colid]}
                   ## only print out if the column has a value
                   if [ -n "$value" ]; then
                       printf "$FORMAT_GWOS" "$akey" "$value" | eval $FORMAT_GWOS_POSTPROCESS
                       updatecounter
                       break
                   fi
               done
           done
           echo
       done < <(eval ${GREP_COMMAND})
       ;;
   *) # brief output
       #echo "brief output"
       #eval ${GREP_COMMAND} | while read -r line ; do
       while read -r line ; do
           declare AWKPARAM=()
           IFS=$DELIM read -a SPLITLINE <<<"$line"
           # see if we need to filter on a column, if no match then skip line
           if [ -n "$FILTERCOLUMN" ]; then
               F="${SPLITLINE[$FILTERCOL]}"
               if [ -n "$F" ]; then
                   MATCHCOLUMN=`echo "$F" | grep $GREP_OPTS -e "$FILTER"`
                   if [ -z "$MATCHCOLUMN" ];then
                       continue
                   fi
               else
                   continue
               fi
           fi
           for c in $FORMAT_BRIEF_COLS
           do
               ## we can have multiple columns defined delimited by |
               ## the first column for which a value is found will be printed
               declare ALLKEYS=()
               IFS=\| read -a ALLKEYS <<<"$c"
               FOUNDVALUE=0
               for akey in ${ALLKEYS[@]}
               do
                   key=C_$akey
                   colid=${!key}
                   value="${SPLITLINE[$colid]}"
                   if [ -n "$value" ]; then
                       AWKPARAM=("${AWKPARAM[@]}" "$value")
                       FOUNDVALUE=1
                       break
                   fi
               done
               if [ $FOUNDVALUE == 0 ]; then
                   AWKPARAM=("${AWKPARAM[@]}" "-")
               fi
           done
           printf "$FORMAT_BRIEF" "${AWKPARAM[@]}" | eval ${FORMAT_BRIEF_POSTPROCESS}
           updatecounter
       done < <(eval ${GREP_COMMAND})
       ;;
esac

## print some message when no results were found
if [ $COUNTER == 0 ]; then
    printf "\nNo matches found. You may want to use options -a or -i\n\n"
fi

exit 0

