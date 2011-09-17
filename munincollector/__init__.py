from pyramid.config import Configurator
from munincollector.resources import Root
from subprocess import PIPE, Popen, STDOUT
import ConfigParser
import MCutils
import os
import re

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    # Read and process our configuration file.
    ConfigurationFile = '/etc/munin/munin-collector.conf'
    if not os.path.exists(ConfigurationFile):
        ConfigurationFile = global_config['here'] + '/munincollector/samples/etc/munin/munin-collector.conf'

    AllowedDomains = []
    HostAllowed = {}
    Options = []

    if not os.path.exists(ConfigurationFile):
        print "Configuration file '%s' does not exist." % ConfigurationFile
        quit()
    else:
        config_file = ConfigParser.ConfigParser()

        try:
            config_file.read(ConfigurationFile)
        except IOError:
            print "Configuration file problem: There was a " \
            "problem reading %s. Check that it is readable," \
            "and that it exists. " % ConfigurationFile
            quit()
        except ConfigParser.ParsingError:
            print "Configuration file problem: Couldn't " \
            "parse your file. Check for spaces before or after variables."
            quit()
        except:
            print "Configuration file problem: There is something wrong with " \
            "your config file."
            quit()

        if config_file.has_option("munin-collector", "DataDir"):
            DataDir = config_file.get("munin-collector", "DataDir")
        else:
            print "Configuration file did not specify a path for 'DataDir'."
            quit()

        if config_file.has_option("munin-collector", "ImageDir"):
            ImageDir = config_file.get("munin-collector", "ImageDir")
        else:
            print "Configuration file did not specify a path for 'ImageDir'."
            quit()

        if config_file.has_option("munin-collector", "LockDir"):
            LockDir = config_file.get("munin-collector", "LockDir")
        else:
            print "Configuration file did not specify a path for 'LockDir'."
            quit()

        if config_file.has_option("munin-collector", "PluginDir"):
            PluginDir = config_file.get("munin-collector", "PluginDir")
        else:
            print "Configuration file did not specify a path for 'PluginDir'."
            quit()

        if config_file.has_option("munin-collector", "Domains"):
            domain_string = config_file.get("munin-collector", "Domains")

            domains = domain_string.split(',')
            for domain in domains:
                words = domain.strip().split('/')
                if len(words) < 1 or len(words) > 2:
                    print "Domains contained an invalid specification: '%s' - too many '/'s." % domain
                    quit()

                if ':' in words[0]:
                    partitions = words[0].partition('::')
                    nibbles_1 =  partitions[0].split(':')
                    if partitions[1] == '::':
                        nibbles_2 =  partitions[2].split(':')
                    nibble_bits = 16
                    nibble_count = 8
                else:
                    nibbles_1 = words[0].split('.')
                    nibbles_2 = ()
                    nibble_bits = 8
                    nibble_count = 4

                if len(words) == 1:
                    subnet_bits = nibble_bits * nibble_count
                else:
                    subnet_bits = MCutils.StrToInt(words[1])

                if len(nibbles_1) + len(nibbles_2) > nibble_count:
                    print "Domains contained an invalid specification: '%s' - too many octets/hextets." % domain
                    quit()

                if subnet_bits > nibble_bits * nibble_count:
                    print "Domains contained an invalid specification: '%s' - too many subnet bits." % domain
                    quit()

                host_bits = (nibble_bits * nibble_count) - subnet_bits
                max_domain_host_count = (2 ** host_bits)

                domain_min_ip_1 = 0
                for ix in range(nibble_count):
                    domain_min_ip_1 = domain_min_ip_1 * (2 ** nibble_bits)
                    if len(nibbles_1) > ix:
                        domain_min_ip_1 += MCutils.StrToInt(nibbles_1[ix])

                domain_min_ip_2 = 0
                for ix in range(len(nibbles_2)):
                    domain_min_ip_2 = domain_min_ip_2 * (2 ** nibble_bits)
                    domain_min_ip_2 += MCutils.StrToInt(nibbles_2[ix])

                domain_min_ip = int((domain_min_ip_1 + domain_min_ip_2) / max_domain_host_count) * max_domain_host_count
                domain_max_ip = domain_min_ip + (2 ** host_bits) - 1
                AllowedDomains += [(domain_min_ip, domain_max_ip)]

            AllowedDomains = sorted(AllowedDomains)

        if config_file.has_option("munin-collector", "Options"):
            option_string = config_file.get("munin-collector", "Options")

            options = option_string.split(',')
            for option in options:
                option = option.strip()
                if not option in Options:
                    Options += [option]

            Options = sorted(Options)

    # Ensure that each required directory exists.
    p = Popen(['mkdir', '-p', DataDir], stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()

    p = Popen(['mkdir', '-p', ImageDir], stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()

    p = Popen(['mkdir', '-p', LockDir], stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()

    p = Popen(['mkdir', '-p', PluginDir + '/config'], stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()

    p = Popen(['mkdir', '-p', PluginDir + '/links'], stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()

    MCconfig = {
        'DataDir': DataDir,
        'ImageDir': ImageDir,
        'LockDir': LockDir,
        'PluginDir': PluginDir,
        'AllowedDomains': AllowedDomains,
        'HostAllowed': HostAllowed,
        'Options': Options,
        }

    PluginConfigs = {'config': {}, 'datasource': {}, 'hostdomains': {}, 'links': {}}

    # Cache plugin links (stage 1): 
    #     PluginConfigs['links'][<host>][<plugin>] = <hash>
    hash_offset = len(PluginDir + '/config/')
    p = Popen(['ls', PluginDir + '/links'], stdout=PIPE, stderr=PIPE)
    hosts, stderr = p.communicate()
    if stderr == '':
        hosts = hosts.splitlines()

        for host in hosts:
            words = host.split('.')
            del words[0]
            domain = '.'.join(words)
            if not PluginConfigs['hostdomains'].has_key(domain):
                PluginConfigs['hostdomains'][domain] = []

            if not host in PluginConfigs['hostdomains'][domain]:
                PluginConfigs['hostdomains'][domain] += [host]

            p = Popen(['ls', '-l', PluginDir + '/links/' + host], stdout=PIPE, stderr=PIPE)
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

                        PluginConfigs['links'][host][plugin] = hash

    # Cache plugin config and datasource lists (stage 2): 
    #     PluginConfigs['config'][<hash>][<mgid>][<key>] = <value>
    p = Popen(['ls', PluginDir + '/config'], stdout=PIPE, stderr=PIPE)
    hashs, stderr = p.communicate()
    if stderr == '':
        hashs = hashs.splitlines()
        for hash in hashs:
            hash_file = open(PluginDir + '/config/' + hash, 'r')
            lines = hash_file.readlines()
            hash_file.close()
            for line in lines:
                line = line.strip()
                if line == '' or line == '(nil)':
                    continue

                key_value = line.split(' ', 1)

                if key_value[0] == 'pluginname' or key_value[0] == 'multigraph':
                    mgid = key_value[1]
                    pp = re.search('\.', mgid)
                    if pp:
                        [mgid, kprefix] = mgid.split('.', 1)
                        kprefix = kprefix + '_'
                    else:
                        kprefix = ''
                    continue

                if not PluginConfigs['config'].has_key(hash):
                    PluginConfigs['config'][hash] = {}

                if not PluginConfigs['config'][hash].has_key(mgid):
                    PluginConfigs['config'][hash][mgid] = {}

                PluginConfigs['config'][hash][mgid][kprefix + key_value[0]] = key_value[1]

                # PluginConfigs['datasource'][hash][<mgid>] = [<ds>, <ds>, ...]
                words = key_value[0].split(".")
                if len(words) == 2:
                    ds = kprefix + words[0]
                    if not PluginConfigs['datasource'].has_key(hash):
                        PluginConfigs['datasource'][hash] = {}

                    if not PluginConfigs['datasource'][hash].has_key(mgid):
                        PluginConfigs['datasource'][hash][mgid] = []

                    if not ds in PluginConfigs['datasource'][hash][mgid]:
                        PluginConfigs['datasource'][hash][mgid] += [ds]

    config = Configurator(root_factory=Root, settings=settings)
    config.add_settings({'MCconfig': MCconfig})
    config.add_settings({'PluginConfigs': PluginConfigs})
    config.add_view('munincollector.views.show.DisplayMetrics')
    config.add_view('munincollector.views.config.ReadConfig', name='config')
    config.add_view('munincollector.views.value.ReadValue', name='value')
#    config.add_view('munincollector.views.show.DisplayMetrics',
#                    context='munincollector:resources.Root',
#                    renderer='munincollector:templates/show.pt')
    config.add_static_view('static', 'munincollector:static')
    return config.make_wsgi_app()

