from pyramid.response import Response
from subprocess import PIPE, Popen, STDOUT
import os
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
            Params.has_key('time') and
            Params.has_key('key') and
            Params.has_key('value')):

            host = str(Params['host'])
            plugin = str(Params['plugin'])
            mgid = str(Params['mgid'])
            time = str(Params['time'])
            key = str(Params['key'])
            value = str(Params['value'])


            if PluginConfigs['links'].has_key(host):
                PC = PluginConfigs['config'][PluginConfigs['links'][host][plugin]][mgid]

                rrd_path = MCconfig['DataDir'] + '/' + host + '-' + mgid + '-' + key + MCutils.MuninType(PC, key) + '.rrd'
                if not os.path.exists(rrd_path): 
                    # create rrd file for plugin value.
                    base_time = str(MCutils.StrToInt(time)-30)

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
                        return Response('munin-collector-value: unable to create rrd file -' + data_source + ' ' + stderr)

                p = Popen(['rrdtool', 'update', rrd_path, '-t42', time + ':' + value], stdout=PIPE, stderr=PIPE)
                stdout, stderr = p.communicate()
                if stderr != '':
                    return Response('munin-collector-value: unable to update rrd file -' + stderr)

                return Response('OK\n')

            else:
                return Response('munin-collector-value: unable to retrieve plugin configuration.\n')
        else:
            missing = []
            if not Params.has_key('host'):
                missing += ['host']

            if not Params.has_key('plugin'):
                missing += ['plugin']

            if not Params.has_key('mgid'):
                missing += ['mgid']

            if not Params.has_key('time'):
                missing += ['time']

            if not Params.has_key('key'):
                missing += ['key']

            if not Params.has_key('value'):
                missing += ['value']

            return Response('munin-collector-value: the following required fields are missing: ' + str(missing) + '\n')

