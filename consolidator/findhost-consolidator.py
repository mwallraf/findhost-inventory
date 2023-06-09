#!/usr/bin/python

# TODO:
# - put CPE component in separate column
# - component columns
# - make column for OBS routers (ip = 094.105.003.108-32)
# - make column for L2-IPVPN (ip = 10.50.x.x ??)
# - TODO: REMOVE column SERVICESTATUS (=synonym for LOOKUP_VALUE)
#         remove PE hardware, serial, ... info from CPE

#
# this script merges different files together to create a single inventory file
# input is based on Frontix dump files + findhost output + others
# a set of columns is defined (KEEPCOLS) and for each input file a new output is created with these set of columns
# if the column does not exist in the source file then the value will be empty
# The columns of the input file can be re-mapped to another column name so that it can match one of the columns in KEEPCOLS
# If different input files have different values for a collumn then the values are merged with @@ delimiter
# The output is generated in 2 stages:
#  - a temporary file is created with all the input files appended but each line will be in the same format with the columns defined by KEEPCOLS
#  - a new file is created based on the temporary file and duplicate lines are joined. The key is the first column (= SERVICEID by default)
# Some checks are done to try and find errors in the configuration, these errors are written to STDERR
# If there are different values found in different files for the same column then a warning is written to STDOUT
#
# OUTPUT files:
#   - unfiltered file containing ALL data found
#   - filtered file containing only lines which have a VT (=column 0) + LOOKUP_VALUE = Complated or Ongoing  (columns are not filtered or removed)
#

# VERSION:
#   v1.0.0 - initial version
#   v1.0.1 - 20150805 - updated passfilter()
#   v1.0.2 - 20150811 - add PARTNER field and OBS partner
#   v1.0.3 - 20150827 - SERVICESTATUS is now synonym for LOOKUP_VALUE
#   v1.0.4 - 20150901 - add LL leased line info
#                     - add error if the line does not match expected columns
#   v1.0.5 - 20151028 - add PARTNER OBS - if ESU matches 00350-ESU01-002/00-0/00-03/01
#   v1.0.6 - 20151123 - add extra CPE_ fields + findhost_new output file
#   v1.0.7 - 20151201 - add GW_ fields to include monthly utilization info (only for top x customers)
#   v1.0.8 - 20160113 - add cpe config audit info
#   v1.0.9 - 20160224 - add CPE_FIRSTEEN (first time we take a backup of the CPE), CPE_LASTSEEN (last time backup), CPE_VDSL_LP (auto-configured VDSL LP value)
#   v1.0.10 - 20160316 - add CPE_LP_BW_DOWN + CPE_LP_BW_UP + CPE_VDSL_LP_UPDATED
#   v1.0.11 - 20160413 - add SITE_ details
#   v1.0.12 - 20160513 - add INTEROUTE partner check
#   v1.0.13 - 20160521 - add LL_IPADDRESS
#   v1.0.14 - 20161024 - add CPE_APN + CPE_SW_VERSION
#   v1.0.15 - 20161104 - add TACACS_CUST_*
#   v1.0.16 - 20161227 - calculate LEX field from P0_DSLAMID
#                      - add VDSL_* fields
#   v1.0.17 - 20170412 - add CPE_CELLULAR_IMEI + CPE_CELLULAR_IMSI + CPE_CELLULAR_CELLID + CPE_CELLULAR_OPERATOR
#   v1.0.18 - 20170814 - add input file for VDSL qos upgrade result
#   v1.0.19 - 20171019 - add carrier ethernet CES_SVLAN_ID field
#   v1.0.20 - 20180726 - added transmission TIMESLOT fields
#   v1.0.21 - 20190314 - add CPE_LOOPBACK_PINGABLE field that lists all loopback IPs responding to ping
#   v1.0.22 - 20190419 - add TACACS_REALM field, provisioned manually
#   v1.0.23 - 20190426 - add TRUVIEW_SITE_AUTOGEN field, generated automatically for Truview customers
#   v1.0.24 - 20190531 - add TRUVIEW_SITE_DESCR_AUTOGEN field, generated automatically for Truview customers
#   v1.0.25 - 20200911 - add SNMP discovery info, prepended by DISC_
#   v1.0.26 - 20210701 - add VT remarks
#   v1.0.27 - 20211109 - add NPM info
#   v1.0.28 - 20230609 - add product info fields

import os
import re
import sys
import socket
import struct
import logging

VERSION = "1.0.27"

VERBOSE = eval(os.environ.get("VERBOSE", "True").title())
SCRIPTDIR = os.environ.get("SCRIPTDIR", ".")
LOGFOLDER = os.environ.get("LOGDIR", ".")
COLLECTIONSDIR = os.environ.get("COLLECTIONSDIR", "../collections")
LOGFILE = os.path.join(LOGFOLDER, "findhost-consolidator.log")
# files in this folder will be parsed
NISFOLDER = os.environ.get("NISFOLDER", '/opt/SCRIPTS/findhost/data/frontix')
TEMPFOLDER = os.environ.get("TEMPFOLDER", "tmp")
# temporary output file is stored here
TEMPDATA = os.path.join(TEMPFOLDER, "nis_summary.csv")
# folder where the 2 findhost files will be saved:  filtered.findhost.source.csv + findhost.source.csv
OUTPUTDIR = os.environ.get(
    "CONSOLIDATOR_OUTPUT_FOLDER", "/opt/SCRIPTS/findhost/output")
OUTPUTCSV = os.path.join(OUTPUTDIR, "findhost.source.csv")
OUTPUTCSVFILTERED = os.path.join(OUTPUTDIR, "findhost.source.filtered.csv")
PINGFILE = "/opt/SCRIPTS/network-discovery/hosts/hosts"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGFILE)
    ]
)

