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

# Check the currency of the plugin configuration cache.
def CachePluginCheck (MCconfig, PluginConfigs):

    last_cache_update = LastCacheUpdate(MCconfig)

    if PluginConfigs['Timestamp'] < last_cache_update:
        original_timestamp = PluginConfigs['Timestamp']
        slept = 0
        while PluginConfigs['Timestamp'] < last_cache_update:
            time.sleep(1)
            slept += 1
            PluginConfigs['Timestamp'] = int(time.time())
            last_cache_update = LastCacheUpdate(MCconfig)

        Logger(MCconfig, 3, 'MCutils', 'CachePluginCheck: Updating cache, original_timestamp=' + str(original_timestamp) + ', last_cache_update=' + str(last_cache_update) + ', PluginConfigs[\'Timestamp\']=' + str(PluginConfigs['Timestamp']) + ', slept=' + str(slept) + '.')
        CachePluginConfigs (MCconfig, PluginConfigs)


# Cache plugin configuration.
def CachePluginConfigs (MCconfig, PluginConfigs):
    # Update the timestamp for the last cache refresh.

    Logger(MCconfig, 4, 'MCutils', 'Stage 1: Cache plugin links - PluginConfigs[\'links\'][<host>][<plugin>] = <hash>')
    hash_offset = len(MCconfig['PluginDir'] + '/config/')
    p = Popen(['ls', MCconfig['PluginDir'] + '/links'], stdout=PIPE, stderr=PIPE)
    hosts, stderr = p.communicate()
    if stderr == '':
        hosts = hosts.splitlines()

        for host in hosts:
            p = Popen(['ls', '-l', MCconfig['PluginDir'] + '/links/' + host], stdout=PIPE, stderr=PIPE)
            links, stderr = p.communicate()
            if stderr == '':
                links = links.splitlines()

                for link in links:
                    words = link.split()
                    if len(words) >= 11:
                        plugin = words[8]
                        hash = words[10][hash_offset:]

                        if not PluginConfigs['links'].has_key(host):
                            PluginConfigs['links'][host] = {}

                        if not PluginConfigs['links'][host].has_key(plugin):
                            PluginConfigs['links'][host][plugin] = hash

                            link_file = open(MCconfig['PluginDir'] + '/links/' + host + '/' + plugin, 'r')
                            link_timestamp = os.fstat(link_file.fileno())[ST_CTIME]
                            link_file.close()

                            PluginConfigs['Timestamps']['s1'] += [ (link_timestamp, host, plugin) ]

                            Logger(MCconfig, 4, 'MCutils', 'Link added for host=' + host + ', plugin=' + plugin + ', hash=' + hash + '.')

    Logger(MCconfig, 4, 'MCutils', 'Stage 2: Cache plugin configs - PluginConfigs[\'config\'][<hash>][<mgid>][<key>] = <value>')
    p = Popen(['ls', MCconfig['PluginDir'] + '/config'], stdout=PIPE, stderr=PIPE)
    hashes, stderr = p.communicate()
    if stderr == '':
        hashes = hashes.splitlines()
        for hash in hashes:
            if not PluginConfigs['config'].has_key(hash):
                # Wait for the hash to age before processing.
                while 1:
                    hash_file = open(MCconfig['PluginDir'] + '/config/' + hash, 'r')
                    hash_age = time.time() - os.fstat(hash_file.fileno())[ST_CTIME]
                    hash_file.close()
                    if hash_age > 5:
                        break

                    Logger(MCconfig, 3, 'MCutils', 'Sleeping 5 seconds waiting for hash to age.')
                    time.sleep(5)

                Logger(MCconfig, 4, 'MCutils', 'Processing hash=' + hash + '.')
                hash_file = open(MCconfig['PluginDir'] + '/config/' + hash, 'r')
                hash_timestamp = os.fstat(hash_file.fileno())[ST_CTIME]
                lines = hash_file.readlines()
                hash_file.close()
                for line in lines:
                    line = line.strip()
                    if line == '' or line == '(nil)':
                        continue

                    key_value = line.split(' ', 1)

                    if key_value[0] == 'pluginname' or key_value[0] == 'multigraph':
                        mgid = key_value[1]
                        PluginConfigs['Timestamps']['s2'] += [ (hash_timestamp, mgid) ]
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

    Logger(MCconfig, 4, 'MCutils', 'Stage 3: Build domain and plugin trees')
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

    Logger(MCconfig, 4, 'MCutils', 'Stage 4: Build cross references used for graph selection')
    for s1 in sorted(PluginConfigs['Timestamps']['s1']):
        domain =GetDomain(s1[1])

        if not domain in PluginConfigs['DomainXref']:
            PluginConfigs['DomainXref'] += [ domain ]

        if not s1[1] in PluginConfigs['HostXref']:
            PluginConfigs['HostXref'] += [ s1[1] ]

        if not s1[2] in PluginConfigs['PluginXref']:
            PluginConfigs['PluginXref'] += [ s1[2] ]

    for s2 in sorted(PluginConfigs['Timestamps']['s2']):

        if not s2[1] in PluginConfigs['MgidXref']:
            PluginConfigs['MgidXref'] += [ s2[1] ]

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
