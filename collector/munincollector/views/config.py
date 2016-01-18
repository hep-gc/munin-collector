from pyramid.response import Response
from subprocess import PIPE, Popen, STDOUT
import os
import re
import lockfile
import MCutils
import time

os.environ['PATH'] = '/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin'

def check_params(params, param_id, option):
    if not params.has_key(param_id):
        return 0

    if (option and len(str(params[param_id])) < 1):
        return 0

    if (option and re.search(r'[^\_\-\.a-zA-Z0-9]', str(params[param_id]))):
        return 0

    return 1

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

        if (check_params(Params, 'host', 1) and 
            check_params(Params, 'plugin', 1) and 
            check_params(Params, 'hash', 1) and 
            check_params(Params, 'mgid', 1) and 
            check_params(Params, 'sequence', 1) and 
            check_params(Params, 'data', 0)):

            host = str(Params['host'])
            plugin = str(Params['plugin'])
            hash = str(Params['hash'])
            mgid = str(Params['mgid'])
            sequence = MCutils.StrToInt(Params['sequence'])
            data = str(Params['data'])

            if data.strip() == '(nil)':
                MCutils.Logger(MCconfig, 2, 'config', 'Returning data field is empty.')
                return Response('munin-collector-config: the data field is empty ("(nil)").\n')

            if host == 'localhost.localdomain':
                MCutils.Logger(MCconfig, 2, 'config', 'Rejecting non-specific FQDN of "localhost.localdomain" from IP=' + str(self.request.remote_addr) + '.')
                return Response('munin-collector-config: Rejecting non-specific FQDN of "localhost.localdomain".\n')

            p = Popen(['mkdir', '-p',  MCconfig['PluginDir'] + '/links/' + host], stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()
            if stderr == '':
                if sequence < 1:
                    # Lock around file operations.
                    lock = lockfile.FileLock(MCconfig['LockDir'] + '/' + hash)
                    try:
                        lock.acquire(timeout=10)
                    except:
                        MCutils.Logger(MCconfig, 1, 'config', 'Unable to obtain config file lock:' + hash + '.')
                        return Response('munin-collector-config: unable to obtain config file lock:' + hash + '.\n')

                    # If the host link to the plugin configuration hash already exists and the new hash and the old hash differ, delete the obsolete symlink.
                    if os.path.exists(MCconfig['PluginDir'] + '/links/' + host + '/' + plugin):
                        p1 = Popen(['readlink', MCconfig['PluginDir'] + '/links/' + host + '/' + plugin], stdout=PIPE, stderr=STDOUT)
                        p2 = Popen(['xargs', '-L', '1', 'basename'], stdin=p1.stdout, stdout=PIPE, stderr=STDOUT)
                        old_hash = p2.communicate()[0][:-1]
                        if old_hash != hash:
                            p = Popen(['rm', '-f', MCconfig['PluginDir'] + '/links/' + host + '/' + plugin], stdout=PIPE, stderr=STDOUT)
                            MCutils.Logger(MCconfig, 3, 'config', 'Obsolete config link deleted, host=' + host + ', plugin=' + plugin + '(' + old_hash + ').')


                    # If the host link to the plugin configuration hash does not exist (we might have just deleted an obsolete symlink), create it.
                    if not os.path.exists(MCconfig['PluginDir'] + '/links/' + host + '/' + plugin):
                        p = Popen(['ln', '-s', '-f', 
                            MCconfig['PluginDir'] + '/config/' + hash, 
                            MCconfig['PluginDir'] + '/links/' + host + '/' + plugin],
                            stdout=PIPE, stderr=PIPE)

                        stdout, stderr = p.communicate()
                        if stderr != '':
                            lock.release()
                            MCutils.Logger(MCconfig, 1, 'config', 'Unable to create config link.')
                            return Response('munin-collector-config: unable to link.\n')

                        # Update the timestamp.
                        open(MCconfig['PluginDir'] + '/config/.last_updated', 'w').close()

                        MCutils.Logger(MCconfig, 3, 'config', 'New config link created, host=' + host + ', plugin=' + plugin + '(' + hash + ').')

                    # First reporter creates the plugin configuration hash.
                    if os.path.exists(MCconfig['PluginDir'] + '/config/' + hash):
                        lock.release()
                        MCutils.Logger(MCconfig, 4, 'config', 'Config already saved.')
                        return Response('munin-collector-config: already saved.\n')
                    else:
                        p = Popen(['touch', MCconfig['PluginDir'] + '/config/' + hash], stdout=PIPE, stderr=PIPE)
                        stdout, stderr = p.communicate()
                        lock.release()
                        MCutils.Logger(MCconfig, 3, 'config', 'New config file created, hash=' + hash + '.')

                # Append new line to configuration file.
                file = open(MCconfig['PluginDir'] + '/config/' + hash, 'a')
                if sequence < 1:
                    file.write('pluginname ' + plugin + '\n')
                file.write(data + '\n')
                file.close()

                # Update the timestamp.
                open(MCconfig['PluginDir'] + '/config/.last_updated', 'w').close()

                MCutils.Logger(MCconfig, 4, 'config', 'New line appended to config file.')

                return Response('OK\n')
            else:
                MCutils.Logger(MCconfig, 1, 'config', 'Unable to create host directory.')
                return Response('munin-collector-config: unable to create host directory.\n')
        else:
            missing = []
            if not check_params(Params, 'host', 1):
                missing += ['host']

            if not check_params(Params, 'plugin', 1):
                missing += ['plugin']

            if not check_params(Params, 'hash', 1):
                missing += ['hash']

            if not check_params(Params, 'mgid', 1):
                missing += ['mgid']

            if not check_params(Params, 'sequence', 1):
                missing += ['sequence']

            if not check_params(Params, 'data', 0):
                missing += ['data']

            MCutils.Logger(MCconfig, 2, 'config', 'From IP=' + str(self.request.remote_addr) + ', the following required fields are missing or invalid: ' + str(missing))
            return Response('munin-collector-config: the following required fields are missing or invalid: ' + str(missing) +     '\n')

