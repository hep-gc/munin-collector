import os
import cPickle
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

def CachePluginConfig (MCconfig, PluginConfigs, hash):
    # Cache plugin config and datasource lists (stage 2): 
    #     PluginConfigs['config'][<hash>][<mgid>][<key>] = <value>
    hash_file = open(MCconfig['PluginDir'] + '/config/' + hash, 'r')
    lines = hash_file.readlines()
    hash_file.close()
    for line in lines:
        line = line.strip()
        if line == '' or line == '(nil)':
            continue

        key_value = line.split(' ', 1)

        if key_value[0] == 'pluginname' or key_value[0] == 'multigraph':
            mgid = key_value[1]
            continue

        if not PluginConfigs['config'].has_key(hash):
            PluginConfigs['config'][hash] = {}
            PluginConfigs['resolved'][hash] = False

        if not PluginConfigs['config'][hash].has_key(mgid):
            PluginConfigs['config'][hash][mgid] = {}

        PluginConfigs['config'][hash][mgid][key_value[0]] = key_value[1]

        # PluginConfigs['datasource'][hash][<mgid>] = [<ds>, <ds>, ...]
        words = key_value[0].split(".")
        if len(words) == 2:
            ds = words[0]
            if not PluginConfigs['datasource'].has_key(hash):
                PluginConfigs['datasource'][hash] = {}

            if not PluginConfigs['datasource'][hash].has_key(mgid):
                PluginConfigs['datasource'][hash][mgid] = []

            if not ds in PluginConfigs['datasource'][hash][mgid]:
                PluginConfigs['datasource'][hash][mgid] += [ds]

def CachePluginLink (MCconfig, PluginConfigs, host, plugin, hash):
    # Cache plugin links (stage 1): 
    #     PluginConfigs['links'][<host>][<plugin>] = <hash>
    if not PluginConfigs['links'].has_key(host):
        PluginConfigs['links'][host] = {}

    PluginConfigs['links'][host][plugin] = hash

def CachePluginXref(MCconfig, PluginConfigs):
    # Build domain and plugin trees and cross references used for graph selection (stage 3).
    for host in PluginConfigs['links']:
        domain = GetDomain(host)
        for plugin in PluginConfigs['links'][host]:
            for mgid in PluginConfigs['config'][PluginConfigs['links'][host][plugin]]:
                if not PluginConfigs['DomainTree'].has_key(domain):
                    PluginConfigs['DomainTree'][domain] = {}

                if not PluginConfigs['DomainTree'][domain].has_key(host):
                    PluginConfigs['DomainTree'][domain][host] = {}

                if not PluginConfigs['DomainTree'][domain][host].has_key(plugin):
                    PluginConfigs['DomainTree'][domain][host][plugin] = []

                if not mgid in PluginConfigs['DomainTree'][domain][host][plugin]:
                    PluginConfigs['DomainTree'][domain][host][plugin] += [mgid]

                if not PluginConfigs['PluginTree'].has_key(plugin):
                    PluginConfigs['PluginTree'][plugin] = {}

                if not PluginConfigs['PluginTree'][plugin].has_key(mgid):
                    PluginConfigs['PluginTree'][plugin][mgid] = {}

                if not PluginConfigs['PluginTree'][plugin][mgid].has_key(domain):
                    PluginConfigs['PluginTree'][plugin][mgid][domain] = []

                if not host in PluginConfigs['PluginTree'][plugin][mgid][domain]:
                    PluginConfigs['PluginTree'][plugin][mgid][domain] += [host]

                if not domain in PluginConfigs['DomainXref']:
                    PluginConfigs['DomainXref'] += [domain]
                    cPickle.dump(PluginConfigs['DomainXref'], open(MCconfig['PluginDir'] + '/pickles/DomainXref', 'wb') )

                if not host in PluginConfigs['HostXref']:
                    PluginConfigs['HostXref'] += [host]
                    cPickle.dump(PluginConfigs['HostXref'], open(MCconfig['PluginDir'] + '/pickles/HostXref', 'wb') )

                if not plugin in PluginConfigs['PluginXref']:
                    PluginConfigs['PluginXref'] += [plugin]
                    cPickle.dump(PluginConfigs['PluginXref'], open(MCconfig['PluginDir'] + '/pickles/PluginXref', 'wb') )

                if not mgid in PluginConfigs['MgidXref']:
                    PluginConfigs['MgidXref'] += [mgid]
                    cPickle.dump(PluginConfigs['MgidXref'], open(MCconfig['PluginDir'] + '/pickles/MgidXref', 'wb') )


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
