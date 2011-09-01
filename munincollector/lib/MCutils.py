import os
from subprocess import PIPE, Popen, STDOUT

os.environ['PATH'] = '/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin'

MuninValueTypes = {
    'default': '-g',
    'COUNTER': '-c',
    'DERIVE': '-d',
    'GAUGE': '-g',
    'ABSOLUTE': '-a',
    'COMPUTE': '-e',
    }

# Scan AllowedDomains. Return 'True', if the specified host is within an allowed domain. Otherwise return 'False'.
def CheckAllowedDomains( AllowedDomains, HostAddr ):
    for ix in range(len(AllowedDomains)):
        if HostAddr >= AllowedDomains[ix][0] and HostAddr <= AllowedDomains[ix][1]:
            return True
    return False

# Convert the given IP string to an integer.
def IpToInt( Ip ):
    if ':' in Ip:
        partitions = Ip.partition('::')
        nibbles_1 =  partitions[0].split(':')
        if partitions[1] == '::':
            nibbles_2 =  partitions[2].split(':')
        nibble_bits = 16
        nibble_count = 8
    else:
        nibbles_1 = Ip.split('.')
        nibbles_2 = ()
        nibble_bits = 8
        nibble_count = 4

    host_addr_1 = 0
    for ix in range(nibble_count):
        host_addr_1 = host_addr_1 * (2 ** nibble_bits)
        if len(nibbles_1) > ix:
            host_addr_1 += StrToInt(nibbles_1[ix])

    host_addr_2 = 0
    for ix in range(len(nibbles_2)):
        host_addr_2 = host_addr_2 * (2 ** nibble_bits)
        host_addr_2 += StrToInt(nibbles_2[ix])

    return host_addr_1 + host_addr_2

def MuninType( PluginConfig, key ):
# Return Munin rrd file modifier based on supplied plugin configuration parameters.
# Pluginconfig must provide the plugin configuration dictionary (PluginConfigs[hash][mgid]).
# key must provide a data source key (eg. the 'if_' plugin has 2 keys, 'up' and 'down').
    try:
        return(MuninValueTypes[PluginConfig[key + '.type']])
    except:
        return(MuninValueTypes['default'])

def StrToFloat( str ):
# convert the given string to a floating point number.
    try:
        result = float(str)
    except ValueError:
        result = 0.0
    return result


def StrToInt( str ):
# convert the given string to an integer.
    try:
        result = int(str)
    except ValueError:
        result = 0
    return result