logger = logging.getLogger("findhost-consolidator")

if VERBOSE:
    logger.addHandler(logging.StreamHandler(sys.stdout))

# SERVICEID MUST BE THE FIRST COLUMN !!!!
KEEPCOLS = ['SERVICEID',  # VT reference
            'GSID',  # GSID
            'LOOKUP_VALUE',  # NIS STATUS: Completed, Inactive
            'SERVICETYPE',  # service type: IP-VPN, Corporate Internet
            'ACCOUNTNAME',
            # find related VT's (or keys in general if another first column is used) based on ACCOUNTID + SITE_ID
            'RELATED_KEYS',
            'MOBISTARREFERENCE',
            'ACCOUNTID',
            'SALESDEPARTMENT',  # for active MES sites the value: 312,  for old KPN sites empty
            'DESCRIPTION',
            'MACDREMARK',
            'OBS_CE_MAN_LOOPBACK',  # loopback ip for OBS connected L3 VPN routers
            'CASEID',
            'SERVICE_TYPE_2',  # ADD/DELETE/...
            'PM_FULLNAME',  # Project manager name
            'PM_EMAILADDRESS',  # Project manager email address
            'ACCOUNTMANAGER',
            'SITE_ID',
            'SITE_SITENAME',
            'SITE_STREET',
            'SITE_HOUSENUMBER',
            'SITE_ZIPCODE',
            'SITE_CITY',
            'SITE_COUNTRY',
            'EQUIPMENT_SUBNET',  # for CPE components this is the modem mgmt subnet
            'EQUIPMENT_IPADDRESS',  # for CPE components this is the modem mgmt ip address
            # for CPE components this is the modem end of ip address range
            'EQUIPMENT_IPADDRESS_END',
            'EQUIPMENTSUPPLIER',
            'SERVICESTATUS',
            'EQUIPMENT_STATUS',
            'EQUIPMENTDESCRIPTION',
            'SERVICE_CREATED',
            'EQUIPMENTLABEL',
            'LINEPROFILE',
            'VLANPROFILE',
            'COMPONENTDESCRIPTION',
            'COMPONENT_TYPE',
            'COMPONENT_CREATED',
            'COMPONENT_VPN_NAME',  # VPN name as described in Frontix
            'ROUTERTYPE',
            'COMPONENTID',
            'SEGMENT',
            'CIRCUIT_ID',
            'NETWORKELEMENT',
            'LEX',
            'DSL_SERVICE',
            'COMPONENT_STATUS',
            'HOSTNAME',
            'LABEL',
            'VCI',
            'VLAN',
            'VPI',
            'BANDWIDTH',
            'PROJECTID',
            'CIRCUIT_CAPACITY',
            'PORTLABEL_A',
            'PORTLABEL_B',
            'STATUS_CIRCUIT',
            'CES_SVLAN_ID',  # new carrier ethernet SVLAN id
            'TIMESLOT',
            'TIMESLOT_B',
            'TDI_ID',
            'PORT_UNI',
            'STATUS_TDI',
            'CAPACITY',
            'COPPERLINEID',
            'ORDERTYPE',
            'MOBICEMAINIPMASK',
            'BASICPROFILE',
            'MAXUPSTREAM',
            'CONFIGURATION',
            'SERVICE',  # VDSL SERVICE TYPE "VDSL internet High Upstream MES"
            'MOBICEMAINIPADDRESS',
            'LINESHARING',
            'MAXDOWNSTREAM',
            'MANAGEMENTIP',  # Unmanaged ethernet VPN ip address IP over Mobistar
            'GATEWAYIP',  # Unmanaged ethernet VPN gateway IP over Mobistar
            'DSID',
            'MOBIMAINCUSTOMERLAN',
            'ORDERSTATUS',
            'P0_VLANID',
            'MOBICUSTOMERLOOPBACK',
            'ISP',
            'LASTMODIFICATIONDATE',
            'L2PE',
            'ORDERID',
            'ORDERREF',
            'P0_DSLAMID',
            'NEWLINE',
            'NAME',
            'P0_PORTID',
            'SUBNET',
            'CPE_FIRSTSEEN',
            'CPE_LASTSEEN',
            'CPE_HOSTNAME',
            'CPE_HOSTNAME_GUESS',
            'CPE_LOOPBACK',
            'CPE_LOOPBACK_PINGABLE',  # all ip addresses responding to ping
            'CPE_VENDOR',
            'CPE_WAN_IP',
            'CPE_WAN_SUBNET',
            'CPE_WAN_MASK',
            'CPE_MULTIVRF',
            'CPE_MANAGED',
            'CPE_WAN_INT',
            'CPE_PING',
            'CPE_TELNET',
            'CPE_QOS_IN',  # QOS policy-map configured in CPE
            'CPE_QOS_OUT',  # QOS policy-map configured in CPE
            'CPE_STANDBY_IP',
            'CPE_SW_VERSION',
            'CPE_SW_TYPE',
            'CPE_CHASSIS',
            'CPE_SERIAL',
            'CPE_TRANSMISSION',
            'CPE_INFO_FROM',
            'CPE_INTF_FUNCTION',
            'CPE_INTF_ALL_VT',  # all VT's found on the CPE + PE interface
            # parsed from QOS description in CPE, ex: *** AUTO UPDATED ON: 2015-07-15 - LP:LP701 (20/2) ***
            'CPE_VDSL_LP',  # the configured VDSL lineprofile
            'CPE_VDSL_BW_DOWNLOAD',  # the configured VDSL download bandwidth
            'CPE_VDSL_BW_UPLOAD',  # the configured VDSL upload bandwidth
            # date when the VDSL line profile was updated automatically by script
            'CPE_VDSL_LP_UPDATED',
            'CPE_VDSL_LP_MESSAGE',  # status message related to the last VDSL QOS update
            'CPE_APN',  # APN info found in CPE config
            'CPE_CELLULAR_IMEI',  # IMEI info found in CPE config
            'CPE_CELLULAR_IMSI',  # IMSI info found in CPE config
            'CPE_CELLULAR_CELLID',  # CELLID info found in CPE config
            'CPE_CELLULAR_OPERATOR',  # OPERATOR info found in CPE config
            'PE_VAR_QOS_IN',  # QOS policy-map configured in PE
            'PE_VAR_QOS_OUT',  # QOS poolicy-map configured in PE
            'PE_VAR_WAN_IP',
            'PE_VAR',
            'PE_VAR_INT',
            'PE_VAR_INT_STATUS',
            'PE_VAR_INT_DESCR',
            'PE_VAR_REMOTE_AS',
            'VRF',
            'TACACS_REALM',  # generated manually based on VRF
            'LL_ID',
            'LL_LINEID',
            'LL_STATUS',
            'LL_BW',
            'LL_IPADDRESS',
            'LL_LINETYPE',
            'LL_DSID',
            'LL_BOFID',
            'LL_OLO',
            'LL_CONTRACTENDDATE',
            'LL_CONTRACTSTARTDATE',
            'LL_CONNECTORTYPE_A',
            'LL_ZONE',
            'LL_SITEID_A',
            'LL_LOCATIONNAME_A',
            'LL_LOCATIONADDRESS_A',
            'LL_LOCATIONNAME_B',
            'LL_LOCATIONADDRESS_B',
            'LL_CONNECTORTYPE_B',
            'LL_REQUESTEDDATE',
            'LL_RFSACTUALDATE',
            'LL_CANCELDATE',
            'LL_ISHALFLINK',
            'LL_ISMULTILINK',
            'LL_SALESDEPT',
            # TROPS SVLAN
            'SVLAN_CONNECTIONID',
            'SVLAN_STATUS',
            'SVLAN_LABEL',
            'SVLAN_PRT',
            'SVLAN_CAPACITY',
            'SVLAN_TYPE',
            'SVLAN_PROJECTID_A',
            'SVLAN_PROJECTID_B',
            'SVLAN_LABEL_SHORT',
            # TROPS VIRTUAL SWITCH
            'VSWITCH_CONNECTIONID',
            'VSWITCH_STATUS',
            'VSWITCH_LABEL',
            'VSWITCH_PRT',
            'VSWITCH_CAPACITY',
            'VSWITCH_PROJECTID_A',
            'VSWITCH_PROJECTID_B',
            'VSWITCH_LABEL_SHORT',
            # Groundwork stats
            'GW_MONTH',
            'GW_AVGIN_BITS',
            'GW_USAGEIN_PCT',
            'GW_POTIN_PCT',
            'GW_TBWIN_MB',
            'GW_95PIN_BITS',
            'GW_AVGOUT_BITS',
            'GW_USAGEOUT_PCT',
            'GW_POTOUT_PCT',
            'GW_TBWOUT_MB',
            'GW_95POUT_BITS',
            'GW_BANDWIDTH',
            # CHECKVT audit stats
            'AUDIT_DATE',
            'AUDIT_RESULT',
            'AUDIT_CONFIG',
            'AUDIT_CUSTOMERCONFIG',
            'AUDIT_INTERFACES',
            'AUDIT_QOS',
            'AUDIT_BGP',
            'AUDIT_STATICROUTES',
            'AUDIT_NETFLOW',
            'TACACS_CUST_NASID',  # CUSTOMER TACACS ID
            'TACACS_CUST_REALM',  # CUSTOMER TACACS REALM
            'TACACS_CUST_TACGROUP',  # CUSTOMER TACACS GROUP
            'VDSL_BW_UPSTREAM',  # VDSL upstream bw for single VT
            'VDSL_BW_DOWNSTREAM',  # VDSL downstream bw for single VT
            'VDSL_SVLAN_ID',  # VDSL SVLAN ID
            'VDSL_SVLAN',  # VDSL SVLAN  1234:1234
            'VDSL_BAS',  # VDSL BAS router
            'VDSL_SVLAN_PURPOSE',  # PXS SVLAN purpose: data, voice
            'VDSL_SVLAN_QOS_PBIT',  # PXS SVLAN QOS BIT
            'VDSL_SVLAN_BW_MBPS',  # PXS bandwidth of SVLAN
            'VDSL_SVLAN_NBR_CUSTOMERS',  # PXS nbr of customers for SVLAN
            'VDSL_SVLAN_BW_PER_CUSTOMER',  # PXS avg BW per customer for SVLAN
            'VDSL_SVLAN_PCT_OVERBOOKING',  # PCT overbooking for PXS SVLAN
            'VDSL_SVLAN_NAME',  # PXS SVLAN name
            'VDSL_SVLAN_TRUNK',  # PXS SVLAN trunk name
            'VDSL_LAG',  # PXS LAG name
            'VDSL_CPEUSERNAME',  # VDSL MODEM USERNAME
            'VDSL_CPEPASSWORD',  # VDSL MODEM PASSWORD
            # 'CPE_SW_FEATURE_SET', NOT USED
            # 'SERTYPE', =SERVICETYPE
            # 'STATUS', NOT USED
            # 'SITECODE', NOT USED
            # 'LASTCHANGEDBY', NOT USED
            # 'LOCATIONNAME', NOT USED
            # 'PARTCODE', NOT USED
            # 'LOCATIONTYPE', NOT USED
            # 'LASTCHANGED', NOT USED
            # 'LOOPBACKIPADDRESS', NOT USED
            # 'APG_PROJECTMANAGER', NOT USED
            # 'BANDWIDTH_REQUESTED', NOT USED
            # 'STATUS_SERVICEID', = LOOKUP_VALUE
            # 'P5_VLANID', NOT USED
            # 'SERVICEREF', = ORDERREF
            # 'PROJECTMANAGER', = FULLNAME
            # 'SERVICE2TYPE', = SERTYPE
            # 'VT_ID', = SERVICEID
            'VDSL2TYPE',  # manipulated from SERVICE column => "VDSL Dedicated": "VDSL2_DEDICATED",  "VDSL Internet": "VDSL2_SHARED",  should be last column because it may be changed depending on other column values
            # column indicating the CPE PARTNER (ex. OBS, INTEROUTE, FT, T2, ...),  should be last column because it may be changed depending on other column values
            'PARTNER',
            # NPM (TRUVIEW)
            # column of auto-generated site name to be used in Truview, only for truview customers
            'TRUVIEW_SITE_AUTOGEN',
            # column of auto-generated site name to be used in Truview, only for truview customers
            'TRUVIEW_SITE_DESCR_AUTOGEN',
            'NPM_LOGIN',  # login account for NPM
            'NPM_PSW',   # password for NPM
            'NPM_IP',    # ip address for NPM
            'NPM_BW_DOWN_MB',  # SITE download speed in MB, overrides SNMP discovery
            'NPM_BW_UP_MB',  # SITE upload speed in MB, overrides SNMP discovery
            'NPM_SITE_DESCR',  # SITE description, overrides the AUTOGEN SITE DESCR
            'NPM_SITE_NAME',  # SITE name, overrids AUTOGEN SITE NAME
            'NPM_DOMAIN_NAME',  # NPM DOMAIN NAME (HARDCODED)
            'NPM_DOMAIN_ID',  # NPM DOMAIN ID (HARDCODED)
            # info discovered by network-discovery and router-config-parser, SNMP discovered so RELIABLE
            'DISC_MGMT_IP',     # discovered management ip
            'DISC_DOMAINNAME',  # dns domain name
            'DISC_COMMUNITY',  # snmp community that was used to connect
            'DISC_SYSOBJID',   # system sysobjid
            'DISC_VENDOR',     # mapping of SYSOBJID to vendor
            'DISC_HWTYPE',     # mapping of SYSOBJID to hardware type
            'DISC_FUNCTION',   # mapping of IP to function
            'DISC_SERVICE',    # mapping of IP to service
            'NAPALM_DRIVER',   # mapping of SYSOBJID to driver
            # based on nmap (either 22 for ssh or 23 for telnet)
            'DISC_PROTOCOL',
            # VT remarks
            'REMARKS_ACCOUNT',
            'REMARKS_CONTRACT',
            'REMARKS_PROVISION',
            'REMARKS_SERVICE',
            # PRODUCT info tab tracker
            'PINFO_CONFIGURATION', 
            'PINFO_COMMERCIAL_COS', 
            'PINFO_REMARKS_ACCOUNT', 
            'PINFO_REMARKS_CONTRACT', 
            'PINFO_REMARKS_PROVISION', 
            'PINFO_REMARKS_SERVICE', 
            'PINFO_TOPOLOGY',
            'PINFO_TYPE_OF_QOS', 
            'PINFO_TAGGING_OPTION', 
            'PINFO_SITE_A_CVLAN', 
            'PINFO_SITE_A_SVLAN', 
            'PINFO_SITE_B_CVLAN', 
            'PINFO_SITE_B_SVLAN',
            ]

