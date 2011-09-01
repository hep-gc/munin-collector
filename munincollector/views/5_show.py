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
            # Munin graph subdirectory (hidden value)
            'h1': {'type': 'dir', 'disabled': 'h1', 'value': str(int(Now))},

            # Checkbox selections (hidden value)
            'h2': {'type': 'str', 'disabled': 'h2', 'value': ''},           

            # Absolute start time
            'ta': {'type': 'int', 'disabled': 'disabled', 'value': 0, 'min': int(Now-360000000), 'max': int(Now-1800)},

            # Relative start time/time range
            'tr': {'type': 'flt', 'disabled': 'disabled', 'value': 30, 'min': .5, 'max': 100000},

            # Timeout
            'to': {'type': 'int', 'disabled': 'disabled', 'value': 300, 'min': 10, 'max': 3600},

            # Graph height
            'ht': {'type': 'int', 'disabled': 'disabled', 'value': 400, 'min': 100, 'max': 2400},

            # Graph width
            'wd': {'type': 'int', 'disabled': 'disabled', 'value': 800, 'min': 100, 'max': 2400},

            # Title font size
            'ft': {'type': 'int', 'disabled': 'disabled', 'value': 8, 'min': 6, 'max': 32},

            # Axis font size
            'fa': {'type': 'int', 'disabled': 'disabled', 'value': 8, 'min': 6, 'max': 32},

            # Vertical Label (UNIT) font size
            'fv': {'type': 'int', 'disabled': 'disabled', 'value': 8, 'min': 6, 'max': 32},

            # Statistics (LEGEND) font size
            'fs': {'type': 'int', 'disabled': 'disabled', 'value': 8, 'min': 0, 'max': 32},

            # Graph columns
            'gc': {'type': 'int', 'disabled': 'disabled', 'value': 1, 'min': 1, 'max': 24},

            # Graph title
            'gt': {'type': 'str', 'disabled': 'disabled', 'value': ''},

            # Graph title
            'if': {'type': 'str', 'disabled': 'if', 'value': 'PNG'},

            }

        # Process keyword/value parameters.
        for param in Params.keys():
            if not Options.has_key(param):
                continue

            if (Options[param]['type'] == 'str'):
                if str(Params[param]) != '':
                    Options[param]['disabled'] = param
                    Options[param]['value'] = str(Params[param])
            elif (Options[param]['type'] == 'dir'):
                if str(Params[param]) != '':
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

                    if len(Hosts[host]['plugins'][plugin]['mgids'].keys()) < 2:
                        mgid = plugin
                        Hosts[host]['plugins'][plugin]['mgids'][mgid]['checked'] = True

                elif (len(sel) == 3):
                    host = host_xref[sel[0]]
                    plugin = Hosts[host]['plugin_xref'][sel[1]]
                    mgid = Hosts[host]['plugins'][plugin]['mgid_xref'][sel[2]]
                    Hosts[host]['plugins'][plugin]['mgids'][mgid]['checked'] = True

        # Rationalize absolute start time ("ta") and relative start time/range ("tr") parameters.
        if (Options['ta']['disabled'] == 'disabled'):
            Options['ta']['value'] = int(Now - (Options['tr']['value'] * 3600.0))

        elif (int(Options['ta']['value'] + (Options['tr']['value'] * 3600.0)) > Now):
            Options['tr']['value'] = float((Now - Options['ta']['value']) / 3600.0)

        # Scan selections array to generate selected graphs.
        Selections = []
        for host in sorted(Hosts.keys()):
            for plugin in sorted(Hosts[host]['plugins'].keys()):
                for mgid in sorted(Hosts[host]['plugins'][plugin]['mgids'].keys()):
                    if Hosts[host]['plugins'][plugin]['mgids'][mgid]['checked']:
                        data_path = MCconfig['DataDir'] + '/' + host + '-' + mgid
                        if PluginConfigs['config'][PluginConfigs['links'][host][plugin]][mgid].has_key('graph_order'):
                            data_sources = PluginConfigs['config'][PluginConfigs['links'][host][plugin]][mgid]['graph_order'].split()
                        else:
                            data_sources = PluginConfigs['datasource'][PluginConfigs['links'][host][plugin]][mgid]

                        if Options['if']['value'] == 'CSV':
                            # Generate a CSV file; start by fetching data.
                            if (Options['ta']['disabled'] == 'disabled'):
                                csv_heading = host + '-' + mgid + '.csv'
                                csv_path = Options['h1']['value'] + '/' + csv_heading
                            else:
                                csv_heading = host + '-' + mgid + '-' + str(Options['ta']['value']) + '-' + str(Options['tr']['value']) + '-' + str(Options['ht']['value']) + 'x' + str(Options['wd']['value']) + '.csv'
                                csv_path = Options['h1']['value'] + '/' + csv_heading
                            Columns = ['Time']
                            Rows = {}
                            for ds in data_sources:
                                Columns += [ds]
                                ds_path = data_path + '-' + ds + '.rrd'
                                if os.path.exists(ds_path):
                                    if PluginConfigs['config'][PluginConfigs['links'][host][plugin]][mgid].has_key(ds + '.draw'):
                                        csv_command = [
                                            'rrdtool',
                                            'fetch',
                                            ds_path,
                                            'AVERAGE',
                                            '--start',
                                            str(Options['ta']['value']),
                                            '--end',
                                            str(Options['ta']['value'] + int(Options['tr']['value'] * 3600)),
                                            ]

                                        p = Popen(csv_command, stdout=PIPE, stderr=PIPE)
                                        items, stderr = p.communicate()
                                        if stderr == '':
                                            items = items.splitlines()

                                            for item in items:
                                                values = item.split()
                                                if len(values) > 1:
                                                    ts = MCutils.StrToInt(values[0].strip(':'))
                                                    if not Rows.has_key(ts):
                                                        Rows[ts] = []

                                                    if values[1] == 'nan':
                                                        Rows[ts] += ['0.0']
                                                    else:
                                                        Rows[ts] += [str(MCutils.StrToFloat(values[1]))]

                            csv = open(MCconfig['ImageDir'] + '/' + csv_path, 'w')
                            csv.write(','.join(Columns) + '\n')
                            for ts in sorted(Rows.keys()):
                                csv.write(str(ts) + ',' + ','.join(Rows[ts]) + '\n')
                            csv.close()

                            Selections += [(csv_heading, csv_path)]
                            # End of CSV Generation.

                        else:
                            # Generate a graph.
                            if Options['if']['value'] == 'SVG':
                                image_format = ('.svg', 'SVG')
                            else:
                                image_format = ('.png', 'PNG')

                            if (Options['ta']['disabled'] == 'disabled'):
                                graph_heading = host + '-' + mgid + image_format[0]
                                graph_path = Options['h1']['value'] + '/' + graph_heading
                            else:
                                graph_heading = host + '-' + mgid + '-' + str(Options['ta']['value']) + '-' + str(Options['tr']['value']) + '-' + str(Options['ht']['value']) + 'x' + str(Options['wd']['value']) + image_format[0]
                                graph_path = Options['h1']['value'] + '/' + graph_heading

                            graph_command = [
                                'rrdtool',
                                'graph',
                                '--font',
                                'TITLE:' + str(Options['ft']['value']) + ':DejaVuSans',
                                '--font',
                                'AXIS:' + str(Options['fa']['value']) + ':DejaVuSansMono',
                                '--font',
                                'UNIT:' + str(Options['fv']['value']) + ':DejaVuSansMono',
                                '--font',
                                'LEGEND:' + str(Options['fs']['value']) + ':DejaVuSansMono',
                                '--font',
                                'WATERMARK:6:DejaVuSansMono',
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
                                str(Options['ta']['value']),
                                ]

    #                        if (Options['tr']['disabled'] != 'disabled'):
                            graph_command += [
                                '--end',
                                str(Options['ta']['value'] + int(Options['tr']['value'] * 3600)),
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
                                image_format[1],
                                ]

                            if PluginConfigs['config'][PluginConfigs['links'][host][plugin]][mgid].has_key('graph_vlabel'):
                                graph_command += [
                                    '--vertical-label',
                                    PluginConfigs['config'][PluginConfigs['links'][host][plugin]][mgid]['graph_vlabel'],
                                    ]

                            if PluginConfigs['config'][PluginConfigs['links'][host][plugin]][mgid].has_key('graph_args'):
                                graph_command += PluginConfigs['config'][PluginConfigs['links'][host][plugin]][mgid]['graph_args'].split()


                            if Options['fs']['value'] > 5:
                                graph_command += [
                                    'COMMENT:           ',
                                    'COMMENT: Cur\:',
                                    'COMMENT:Min\:',
                                    'COMMENT:Avg\:',
                                    'COMMENT:Max\:  \j',
                                    ]

                            ds_lastupdated = 0
                            for ds in data_sources:
                                ds_path = str(data_path + '-' + ds + '.rrd')
                                if os.path.exists(ds_path):
                                    p = Popen(['rrdtool', 'last',  ds_path], stdout=PIPE, stderr=PIPE)
                                    stdout, stderr = p.communicate()
                                    if stderr == '':
                                        last_time = MCutils.StrToInt(stdout)
                                        if last_time > ds_lastupdated:
                                            ds_lastupdated = last_time

                                    ds_prefix = ''
                                    graph_command += [
                                        'DEF:v' + ds + '=' + ds_path + ':42:AVERAGE',
                                        'DEF:a' + ds + '=' + ds_path + ':42:MAX',
                                        'DEF:i' + ds + '=' + ds_path + ':42:MIN',
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
                                ds_path = data_path + '-' + ds + '.rrd'
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
                                        ]

                                    if Options['fs']['value'] > 5:
                                        graph_command += [
                                            'GPRINT:' + ds_prefix + 'v' + ds + ':LAST:%6.2lf%s',
                                            'GPRINT:' + ds_prefix + 'i' + ds + ':MIN:%6.2lf%s',
                                            'GPRINT:' + ds_prefix + 'v' + ds + ':AVERAGE:%6.2lf%s',
                                            'GPRINT:' + ds_prefix + 'a' + ds + ':MAX:%6.2lf%s' + '\\j',
                                            ]

                                    ds_ix += 1

                            if Options['fs']['value'] > 5:
                                graph_command += [
                                    'COMMENT:Last Updated\: ' + '\:'.join(time.ctime(ds_lastupdated).split(':')) + '\\r',
                                    ]
                            else:
                                graph_command += [
                                    'COMMENT:   \\j',
                                    ]

                            graph_command += [
                                'COMMENT:   \\j',
                                ]
                            
#                            debug = open('/tmp/show.log', 'w')
#                            debug.write(str(graph_command))
#                            debug.close()

                            p = Popen(graph_command, stdout=PIPE, stderr=PIPE)
                            stdout, stderr = p.communicate()

                            Selections += [(graph_heading + stderr, graph_path)]
                            # End of Graph Generation.

        return render_to_response('munincollector:templates/show.pt', {
            'request': self.request,
            'PluginConfigs': PluginConfigs,
            'Selections': Selections,
            'Hosts': Hosts,
            'Options': Options,
            })
