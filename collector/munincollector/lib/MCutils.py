import copy
import cPickle
import os
import time
from stat import *
from subprocess import PIPE, Popen, STDOUT

os.environ['PATH'] = '/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin'

LogLevels = [
    'NoLogging',
    'Error',
    'Warning',
    'Info',
    'Debug',
    ]

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

# Return the domain from the specified full host name.
def GetDomain( host ):
    words = host.split('.')
    del words[0]
    return '.'.join(words)

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

def LastCacheUpdate (MCconfig):

    cache_file = open(MCconfig['PluginDir'] + '/config/.last_updated', 'r')
    last_cache_update = os.fstat(cache_file.fileno())[ST_CTIME]
    cache_file.close()

    return last_cache_update

def Logger( MCconfig, level, module, message ):
    if level <= MCconfig['LogLevel']:
        print module + ' (' + str('%05d' % os.getpid()) + ') ' + LogLevels[level] + ': ' + message

def MuninType( PluginConfig, key ):
# Return Munin rrd file modifier based on supplied plugin configuration parameters.
# Pluginconfig must provide the plugin configuration dictionary (PluginConfigs[hash][mgid]).
# key must provide a data source key (eg. the 'if_' plugin has 2 keys, 'up' and 'down').
    try:
        return(MuninValueTypes[PluginConfig[key + '.type']])
    except:
        return(MuninValueTypes['default'])

# Ensure the latest plugin configuration is loaded.
def ReloadPluginConfig (MCconfig, PluginConfigs):
    pickle_status = os.stat(MCconfig['PluginDir'] + '/pickles/PluginConfigs')
    if pickle_status.st_mtime > PluginConfigs['Timestamp']:
        Logger(MCconfig, 3, 'MCutils', 'Reloading the plugin configuration.')
        return True
    return False

# Ensure the latest time ranges are loaded.
def ReloadStatisticsActivity (MCconfig, StatisticsActivity):
    pickle_status = os.stat(MCconfig['PluginDir'] + '/pickles/StatisticsActivity')
    if pickle_status.st_mtime > StatisticsActivity['Timestamp']:
        Logger(MCconfig, 3, 'MCutils', 'Reloading the statistics activity.')
        return True
    return False

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