# ignore these files if they were found
IGNORE_FILES = ['dump_query_2_ts_last.csv', 'dump_query_15_ts_last.csv']
# static files in other locations can be added here
OTHER_FILES = {
    # '/opt/SCRIPTS/findhost/output/cpe_vendor.csv': ';' ,
    # '/opt/SCRIPTS/findhost/output/cpelist.csv': '|',
    # '/opt/SCRIPTS/findhost/output/findhost_new.csv': '|',
    os.path.join(COLLECTIONSDIR, "network-config-parser/router-parser.csv"): "|",
    os.path.join(COLLECTIONSDIR, 'proximus/dsid.csv'): ';',
    os.path.join(COLLECTIONSDIR, 'groundwork/groundwork.900008487.csv'): ';',
    os.path.join(COLLECTIONSDIR, 'cpe_config_audit/cpe_config_audit.csv'): ';',
    os.path.join(COLLECTIONSDIR, 'tacacs/tacacs_customer_cpe.csv'): ',',
    os.path.join(COLLECTIONSDIR, 'output/vdsl_lex_vlan.csv'): ';',
    os.path.join(COLLECTIONSDIR, 'data/vdsl_qos_upgrade/report.txt'): ',',
}

# columns stored in here are checked for duplicate entries, example duplicate loopback or WAN subnet
DUPLICATES = {
    # make sure we don't have duplicate WAN IP's unless it's VDSL shared vlan on PE "emlp"
    'CPE_WAN_SUBNET': {},
    'CPE_LOOPBACK': {},  # cpe loopback should be unique
    'CPE_HOSTNAME': {},  # hostnames should be unique unless it's multi-VRF
}

