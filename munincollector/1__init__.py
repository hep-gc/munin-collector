from pyramid.config import Configurator
from munincollector.resources import Root
from subprocess import PIPE, Popen, STDOUT
import os

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    DataDir = '/tmp/munin-collector/data'
    ImageDir = '/tmp/munin-collector/images'
    LockDir = '/tmp/munin-collector/run'
    PluginDir = '/tmp/munin-collector/plugin'

    debug = open('/tmp/main.log', 'w')
    debug.write(str(global_config) + '\n\n')
    debug.write(str(Root) + '\n\n')
    debug.write(str(settings) + '\n\n')
    debug.close()

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

    debug = open("/tmp/y", "w")
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
                    continue

                if not PluginConfigs['config'].has_key(hash):
                    PluginConfigs['config'][hash] = {}

                if not PluginConfigs['config'][hash].has_key(mgid):
                    PluginConfigs['config'][hash][mgid] = {}

                PluginConfigs['config'][hash][mgid][key_value[0]] = key_value[1]

                # PluginConfigs['datasource'][hash][<mgid>] = [<ds>, <ds>, ...]
                words = key_value[0].split(".")
                debug.write(str(words)  + "\n")
                if len(words) == 2:
                    if not PluginConfigs['datasource'].has_key(hash):
                        PluginConfigs['datasource'][hash] = {}

                    if not PluginConfigs['datasource'][hash].has_key(mgid):
                        PluginConfigs['datasource'][hash][mgid] = []

                    if not words[0] in PluginConfigs['datasource'][hash][mgid]:
                        PluginConfigs['datasource'][hash][mgid] += [words[0]]

    debug.close()

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

