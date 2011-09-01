from pyramid.response import Response
from pyramid.renderers import render_to_response
from subprocess import PIPE, Popen, STDOUT
import os
import time
import lockfile
import MCutils

os.environ['PATH'] = '/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin'

class DisplayMetrics(object):
    def __init__(self, request):
        self.request = request

    def __call__(self):
        # Set pointers to global variables.
        Params = self.request.params
        MCconfig = self.request.registry.settings['MCconfig']
        PluginConfigs = self.request.registry.settings['PluginConfigs']

        # Set processing defaults.
        Now = time.time()
        Palette = (
        #    Greens     Blues   Oranges    Dk yel    Dk blu    Purple      lime      Reds      Gray
            '00CC00', '0066B3', 'FF8000', 'FFCC00', '330099', '990099', 'CCFF00', 'FF0000', '808080',
            '008F00', '00487D', 'B35A00', 'B38F00',           '6B006B', '8FB300', 'B30000', 'BEBEBE',
            '80FF80', '80C9FF', 'FFC080', 'FFE680', 'AA80FF', 'EE00CC', 'FF8080',
            '666600', 'FFBFFF', '00FFCC', 'CC6699', '999900',
            )


        # Build selections array and cross reference.
        Hosts = {}
        host_xref = []

        for host in sorted(PluginConfigs['links']):
            host_xref += [host]
            Hosts[host] = {'checked': False, 'plugin_xref': [], 'plugins': {}}

            for plugin in sorted(PluginConfigs['links'][host]):
                Hosts[host]['plugin_xref'] += [plugin]
                Hosts[host]['plugins'][plugin] = {'checked': False, 'mgid_xref': [], 'mgids': {}}

                for mgid in sorted(PluginConfigs['config'][PluginConfigs['links'][host][plugin]]):
                    Hosts[host]['plugins'][plugin]['mgid_xref'] += [mgid]
                    Hosts[host]['plugins'][plugin]['mgids'][mgid] = {'checked': False}

        # Set parameter defaults. NB: enabled parameters will have a 'disabled' value equal to their parameter name.
        Options = {
            # Graph title
            'gt': {'type': 'str', 'disabled': 'disabled', 'value': ''},

            # Graph columns
            'gc': {'type': 'int', 'disabled': 'disabled', 'value': 0, 'min': 1, 'max': 24},

            # Absolute start time
            'sa': {'type': 'int', 'disabled': 'disabled', 'value': 0, 'min': int(Now-360000000), 'max': int(Now-1800)},

            # Relative start time
            'sr': {'type': 'flt', 'disabled': 'disabled', 'value': 30, 'min': .5, 'max': 100000},

            # Time range
            'tr': {'type': 'flt', 'disabled': 'disabled', 'value': 30, 'min': .5, 'max': 100000},

            # Graph height
            'ht': {'type': 'int', 'disabled': 'disabled', 'value': 600, 'min': 100, 'max': 2400},

            # Graph width
            'wd': {'type': 'int', 'disabled': 'disabled', 'value': 1200, 'min': 100, 'max': 2400},

            # Label font size
            'fl': {'type': 'int', 'disabled': 'disabled', 'value': 8, 'min': 6, 'max': 32},

            # Statistics font size
            'fs': {'type': 'int', 'disabled': 'disabled', 'value': 8, 'min': 6, 'max': 32},

            # Timeout
            'to': {'type': 'int', 'disabled': 'disabled', 'value': 300, 'min': 60, 'max': 3600},

            # Munin graph subdirectory (hidden value)
            'h1': {'type': 'dir', 'disabled': 'h1', 'value': str(int(Now))},

            # Checkbox selections (hidden value)
            'h2': {'type': 'str', 'disabled': 'h2', 'value': ''},           
            }

        # Process keyword/value parameters.
        for param in Params.keys():
            if not Options.has_key(param):
                continue

            if (Options[param]['type'] == 'str'):
                Options[param]['disabled'] = param
                Options[param]['value'] = str(Params[param])
            elif (Options[param]['type'] == 'dir'):
                if os.path.exists(MCconfig['ImageDir'] + "/" + Params[param]):
                    Options[param]['disabled'] = param
                    Options[param]['value'] = str(Params[param])
            elif (Options[param]['type'] == 'flt'):
                param_value = abs(MCutils.StrToFloat(Params[param]))
                if (param_value >= Options[param]['min'] and param_value <= Options[param]['max']):
                    Options[param]['disabled'] = param
                    Options[param]['value'] = param_value
            else:
                param_value = abs(MCutils.StrToInt(Params[param]))
                if (param_value >= Options[param]['min'] and param_value <= Options[param]['max']):
                    Options[param]['disabled'] = param
                    Options[param]['value'] = param_value

        # Ensure image sub-directory (h1 parameter) exists.
        if not os.path.exists(MCconfig['ImageDir'] + "/" + Options['h1']['value']):
            p = Popen(['mkdir', '-p',  MCconfig['ImageDir'] + '/' + Options['h1']['value']], stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()
            if stderr != '':
                return Response('munin-collector-show: unable to create image sub-directory.\n')

        # Process the resource selection (h2) parameter.
        for h2_item in Options['h2']['value'].split('_'):
            h2_parm_valid = True
            sel = h2_item.split('.')
            for ix in range(len(sel)):
                sel[ix] = MCutils.StrToInt(sel[ix]) - 1
                if sel[ix] < 0:
                    h2_parm_valid = False
                    break

            if h2_parm_valid:
                if (len(sel) == 1):
                    host = host_xref[sel[0]]
                    Hosts[host]['checked'] = True
                elif (len(sel) == 2):
                    host = host_xref[sel[0]]
                    plugin = Hosts[host]['plugin_xref'][sel[1]]
                    Hosts[host]['plugins'][plugin]['checked'] = True
                elif (len(sel) == 3):
                    host = host_xref[sel[0]]
                    plugin = Hosts[host]['plugin_xref'][sel[1]]
                    mgid = Hosts[host]['plugins'][plugin]['mgid_xref'][sel[2]]
                    Hosts[host]['plugins'][plugin]['mgids'][mgid]['checked'] = True

        # Rationalize start time ("sa" and "sr") and time range ("tr") parameters.
        if (Options['sa']['disabled'] != 'disabled'):
            Options['sr']['disabled'] = 'disabled'
            Options['sr']['value'] = (Now - Options['sa']['value']) / 3600.0

            predicted_end_time = Options['sa']['value'] + (Options['tr']['value'] * 3600)
            if (predicted_end_time > Now):
                Options['tr']['disabled'] = 'disabled'
                Options['tr']['value'] = Options['sr']['value']

        elif (Options['sr']['disabled'] != 'disabled'):
            Options['sa']['value'] = int(Now - (Options['sr']['value'] * 3600.0))

            predicted_end_time = Options['sa']['value'] + (Options['tr']['value'] * 3600)
            if (predicted_end_time > Now):
                Options['tr']['disabled'] = 'disabled'
                Options['tr']['value'] = Options['sr']['value']

        elif (Options['tr']['disabled'] != 'disabled'):
            Options['tr']['disabled'] = 'disabled'
            Options['sr']['disabled'] = 'sr'
            Options['sr']['value'] = Options['tr']['value']
            Options['sa']['value'] = int(Now - (Options['sr']['value'] * 3600.0))
            predicted_end_time = Options['sa']['value'] + (Options['tr']['value'] * 3600)

        else:
            Options['sa']['value'] = int(Now - (Options['sr']['value'] * 3600.0))
            predicted_end_time = Options['sa']['value'] + (Options['tr']['value'] * 3600)

        debug = open('/tmp/xx', 'w')
        xx = 0
        for x in sorted(PluginConfigs['datasource'].keys()):
            xx += 1
            debug.write(str(xx) + " " + x + " " + str(PluginConfigs['datasource'][x]) + '\n\n')
        debug.write('\n')

        # Scan selections array to generate selected graphs.
        Selections = []
        for host in sorted(Hosts.keys()):
            host_sel = False
            if (Hosts[host]['checked'] == True):
                host_sel = (host_sel != True)

            for plugin in sorted(Hosts[host]['plugins'].keys()):
                mgid = plugin
                plugin_sel = host_sel
                if (Hosts[host]['plugins'][plugin]['checked'] == True):
                    plugin_sel = (plugin_sel != True)

                for mgid in sorted(Hosts[host]['plugins'][plugin]['mgids'].keys()):
                    mgid_sel = plugin_sel
                    if (Hosts[host]['plugins'][plugin]['mgids'][mgid]['checked'] == True):
                        mgid_sel = (mgid_sel != True)

                    if (mgid_sel):
                        data_path = MCconfig['DataDir'] + '/' + host + '_' + mgid
                        graph_heading = host + '(' + mgid + ')'
                        graph_path = Options['h1']['value'] + '/' + host + '_' + mgid + '_' + str(Options['sa']['value']) + '_' + str(Options['tr']['value']) + '_' + str(Options['ht']['value']) + 'x' + str(Options['wd']['value']) + '.png'

                        # Generate a graph.
                        graph_command = [
                            'rrdtool',
                            'graph',
                            '--font',
                            'DEFAULT:' + str(Options['fl']['value']) + ':DejaVuSans',
                            '--font',
                            'DEFAULT:' + str(Options['fs']['value']) + ':DejaVuSansMono',
                            '-W',
                            'Munin-Collector 1.0',
                            MCconfig['ImageDir'] + '/' + graph_path,
                            ]

                        if Options['gt']['value'] != '':
                            graph_command += [
                                '--title',
                                Options['gt']['value'],
                                ]
                        elif PluginConfigs['config'][PluginConfigs['links'][host][plugin]][mgid].has_key('graph_title'):
                            graph_command += [
                                '--title',
                                PluginConfigs['config'][PluginConfigs['links'][host][plugin]][mgid]['graph_title'],
                                ]
                        else:
                            graph_command += [
                                '--title',
                                graph_heading,
                                ]

                        graph_command += [
                            '--start',
                            '-' + str(Options['sr']['value']) + 'h',
                            ]

                        if (Options['tr']['disabled'] != 'disabled'):
                            graph_command += [
                                '--end',
                                '-' + str(Options['sr']['value'] - Options['tr']['value']) + 'h',
                                ]

                        graph_command += [
                            '--height',
                            str(Options['ht']['value']),
                            ]

                        graph_command += [
                            '--width',
                            str(Options['wd']['value']),
                            ]

                        graph_command += [
                            '--imgformat',
                            'PNG',
                            ]

                        if PluginConfigs['config'][PluginConfigs['links'][host][plugin]][mgid].has_key('graph_vlabel'):
                            graph_command += [
                                '--vertical-label',
                                PluginConfigs['config'][PluginConfigs['links'][host][plugin]][mgid]['graph_vlabel'],
                                ]

                        if PluginConfigs['config'][PluginConfigs['links'][host][plugin]][mgid].has_key('graph_args'):
                            graph_command += PluginConfigs['config'][PluginConfigs['links'][host][plugin]][mgid]['graph_args'].split()

                        if PluginConfigs['config'][PluginConfigs['links'][host][plugin]][mgid].has_key('graph_order'):
                            data_sources = PluginConfigs['config'][PluginConfigs['links'][host][plugin]][mgid]['graph_order'].split()
                        else:
                            data_sources = PluginConfigs['datasource'][PluginConfigs['links'][host][plugin]][mgid]

                        graph_command += [
                            'COMMENT:              Cur\:        Min\:        Avg\:        Max\:     \j',
                            ]

                        ds_lastupdated = 0
                        for ds in data_sources:
                            ds_path = str(data_path + '_' + ds + '.rrd')
                            if os.path.exists(ds_path):
                                p = Popen(['rrdtool', 'last',  ds_path], stdout=PIPE, stderr=PIPE)
                                stdout, stderr = p.communicate()
                                if stderr == '':
                                    last_time = MCutils.StrToInt(stdout)
                                    if stdout > ds_lastupdated:
                                        ds_lastupdated = stdout

                                ds_prefix = ''
                                graph_command += [
                                    'DEF:v' + ds + '=' + ds_path + ':mc10:AVERAGE',
                                    'DEF:a' + ds + '=' + ds_path + ':mc10:MAX',
                                    'DEF:i' + ds + '=' + ds_path + ':mc10:MIN',
                                    ]
                                if PluginConfigs['config'][PluginConfigs['links'][host][plugin]][mgid].has_key(ds + '.cdef'):
                                    ds_prefix = 'x'
                                    graph_command += [
                                        'CDEF:xv' + ds + '=v' + PluginConfigs['config'][PluginConfigs['links'][host][plugin]][mgid][ds + '.cdef'],
                                        'CDEF:xa' + ds + '=a' + PluginConfigs['config'][PluginConfigs['links'][host][plugin]][mgid][ds + '.cdef'],
                                        'CDEF:xi' + ds + '=i' + PluginConfigs['config'][PluginConfigs['links'][host][plugin]][mgid][ds + '.cdef'],
                                        ]

                        ds_ix = 0
                        for ds in data_sources:
                            ds_path = data_path + '_' + ds + '.rrd'
                            if os.path.exists(ds_path):
                                if PluginConfigs['config'][PluginConfigs['links'][host][plugin]][mgid].has_key(ds + '.draw'):
                                    ds_draw = PluginConfigs['config'][PluginConfigs['links'][host][plugin]][mgid][ds + '.draw']

                                    if ds_draw == 'AREASTACK':
                                        if ds_ix == 0:
                                            ds_draw = 'AREA'
                                        else:
                                            ds_draw = 'STACK'

                                    if ds_draw == 'LINESTACK':
                                        if ds_ix == 0:
                                            ds_draw = 'LINE2'
                                        else:
                                            ds_draw = 'STACK'

                                else:
                                    ds_draw = 'LINE2'

                                if PluginConfigs['config'][PluginConfigs['links'][host][plugin]][mgid].has_key(ds + '.colour'):
                                    ds_colour = PluginConfigs['config'][PluginConfigs['links'][host][plugin]][mgid][ds + '.colour']
                                else:
                                    ds_colour = Palette[ds_ix]

                                ds_label = ds
                                if PluginConfigs['config'][PluginConfigs['links'][host][plugin]][mgid].has_key(ds + '.label'):
                                    ds_label = PluginConfigs['config'][PluginConfigs['links'][host][plugin]][mgid][ds + '.label']

                                graph_command += [
                                    ds_draw + ':' + ds_prefix + 'v' + ds + '#' + ds_colour + ':' + ds_label,
                                    'GPRINT:' + ds_prefix + 'v' + ds + ':LAST:%6.2lf%s',
                                    'GPRINT:' + ds_prefix + 'i' + ds + ':MIN:%6.2lf%s',
                                    'GPRINT:' + ds_prefix + 'v' + ds + ':AVERAGE:%6.2lf%s',
                                    'GPRINT:' + ds_prefix + 'a' + ds + ':MAX:%6.2lf%s',
                                    ]

                                ds_ix += 1

#                        graph_command += [
#                            'COMMENT:Last Updated\: ' + join(time.ctime(ds_lastupdated).split(':'), '\') + '\r',
#                            ]
                        
                        debug.write(str(Selections) + '\n')
                        debug.write(str(graph_command) + '\n')

                        p = Popen(graph_command, stdout=PIPE, stderr=PIPE)
                        stdout, stderr = p.communicate()
                        debug.write('>>>' + stdout + '\n')
                        debug.write('<<<' + stderr + '\n')

                        Selections += [(graph_heading + " " + stdout + "/" + stderr, graph_path)]

        debug.close()

        return render_to_response('munincollector:templates/show.pt', {
            'request': self.request,
            'PluginConfigs': PluginConfigs,
            'Selections': Selections,
            'Hosts': Hosts,
            'Options': Options,
            })