# store related VTs (or other key) here. Format = "ACCOUNTID-SITE_ID": "key1@@key2@@..."
RELATEDKEYS = {
}

DELIM = ";"  # default input + output delimiter, input delim can be overridden by adding them to the OTHER_FILES dict
COLDELIM = '@@'  # the delimiter used when joining fields for the same column


# VRF to TACACS_REALM MAPPING
VRF_REALM_MAP = {
    "IRISNET.*": "IRISNET",
    "ADECCO.*": "ADECCO",
    "THOMASCOOK.*": "THOMASCOOK",
    "SDWOR.*": "SDWORX",
    "SDVZW.*": "SDWORX",
    "ACCOR_.*": "ACCOR_0001",
    "AGINSURANCE.*": "AGINSURANCE_0001",
    "MATEXI.*": "MATEXI",
}

# list of truview customers
TRUVIEW_ACCOUNTS = ["900154616", "900154609",
                    "900154648", "900084334", "900136919", "900154648"]
TRUVIEW_SITE_NAMES = {
    "DEFAULT": {"delim": " - ", "columns": ["SITE_ID", "SITE_SITENAME"]},
    "900154616": {"delim": " ", "columns": ["SITE_CITY", "SITE_STREET"]},
    "900136919": {"delim": " ", "columns": ["SITE_CITY", "SITE_STREET"]},
    "900084334": {"delim": " ", "columns": ["SITE_CITY", "SITE_STREET"]},
    "900154648": {"delim": " ", "columns": ["SITE_CITY", "SITE_STREET"]},
}

