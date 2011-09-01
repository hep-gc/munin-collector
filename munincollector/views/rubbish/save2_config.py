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
        Params = self.request.params
        MCconfig = self.request.registry.settings['MCconfig']
        PluginConfigs = self.request.registry.settings['PluginConfigs']

        if ('host' in Params.keys() and
            'plugin' in Params.keys() and
            'hash' in Params.keys() and
            'mgid' in Params.keys() and
            'sequence' in Params.keys() and
            'data' in Params.keys()): 

                p = Popen(['mkdir', '-p',  MCconfig['PluginDir'] + '/links/' + Params['host']], stdout=PIPE, stderr=PIPE)
                stdout, stderr = p.communicate()
                if stderr == '':
                    p = Popen(['ln', '-s', '-f', 
                        MCconfig['PluginDir'] + '/config/' + Params['hash'], 
                        MCconfig['PluginDir'] + '/links/' + Params['host'] + '/' + Params['plugin']],
                        stdout=PIPE, stderr=PIPE)
                    stdout, stderr = p.communicate()
                    if stderr == '':
                        i = MCutils.StrToInt(Params['sequence'])
                        if i < 1:
                            lock = lockfile.FileLock(MCconfig['LockDir'] + '/' + Params['hash'])
                            try:
                                lock.acquire(timeout=10)
                            except:
                                return Response('munin-collector-config: unable to obtain config file lock.\n')

                            if os.path.exists(MCconfig['PluginDir'] + '/config/' + Params['hash']):
                                lock.release()
                                return Response('munin-collector-config: config already saved.\n')
                            else:
                                p = Popen(['touch', MCconfig['PluginDir'] + '/config/' + Params['hash']], stdout=PIPE, stderr=PIPE)
                                stdout, stderr = p.communicate()
                                lock.release()

                        file = open(MCconfig['PluginDir'] + '/config/' + Params['hash'], 'a')
                        file.write(Params['data'] + '\n')
                        file.close()
                        return Response('OK\n')
                    else:
                        return Response('munin-collector-config: unable to link.\n')
                else:
                    return Response('munin-collector-config: unable to create host directory.\n')
        else:
            if not MCconfig.has_key('TestData'):
                MCconfig['TestData'] = 'Hello'
            MCconfig['TestCounter'] += 1
            return Response(str(MCconfig['TestCounter'])
                + ' '
                + MCconfig['TestData']
                + ' - '
                + PluginConfigs['config'][PluginConfigs['links']['elephant01.heprc.uvic.ca']['cpu']]['system.type']
                + '\n')

