from pyramid.response import Response
from subprocess import PIPE, Popen, STDOUT
import os
import lockfile
import MCutils

os.environ['PATH'] = '/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin'

class ReadConfig(object):
    def __init__(self, request):
        self.request = request

    def __call__(self):
        MCconfig = self.request.registry.settings['MCconfig']
        if not MCconfig['HostAllowed'].has_key(self.request.remote_addr):
            MCconfig['HostAllowed'][self.request.remote_addr] = MCutils.CheckAllowedDomains(MCconfig['AllowedDomains'], MCutils.IpToInt(self.request.remote_addr))

        if not MCconfig['HostAllowed'][self.request.remote_addr]:
            return Response('munin-collector-config: not authorized.\n')

        Params = self.request.params
        PluginConfigs = self.request.registry.settings['PluginConfigs']

        if (Params.has_key('host') and
            Params.has_key('plugin') and
            Params.has_key('hash') and
            Params.has_key('mgid') and
            Params.has_key('sequence') and
            Params.has_key('data')):

            host = str(Params['host'])
            plugin = str(Params['plugin'])
            hash = str(Params['hash'])
            mgid = str(Params['mgid'])
            sequence = MCutils.StrToInt(Params['sequence'])
            data = str(Params['data'])

            if data.strip() == '(nil)':
                return Response('munin-collector-config: the data field is empty ("(nil)").\n')

            p = Popen(['mkdir', '-p',  MCconfig['PluginDir'] + '/links/' + host], stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()
            if stderr == '':
                if sequence < 1:
                    # Save host's domain.
                    words = host.split('.')
                    del words[0]
                    domain = '.'.join(words)
                    if not PluginConfigs['hostdomains'].has_key(domain):
                        PluginConfigs['hostdomains'][domain] = []

                    PluginConfigs['hostdomains'][domain] += [host]

                    # Set link variable.
                    if not PluginConfigs['links'].has_key(host):
                        PluginConfigs['links'][host] = {}
                      
                    PluginConfigs['links'][host][plugin] = hash

                    # Lock around file operations.
                    lock = lockfile.FileLock(MCconfig['LockDir'] + '/' + hash)
                    try:
                        lock.acquire(timeout=10)
                    except:
                        return Response('munin-collector-config: unable to obtain config file lock.\n')

                    # Create host link to config hash.
                    p = Popen(['ln', '-s', '-f', 
                        MCconfig['PluginDir'] + '/config/' + hash, 
                        MCconfig['PluginDir'] + '/links/' + host + '/' + plugin],
                        stdout=PIPE, stderr=PIPE)
                    stdout, stderr = p.communicate()
                    if stderr != '':
                        lock.release()
                        return Response('munin-collector-config: unable to link.\n')


                    # First reporter creates config hash.
                    if os.path.exists(MCconfig['PluginDir'] + '/config/' + hash):
                        lock.release()
                        return Response('munin-collector-config: config already saved.\n')
                    else:
                        p = Popen(['touch', MCconfig['PluginDir'] + '/config/' + hash], stdout=PIPE, stderr=PIPE)
                        stdout, stderr = p.communicate()
                        lock.release()

                file = open(MCconfig['PluginDir'] + '/config/' + hash, 'a')
                if sequence < 1:
                    file.write('pluginname ' + plugin + '\n')
                file.write(data + '\n')
                file.close()

                # Set config variable.
                if (data.strip() != '' and data.split(' ', 1)[0] != 'multigraph'):
                    if not PluginConfigs['config'].has_key(hash):
                        PluginConfigs['config'][hash] = {}
                                         
                    if not PluginConfigs['config'][hash].has_key(mgid):
                        PluginConfigs['config'][hash][mgid] = {}
                                         
                    key_value = data.split(' ', 1)
                    PluginConfigs['config'][hash][mgid][key_value[0]] = key_value[1]

                    # Update datasource variable: PluginConfigs['datasource'][hash][<mgid>] = [<ds>, <ds>, ...]
                    words = key_value[0].split('.')
                    if len(words) == 2:
                        if not PluginConfigs['datasource'].has_key(hash):
                            PluginConfigs['datasource'][hash] = {}
                                             
                        if not PluginConfigs['datasource'][hash].has_key(mgid):
                            PluginConfigs['datasource'][hash][mgid] = []
                                             
                        if not words[0] in PluginConfigs['datasource'][hash][mgid]:
                            PluginConfigs['datasource'][hash][mgid] += [words[0]]

                return Response('OK\n')
            else:
                return Response('munin-collector-config: unable to create host directory.\n')
        else:
            missing = []
            if not Params.has_key('host'):
                missing += ['host']

            if not Params.has_key('plugin'):
                missing += ['plugin']

            if not Params.has_key('hash'):
                missing += ['hash']

            if not Params.has_key('mgid'):
                missing += ['mgid']

            if not Params.has_key('sequence'):
                missing += ['sequence']

            if not Params.has_key('data'):
                missing += ['data']

            return Response('munin-collector-config: the following required fields are missing: ' + str(missing) +     '\n')

