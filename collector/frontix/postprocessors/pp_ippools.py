# Post Processor to manage IPPOOL information
# it converts integer IP addresses to regular IP addresses
# this just returns a json representation of:
#   { "column": "value", .. }

import json
from socket import inet_aton, inet_ntoa
from struct import unpack, pack
import re

def ip2long(ip_addr):
    return unpack("!L", inet_aton(ip_addr))[0]

def long2ip(i):
    return inet_ntoa(pack('!L', i))


# convert columns ending with _INT from integer to IP
def post_processor(cols, row):
    j = {}
    for idx, col in enumerate(cols):
        if "_INT" in str(col):
            ipv4 = long2ip(int(row[idx]))
            newcol = str(col).replace("_INT", "")
            j[newcol] = str(ipv4)
        else:
            if str(col) == "REMARKS":
                m = re.match(".*SIM Card number *= *(?P<SIM>[0-9]+).*MSISDN *= *(?P<MSISDN>[0-9]+).*PIN *= *(?P<PIN>[0-9]+).*PUK *= *(?P<PUK>[0-9]+).*", str(row[idx]))
                if m:
                    for k in m.groupdict():
                        j[k] = m.groupdict().get(k, "")
            j[str(col)] = str(row[idx])
    return json.dumps(j)

if __name__ == '__main__':
    cols = [ "REMARKS" ]
    row = [ "SIM Card number=7533331689367, MSISDN=490495436, IP=094.107.211.225, PIN=2832, PUK=84796962" ]
    print(post_processor(cols, row))