# NPM ACCOUNT TO DOMAIN HARDCODE MAPPING
NPM_ACCOUNT_TO_DOMAIN_MAP = {
    "900084334": {"domainId": 11, "domainName": "Adecco Domain"},
    "900136919": {"domainId": 12, "domainName": "Select Human Resources Domain"},
    "900154553": {"domainId": 13, "domainName": "Impact"},
    "900154609": {"domainId": 14, "domainName": "[OBE - DEMO]"},  # OrangeShop
    "900154616": {"domainId": 16, "domainName": "Matexi Group"},
    "900087514": {"domainId": 17, "domainName": "Irisnet"},
    "900154648": {"domainId": 18, "domainName": "MEDIMARKET"},
}


# list of IP addresses known in the network that respond to ping
# this is the output of the network-discovery script
# /opt/SCRIPTS/network-discovery/discover.sh
PINGABLE_IP = []


# find all files in the NISFOLDER and return dict of file: delimiter
def get_all_files(delim=";"):
    files = {}
    for file in os.listdir(NISFOLDER):
        if file.startswith("dump_query") and not file in IGNORE_FILES:
            files["{}/{}".format(NISFOLDER, file)] = delim
    return files


# populate PINGABLE_IP with the ip addresses found in PINGFILE
def get_pingable_ip():
    if not os.path.isfile(PINGFILE):
        return

    F = open(PINGFILE, "r")
    lines = F.readlines()
    F.close()
    for line in lines:
        PINGABLE_IP.append(line.split(":")[0])


# convert IP address to integer
def ip2int(addr):
    try:
        ip = struct.unpack("!I", socket.inet_aton(str(addr)))[0]
    except:
        ip = addr
    return ip

# convert integer to IP address


def int2ip(addr):
    if not addr:
        return
    logger.debug("Converting integer to IP ({})".format(addr))
    try:
        ip = socket.inet_ntoa(struct.pack("!I", int(addr)))
        logger.debug(
            "Successfully converted integer to IP ({}: {})".format(addr, ip))
    except:
        ip = addr
        logger.error("ERROR Converting integer to IP ({})".format(addr))
    return ip


# sanitize fields, this is used when reading all the input files
# remove unwanted characters:
# - leading + trailing spaces
# - reduce multiple spaces to 1
# remove output delimiter
def sanitize(field):
    field = field.strip()
    field = ' '.join(field.split())
    field = field.replace(DELIM, "-")
    field = field.replace("\"", "'")
    return field


# try to find related VTs (or other keys)
# currently based on ACCOUNTID-SITE_ID
def set_related_keys(mykey, record):
    # only proceed if the relation key values exist
    if record['ACCOUNTID'] and record['SITE_ID']:
        relationkey = "{}-{}".format(record['ACCOUNTID'], record['SITE_ID'])
        if relationkey in RELATEDKEYS:
            if not mykey in RELATEDKEYS[relationkey]:
                RELATEDKEYS[relationkey] = COLDELIM.join(
                    (RELATEDKEYS[relationkey], mykey))
        else:
            RELATEDKEYS[relationkey] = mykey


# send STDERR alert based on some conditions
# this should be called just before generating the permutaded output file
def alert(vt, field, column='', record=''):
    # check that a single VT only has 1 status
    # make sure the lookup value exists for all MES services (exclude old KPN services)
    if column == 'LOOKUP_VALUE':
        if '@@' in field:
            logger.error(
                "multiple LOOKUP_VALUE status found for {} -> {}".format(vt, field))
        if field == '' and record.get('SALESDEPARTMENT', "") != "":
            logger.error(
                "no LOOKUPVALUE (Inactive, Completed, ..) found for {}".format(vt))
    # each VT should have a SERVICETYPE defined
    if column == 'SERVICETYPE':
        if field == '':
            logger.error(
                "no SERVICETYPE (=IP-VPN, CI, ..) found for {}".format(vt))
    # OBS loopback IP's have to be unique and in format 999.999.999.999-32
    if column == 'OBS_CE_MAN_LOOPBACK' and not field == '':
        m = re.match('[0-9]{3}\.[0-9]{3}\.[0-9]{3}\.[0-9]{3}\-32', field)
        if not m:
            logger.error(
                "OBS_CE_MAN_LOOPBACK is not correct for {} -> {}".format(vt, field))
    # report SALESDEPARTMENT '' and SERVICESTATUS='Completed' or 'Ongoing'
    if column == 'SALESDEPARTMENT' and field == '' and ('completed' in record['LOOKUP_VALUE'] or 'Ongoing' in record['LOOKUP_VALUE']):
        logger.warning(
            "SALESDEPARTMENT is not set to 312 but LOOKUP_VALUE is Completed or Ongoing for {}".format(vt))
    # multiple VRF should not exist
    if column == 'VRF' and '@@' in field:
        logger.error(
            "same VT is used for multiple VRF -> {}: {}".format(vt, field))
    # same VT is used in different PE interfaces
    if column == 'PE_VAR_INT' and '@@' in field:
        logger.error(
            "same VT is configured on multiple interfaces -> {}: {}".format(vt, field))
    # same VT is used on different PE devices
    if column == 'PE_VAR' and '@@' in field:
        logger.warning(
            "same VT is configured on multiple VAR routers -> {}: {}".format(vt, field))
    # check for duplicates
    if field and column in DUPLICATES and field in DUPLICATES[column] and DUPLICATES[column][field] > 0 and record['CPE_MULTIVRF'] != 'multivrf':
        logger.error(
            "DUPLICATE entry found for column {} -> {}: {}".format(column, vt, field))


