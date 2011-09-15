from pyramid.response import Response
from subprocess import PIPE, Popen, STDOUT
import os
import re
import lockfile
import MCutils

os.environ['PATH'] = '/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin'

class ReadValue(object):
    def __init__(self, request):
        self.request = request

    def __call__(self):
        MCconfig = self.request.registry.settings['MCconfig']
        if not MCconfig['HostAllowed'].has_key(self.request.remote_addr):
            MCconfig['HostAllowed'][self.request.remote_addr] = MCutils.CheckAllowedDomains(MCconfig['AllowedDomains'], MCutils.IpToInt(self.request.remote_addr))

        if not MCconfig['HostAllowed'][self.request.remote_addr]:
            return Response('munin-collector-value: (' + self.request.remote_addr + ') not authorized.\n')

        Params = self.request.params
        PluginConfigs = self.request.registry.settings['PluginConfigs']

        if (Params.has_key('host') and
            Params.has_key('plugin') and
            Params.has_key('mgid') and
            Params.has_key('key') and
            Params.has_key('values')):

            host = str(Params['host'])
            plugin = str(Params['plugin'])
            mgid = str(Params['mgid'])
            key = str(Params['key'])
            values = str(Params['values'])


            # PluginConfigs['links'][<host>][<plugin>] = <hash>
            # PluginConfigs['config'][<hash>][<mgid>][<key>] = <value>
            # PluginConfigs['datasource'][hash][<mgid>] = [<ds>, <ds>, ...]
            if (PluginConfigs['links'].has_key(host) and
                PluginConfigs['links'][host].has_key(plugin) and
                PluginConfigs['config'][PluginConfigs['links'][host][plugin]].has_key(mgid) and
                key in PluginConfigs['datasource'][PluginConfigs['links'][host][plugin]][mgid]):

                PC = PluginConfigs['config'][PluginConfigs['links'][host][plugin]][mgid]

                lock = lockfile.FileLock(MCconfig['LockDir'] + '/value_update')
                try:
                    lock.acquire(timeout=180)
                except:
                    return Response('munin-collector-value: unable to obtain value update file lock.\n')

                rrd_path = MCconfig['DataDir'] + '/' + host + '-' + mgid + '-' + key + MCutils.MuninType(PC, key) + '.rrd'
                if not os.path.exists(rrd_path): 
                    # create rrd file for plugin values.
                    base_time = str(MCutils.StrToInt(values.split()[0].split(':')[0])-30)

                    if PC.has_key(key + '.type'):
                        data_type = PC[key + '.type'].strip()
                    else:
                        data_type = 'GAUGE'

                    if PC.has_key(key + '.min'):
                        min_val = PC[key + '.min']
                    else:
                        min_val = 'U'

                    if PC.has_key(key + '.max'):
                        max_val = PC[key + '.max']
                    else:
                        max_val = 'U'

                    data_source = 'DS:42:' + data_type + ':600:' + min_val + ':' + max_val

                    p = Popen(['rrdtool', 'create', rrd_path,
                    '-b ' + base_time,
                    data_source,
                    'RRA:AVERAGE:0.5:1:105408', # 5 minute averages for 366 days
                    'RRA:MIN:0.5:1:8928',       # 5 minute minimums for 31 days
                    'RRA:MAX:0.5:1:8928',       # 5 minute maximums for 31 days
                    'RRA:MIN:0.5:288:366',      # daily minimums for 366 days
                    'RRA:MAX:0.5:288:366'],     # daily maximums for 366 days
                    stdout=PIPE, stderr=PIPE)
                    stdout, stderr = p.communicate()
                    if stderr != '':
                        lock.release()
                        return Response('munin-collector-value: unable to create rrd file -' + data_source + ' ' + stderr)

                value_list = values.split()
                update_command = ['rrdtool', 'update', rrd_path, '-t42'] + value_list
                p = Popen(update_command, stdout=PIPE, stderr=PIPE)
                stdout, stderr = p.communicate()
                if stderr != '':
                    pp = re.search(' illegal attempt to update using time ', stderr)
                    while pp:
                        value_list = value_list[1:]
                        if len(value_list) < 1:
                            stderr = ''
                            break
                        update_command = ['rrdtool', 'update', rrd_path, '-t42'] + value_list
                        p = Popen(update_command, stdout=PIPE, stderr=PIPE)
                        stdout, stderr = p.communicate()
                        pp = re.search(' illegal attempt to update using time ', stderr)


                if stderr != '':
                    lock.release()
                    return Response('munin-collector-value: unable to update rrd file -' + stderr)

                lock.release()
                return Response('OK\n')

            else:
                return Response('munin-collector-value: bad input keys.\n')
        else:
            missing = []
            if not Params.has_key('host'):
                missing += ['host']

            if not Params.has_key('plugin'):
                missing += ['plugin']

            if not Params.has_key('mgid'):
                missing += ['mgid']

            if not Params.has_key('key'):
                missing += ['key']

            if not Params.has_key('values'):
                missing += ['values']

            return Response('munin-collector-value: the following required fields are missing: ' + str(missing) + '\n')

