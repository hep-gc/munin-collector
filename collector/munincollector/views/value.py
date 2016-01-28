from pyramid.response import Response
from subprocess import PIPE, Popen, STDOUT
import os
import re
from stat import *
import MCutils

import cPickle

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

            MCutils.Logger(MCconfig, 4, 'value', 'Entered, host=' + host + ', plugin=' + plugin + ', mgid=' + mgid + ', key=' + key + ', values=' + values)

            # Ensure the cached configuration is up to date.
            if MCutils.ReloadPluginConfig(MCconfig, PluginConfigs):
                PluginConfigs = cPickle.load( open( MCconfig['PluginDir'] + '/pickles/PluginConfigs', "rb" ) )
                PluginConfigs['Timestamp'] = os.stat(MCconfig['PluginDir'] + '/pickles/PluginConfigs')

            # PluginConfigs['links'][host][plugin] = config_hash
            if not host in PluginConfigs['links']:
                return self._bad_key(MCconfig, host, plugin, mgid, key, values, PluginConfigs, 'bad host parameter')

            if not plugin in PluginConfigs['links'][host]:
                return self._bad_key(MCconfig, host, plugin, mgid, key, values, PluginConfigs, 'bad plugin parameter')

            config_hash = PluginConfigs['links'][host][plugin]

            # PluginConfigs['config'][config_hash][mgid][key] = value
            if not config_hash in PluginConfigs['config']:
                return self._bad_key(MCconfig, host, plugin, mgid, key, values, PluginConfigs, 'undefined config hash ' + config_hash)

            if not mgid in PluginConfigs['config'][config_hash]:
                return self._bad_key(MCconfig, host, plugin, mgid, key, values, PluginConfigs, 'bad mgid parameter (not in config)')

            # PluginConfigs['datasource'][config_hash][mgid] += [data_source]
            if not config_hash in PluginConfigs['datasource']:
                return self._bad_key(MCconfig, host, plugin, mgid, key, values, PluginConfigs, 'undefined datasource hash ' + config_hash)

            if not mgid in PluginConfigs['datasource'][config_hash]:
                return self._bad_key(MCconfig, host, plugin, mgid, key, values, PluginConfigs, 'bad mgid parameter (not in datasource)')

            MCutils.Logger(MCconfig, 4, 'value', 'Inserting new values into round-robin database (rrd).')

            PC = PluginConfigs['config'][config_hash][mgid]

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
                    return Response('munin-collector-value: unable to create rrd file -' + data_source + ' ' + stderr)

            value_list = values.split()
            update_command = ['rrdtool', 'update', rrd_path, '-t42'] + value_list
            p = Popen(update_command, stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()
            if stderr != '':
                MCutils.Logger(MCconfig, 2, 'value', 'Error return from rrdtool update, stderr: ' + stderr)
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
                return Response('munin-collector-value: unable to update rrd file -' + stderr)

            return Response('OK\n')
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

    def _bad_key(self, MCconfig, host, plugin, mgid, key, values, PluginConfigs, bad_key):

        last_cache_update = os.stat(MCconfig['PluginDir'] + '/config/.last_updated')

        MCutils.Logger(MCconfig, 2, 'value', bad_key + ', host=' + host + ' (' + str(self.request.remote_addr) + '), plugin=' + plugin + ', mgid=' + mgid + ', key=' + key + ', values=' + values + ', cache_time=' + str(PluginConfigs['Timestamp']) + ', config_time=' + str(last_cache_update.st_mtime) + '.')
        return Response('munin-collector-value: ' + bad_key + '.\n')