# do some field calculations or manipulations based on field value or column name:
# field = the field value
# column = column name
def customfields(field, column='', record=None):
    # if not field:
    #    return field
    newfield = field
    # remove "Dumb and Dumber" + N/A values from column EQUIPMENTSUPPLIER
    if column == 'EQUIPMENTSUPPLIER':
        if 'Dumb and Dumber'.lower() in field.lower():
            newfield = ''
        elif 'N/A'.lower() in field.lower():
            newfield = ''
    elif column == 'GATEWAYIP':
        if field.startswith('...'):
            newfield = ''
    elif column == 'MANAGEMENTIP':
        if field.startswith('...'):
            newfield = ''

    # update the DUPLICATES tables
    elif column in DUPLICATES:
        if field in DUPLICATES[column]:
            DUPLICATES[column][field] = DUPLICATES[column][field] + 1
        else:
            DUPLICATES[column][field] = 0

    # update the RELATED_KEYS field based on value found in RELATEDKEYS table
    elif column == 'RELATED_KEYS':
        if record and record['ACCOUNTID'] and record['SITE_ID']:
            relationkey = "{}-{}".format(record['ACCOUNTID'],
                                         record['SITE_ID'])
            if relationkey in RELATEDKEYS:
                newfield = RELATEDKEYS[relationkey]

    # update the VDSL2TYPE field based on SERVICE
    # ^VDSL internet => becomes VDSL2_SHARED
    # ^VDSL dedicated => becomes VDSL2_DEDICATED
    elif column == 'SERVICE':
        if record and 'VDSL2TYPE' in record:
            if field.startswith('VDSL internet'):
                record['VDSL2TYPE'] = "VDSL2_SHARED"
            elif field.startswith('VDSL dedicated'):
                record['VDSL2TYPE'] = "VDSL2_DEDICATED"

    # update the PARTNER field: add external partners
    # OBS_CE_MAN_LOOPBACK => if defined then parnter = OBS
    elif column == 'OBS_CE_MAN_LOOPBACK':
        if record and not field == "":
            record['PARTNER'] = 'OBS'

    # Create a TACACS_REALM field based on the VRF and VRF_REALM_MAP
    elif column == 'VRF':
        for vrfmapkey in VRF_REALM_MAP:
            m = re.match(vrfmapkey, field)
            if m:
                record['TACACS_REALM'] = VRF_REALM_MAP[vrfmapkey]
                break

    # Generate the Truview site based on SITE_ID + SITE_NAME (132 chars)
    # Add NPM domainid and domain names
    elif column == 'ACCOUNTID' and field in TRUVIEW_ACCOUNTS:
        truview_site_name = []
        tv_site_format = TRUVIEW_SITE_NAMES.get(
            field, TRUVIEW_SITE_NAMES["DEFAULT"])
        tv_columns = tv_site_format["columns"]
        tv_delim = tv_site_format["delim"]
        for tv_col in tv_columns:
            normalized_column = re.sub(
                "[\'\"]", " ", str(record.get(tv_col, "")))
            truview_site_name.append(normalized_column.strip())
        record['TRUVIEW_SITE_AUTOGEN'] = tv_delim.join(
            truview_site_name).lower().capitalize()[0:32]

        tv_site_description = (
            "{} - {}".format(record.get("SITE_ID", ""), record.get("SITE_SITENAME")))[0:132]
        record['TRUVIEW_SITE_DESCR_AUTOGEN'] = tv_site_description

        if field in NPM_ACCOUNT_TO_DOMAIN_MAP:
            record['NPM_DOMAIN_NAME'] = NPM_ACCOUNT_TO_DOMAIN_MAP[field]["domainName"]
            record['NPM_DOMAIN_ID'] = str(
                NPM_ACCOUNT_TO_DOMAIN_MAP[field]["domainId"])

    # update the PARTNER field; assign OBS if the ESU port = 00350-ESU01-002/00-0/00-03/01
    elif column == 'LABEL':
        if record and '00350-ESU01-002/00-0/00-03/01' in field:
            record['PARTNER'] = 'OBS'

    # update the PARTNER field; assign INTEROUTE if LL_OLO = Interoute
    elif column == 'LL_OLO':
        if record and 'Interoute' in field:
            record['PARTNER'] = 'INTEROUTE'
        # print "***** field: %s" % field

    # convert int to ip for EQUIPMENT_SUBNET + EQUIPMENT_IPADDRESS + EQUIPMENT_IPADDRESS_END
    elif field and column in ('EQUIPMENT_SUBNET', 'EQUIPMENT_IPADDRESS', 'EQUIPMENT_IPADDRESS_END'):
        #record[column] = int2ip(field)
        newfield = int2ip(field)

    # calculate LEX From P0_DSLAMID : .([0-9]{2}[a-zA-Z]{3}).*
    # map some lex locations to different values
    elif column == 'LEX':
        lexmap = {'02EUR': '02MAR', '02FOR': '02DRO', '02NOH': '02MUT',
                  '02NOR': '02MAR', '51MUE': '51MEU', '91DOS': '91OOS'}
        if record['P0_DSLAMID']:
            m = re.match('.([0-9]{2}[a-zA-Z]{3}).*', record['P0_DSLAMID'])
            if m:
                lex = m.groups()[0]
                if lex in lexmap:
                    newfield = lexmap[lex]
                else:
                    newfield = lex

    # check if the pingable_ips are really pingable
    if column == 'CPE_LOOPBACK':
        delim = ","
        pingable = []
        field = field.replace("@@", ",")
        ips = field.split(",")
        # print(ips)
        for ip in ips:
            if ip in PINGABLE_IP:
                # print(ip)
                pingable.append(ip)
        record['CPE_LOOPBACK_PINGABLE'] = delim.join(pingable)

    return newfield


