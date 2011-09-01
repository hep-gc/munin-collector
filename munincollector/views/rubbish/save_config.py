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
        if ('host' in self.request.params.keys() and
            'plugin' in self.request.params.keys() and
            'hash' in self.request.params.keys() and
            'mgid' in self.request.params.keys() and
            'sequence' in self.request.params.keys() and
            'data' in self.request.params.keys()): 

                p = Popen(['mkdir', '-p',  self.request.registry.settings['MCconfig']['PluginDir'] + '/links/' + self.request.params['host']], stdout=PIPE, stderr=PIPE)
                stdout, stderr = p.communicate()
                if stderr == '':
                    p = Popen(['ln', '-s', '-f', 
                        self.request.registry.settings['MCconfig']['PluginDir'] + '/config/' + self.request.params['hash'], 
                        self.request.registry.settings['MCconfig']['PluginDir'] + '/links/' + self.request.params['host'] + '/' + self.request.params['plugin']],
                        stdout=PIPE, stderr=PIPE)
                    stdout, stderr = p.communicate()
                    if stderr == '':
                        i = MCutils.StrToInt(self.request.params['sequence'])
                        if i < 1:
                            lock = lockfile.FileLock(self.request.registry.settings['MCconfig']['LockDir'] + '/' + self.request.params['hash'])
                            try:
                                lock.acquire(timeout=10)
                            except:
                                return Response('munin-collector-config: unable to obtain config file lock.\n')

                            if os.path.exists(self.request.registry.settings['MCconfig']['PluginDir'] + '/config/' + self.request.params['hash']):
                                lock.release()
                                return Response('munin-collector-config: config already saved.\n')
                            else:
                                p = Popen(['touch', self.request.registry.settings['MCconfig']['PluginDir'] + '/config/' + self.request.params['hash']], stdout=PIPE, stderr=PIPE)
                                stdout, stderr = p.communicate()
                                lock.release()

                        file = open(self.request.registry.settings['MCconfig']['PluginDir'] + '/config/' + self.request.params['hash'], 'a')
                        file.write(self.request.params['data'] + '\n')
                        file.close()
                        return Response('OK\n')
                    else:
                        return Response('munin-collector-config: unable to link.\n')
                else:
                    return Response('munin-collector-config: unable to create host directory.\n')
        else:
            if not self.request.registry.settings['MCconfig'].has_key('TestData'):
                self.request.registry.settings['MCconfig']['TestData'] = 'Hello'
            self.request.registry.settings['MCconfig']['TestCounter'] += 1
            return Response(str(self.request.registry.settings['MCconfig']['TestCounter'])
                + ' '
                + self.request.registry.settings['MCconfig']['TestData']
                + ' - '
                + self.request.registry.settings['PluginConfigs']['config'][self.request.registry.settings['PluginConfigs']['links']['elephant01.heprc.uvic.ca']['cpu']]['system.type']
                + '\n')