# map a column of the input file to a new column matching a column in KEEPCOLS
# this is to make sure that columns are used for an input file, even though they don't have the same column names as in KEEPCOLS
def rename_column_name(header):
    newheader = header
    mapping = {
        'STATUS_SERVICEID': 'LOOKUP_VALUE',
        'SERTYPE': 'SERVICETYPE',
        'SERVICESTATUS': 'LOOKUP_VALUE',
        'VT': 'SERVICEID',
        'LOOPBACK': 'CPE_LOOPBACK',
        'VENDOR': 'CPE_VENDOR',
        'CE_HOSTNAME': 'CPE_HOSTNAME',
        'CE_HOSTNAME_GUESS': 'CPE_HOSTNAME_GUESS',
        'CE_LOOPBACK': 'CPE_LOOPBACK',
        'PE': 'PE_VAR',
        'PE_INT': 'PE_VAR_INT',
        'PE_INT_STATUS': 'PE_VAR_INT_STATUS',
        'PE_DESCR': 'PE_VAR_INT_DESCR',
        'CE_IP': 'CPE_WAN_IP',
        'PE_IP': 'PE_VAR_WAN_IP',
        'PTP_SUBNET': 'CPE_WAN_SUBNET',
        'PTP_MASK': 'CPE_WAN_MASK',
        'MULTIVRF': 'CPE_MULTIVRF',
        'MANAGED': 'CPE_MANAGED',
        'CE_INT': 'CPE_WAN_INT',
        'PING': 'CPE_PING',
        'TELNET': 'CPE_TELNET',
        'CE_QOS_IN': 'CPE_QOS_IN',
        'CE_QOS_OUT': 'CPE_QOS_OUT',
        'PE_QOS_IN': 'PE_VAR_QOS_IN',
        'PE_QOS_OUT': 'PE_VAR_QOS_OUT',
        'PE_REMOTE_AS': 'PE_VAR_REMOTE_AS',
        'STANDBY_IP': 'CPE_STANDBY_IP', 'SW_VERSION': 'CPE_SW_VERSION', 'SW_TYPE': 'CPE_SW_TYPE',
        'SW_FEATURE_SET': 'CPE_SW_FEATURE_SET',
        'CHASSIS': 'CPE_CHASSIS',
        'SERIAL': 'CPE_SERIAL',
        'SVLAN_ID': 'VDSL_SVLAN_ID',
        'SVLAN': 'VDSL_SVLAN',
        'BAS': 'VDSL_BAS',
        'SVLAN_PURPOSE': 'VDSL_SVLAN_PURPOSE',
        'SVLAN_QOS_PBIT': 'VDSL_SVLAN_QOS_PBIT',
        'SVLAN_BW_MBPS': 'VDSL_SVLAN_BW_MBPS',
        'SVLAN_NBR_CUSTOMERS': 'VDSL_SVLAN_NBR_CUSTOMERS',
        'SVLAN_BW_PER_CUSTOMER': 'VDSL_SVLAN_BW_PER_CUSTOMER',
        'SVLAN_PCT_OVERBOOKING': 'VDSL_SVLAN_PCT_OVERBOOKING',
        'SVLAN_NAME': 'VDSL_SVLAN_NAME',
        'SVLAN_TRUNK': 'VDSL_SVLAN_TRUNK',
        'LAG': 'VDSL_LAG',
        'CPEUSERNAME': 'VDSL_CPEUSERNAME',
        'CPEPASSWORD': 'VDSL_CPEPASSWORD',
        'EQ_SUBNET_NUMBER': 'EQUIPMENT_SUBNET',
        'EQ_IPADDRESS_NUMBER': 'EQUIPMENT_IPADDRESS',
        'EQ_IPADDRESS_END_NUMBER': 'EQUIPMENT_IPADDRESS_END',
        'CPE_COMPONENT_TYPE': 'COMPONENT_TYPE',
        'VPN_NAME': 'COMPONENT_VPN_NAME',
    }

    for key in mapping:
        if header == key:
            newheader = mapping[key]
            break

    return newheader


# parse the different input files,  each line is appended to a temporary output file but using the column structure as
# defined by KEEPCOLS
def parse(sfile, dfile, keepcols, delim=";", outdelim=";"):
    CH = {}  # column headers
    firstline = True
    ifile = open(sfile)
    ofile = open(dfile, 'a')
    for line in ifile:
        line = line.rstrip()
        lcols = line.split(delim)
        # we make a hash of the column names
        if firstline:
            i = 0
            for c in lcols:
                # check if the column names of the input file need to be renamed
                # only columns matching the names in KEEPCOLS will be kept
                colname = rename_column_name(c.upper())
                CH[colname] = i
                i = i + 1
            firstline = False
            # print CH
        else:
            newline = []
            if not len(CH) == len(lcols):
                logger.error("line does not match the expected number of {} columns ({}) [{}]".format(
                    len(CH), lcols, sfile))
            else:
                # only columns matching the names in KEEPCOLS will be stored
                for k in keepcols:
                    if k.upper() in CH:
                        try:
                            # sanitize the fields we want to keep
                            newline.append(sanitize(lcols[CH[k.upper()]]))
                        except IndexError as e:
                            # print(e)
                            logger.critical(e)
                            continue
                    else:
                        newline.append('')
                # write to the temporary output file IF the key is not empty
                # if keepcols[0] in CH and not newline[CH[keepcols[0]]] == "":
                ofile.write("{}\n".format(outdelim.join(newline)))
    ifile.close()
    ofile.close()


# apply a filter and see if the line needs to be written to the filtered output file
# current filter:
# - key must exist (always the case)
# - the LOOKUPVALUE must be "completed" or "ongoing"
def passfilter(mykey, record):
    rc = True
    if not mykey:
        rc = False
    #if not (record['LOOKUP_VALUE'].upper() == 'COMPLETED' or record['LOOKUP_VALUE'].upper() == 'ONGOING'): rc = False
    if not (record['LOOKUP_VALUE'].upper().find('COMPLETED') >= 0 or record['LOOKUP_VALUE'].upper().find('ONGOING') >= 0):
        rc = False
    return rc


# read the temporary input file and merge all lines
# the first column in KEEPCOLS is used as unique key,  by default this will be the VT reference
# the result will be a single file with 1 line per unique key (VT)
# sfile = input file generated by the parse function = file with columns matching KEEPCOLS
# dfile = generated output "permutated" file with unique key (=col 0)
# filteredfile = generated output file, same as dfile but first a filter will be applied
def permute(sfile, dfile, filteredfile, keepcols):
    delim = ";"
    cons = {}  # consolidated info in hash
    firstline = True
    line0 = ''  # copy the first column names line from the original file
    CH = {}  # mapping of column names to index
    logger.debug("permute source:{}, destination:{}".format(sfile, dfile))
    ifile = open(sfile)  # input file
    for line in ifile:
        line = line.rstrip()
        lcols = line.split(delim)
        # pass if there is no unique key (=element 0 - usually VT)
        if lcols[0] == "":
            continue
        # make a mapping of the column index and the column name
        if firstline:
            line0 = line
            i = 0
            for c in lcols:
                CH[i] = c.upper()
                i = i + 1
            firstline = False
        else:
            i = 0
            # the unique key is the first column, usually VT,  we refer to vt in the script
            vt = lcols[0]
            # print vt
            for c in lcols:
                # initialize the new VT, make a new empty record for the unique key including all the expected columns found in KEEPCOLS
                if vt not in cons:
                    cons[vt] = {}
                    for k in keepcols:
                        cons[vt][k.upper()] = ''
                # ch = column header,  this is the current column we are looking at (matching KEEPCOLS)
                ch = CH[i]
                # from here the record will be filled
                # if the field is empty then just add it to the record
                # if the field is not empty but it already exists in the record with the same value then do nothing
                #print("vt:{}, ch:{}".format(vt, ch))
                if cons[vt][ch] == '':
                    cons[vt][ch] = c
                # if the element is not empty but it's not the same then there is a conflict, so different input files have different values
                # for the same column. In that case join the fields using @@ delimiter
                elif cons[vt][ch] != c:
                    if c is not '' and c not in cons[vt][ch]:
                        # report if there is a conflict for a column
                        #print("CONFLICT FOR VT: {} ({})".format(vt, c))
                        logger.error("CONFLICT FOR VT: {} ({})".format(vt, c))
                        cons[vt][ch] = "{}{}{}".format(
                            cons[vt][ch], COLDELIM, c)
                i = i + 1
            # keep track of related VTs
            set_related_keys(vt, cons[vt])
    ifile.close()

    # write everything to the output file
    ofile = open(dfile, 'w')  # output file
    # filtered output file, columns stay the same but lines can be filtered
    ffile = open(filteredfile, 'w')
    ofile.write("{}\n".format(line0))
    ffile.write("{}\n".format(line0))
    for vt in cons:
        newline = []
        for k in keepcols:
            # create the new line with the columns in the same order as defined in KEEPCOLS
            newline.append(customfields(
                cons[vt][k.upper()], k.upper(), cons[vt]))
            # check if we want to have an alert
            alert(vt, cons[vt][k.upper()], k.upper(), cons[vt])
        ofile.write("{}\n".format(delim.join(newline)))
        # check filter and write to output if it passes
        if passfilter(vt, cons[vt]):
            ffile.write("{}\n".format(delim.join(newline)))
    ofile.close()
    ffile.close()


get_pingable_ip()
allfiles = get_all_files()
#allfiles = {}
# append non-NIS files
for other_file in OTHER_FILES:
    if os.path.isfile(other_file):
        allfiles[other_file] = OTHER_FILES[other_file]
    else:
        # skip file - it doesn't exist
        logger.error("input file does not exist: {}".format(other_file))
# allfiles.update(OTHER_FILES)


# print allfiles

TEST = False
if not TEST:
    o = open(TEMPDATA, 'w')
    o.write("{}\n".format(";".join(KEEPCOLS)))
    o.close()
    for f in allfiles:
        parse(f, TEMPDATA, KEEPCOLS, delim=allfiles[f])

permute(TEMPDATA, OUTPUTCSV, OUTPUTCSVFILTERED, KEEPCOLS)
