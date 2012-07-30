from pyramid.response import Response
from pyramid.renderers import render_to_response
from subprocess import PIPE, Popen, STDOUT
import os
import re
import time
import lockfile
import MCutils

os.environ['PATH'] = '/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin'

Palette = (
#    Greens     Blues   Oranges    Dk yel    Dk blu    Purple      lime      Reds      Gray
    '00CC00', '0066B3', 'FF8000', 'FFCC00', '330099', '990099', 'CCFF00', 'FF0000', '808080',
    '008F00', '00487D', 'B35A00', 'B38F00',           '6B006B', '8FB300', 'B30000', 'BEBEBE',
    '80FF80', '80C9FF', 'FFC080', 'FFE680', 'AA80FF', 'EE00CC', 'FF8080',
    '666600', 'FFBFFF', '00FFCC', 'CC6699', '999900',
    )

def DrawGraphs(MC, PC, Plugins, CheckedBoxes, Options, Selections, UsersIP, plugin, mgid, domain, host):
    if (plugin in Plugins or
        str(PC['PluginXref'].index(plugin)) + '.' + 
        str(PC['MgidXref'].index(mgid)) + '.' +
        str(PC['DomainXref'].index(domain)) + '.' +
        str(PC['HostXref'].index(host)) in CheckedBoxes):

        if not PC['resolved'][PC['links'][host][plugin]]:
            PC['resolved'][PC['links'][host][plugin]] = True

            for r_mgid in PC['config'][PC['links'][host][plugin]].keys():
                for r_key in PC['config'][PC['links'][host][plugin]][mgid].keys():
                    for r_match in re.finditer(r'\${[\w]+}', PC['config'][PC['links'][host][plugin]][mgid][r_key]):
                        r_kw = r_match.group()[2:-1]
                        if PC['config'][PC['links'][host][plugin]][mgid].has_key(r_kw):
                            PC['config'][PC['links'][host][plugin]][mgid][r_key] = PC['config'][PC['links'][host][plugin]][mgid][r_key].replace(r_match.group(), PC['config'][PC['links'][host][plugin]][mgid][r_kw], 1)
                        else:
                            if r_kw == 'graph_period': PC['config'][PC['links'][host][plugin]][mgid][r_key] = PC['config'][PC['links'][host][plugin]][mgid][r_key].replace(r_match.group(), 'second', 1)


        data_path = MC['DataDir'] + '/' + host + '-' + mgid
        if PC['config'][PC['links'][host][plugin]][mgid].has_key('graph_order'):
            data_sources = PC['config'][PC['links'][host][plugin]][mgid]['graph_order'].split()
        else:
            data_sources = PC['datasource'][PC['links'][host][plugin]][mgid]

        if Options['if']['value'] == 'CSV':
            # Generate a CSV file; start by fetching data.
            if ('no-long-names' in MC['Options'] or Options['ta']['disabled'] == 'disabled'):
                csv_heading = host + '-' + mgid + '.csv'
#                csv_path = Options['h1']['value'] + '/' + csv_heading
                csv_path = UsersIP + '/' + csv_heading
            else:
                csv_heading = host + '-' + mgid + '-' + str(Options['ta']['value']) + '-' + str(Options['tr']['value']) + '-' + str(Options['ht']['value']) + 'x' + str(Options['wd']['value']) + '.csv'
#                csv_path = Options['h1']['value'] + '/' + csv_heading
                csv_path = UsersIP + '/' + csv_heading
            Columns = ['Time']
            Rows = {}
            for ds in data_sources:
                Columns += [ds]
                ds_path = data_path + '-' + ds + MCutils.MuninType(PC['config'][PC['links'][host][plugin]][mgid], ds) + '.rrd'
                if os.path.exists(ds_path):
                    if PC['config'][PC['links'][host][plugin]][mgid].has_key(ds + '.draw'):
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

            csv = open(MC['ImageDir'] + '/' + csv_path, 'w')
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

            if ('no-long-names' in MC['Options'] or Options['ta']['disabled'] == 'disabled'):
                graph_heading = host + '-' + mgid + image_format[0]
#                graph_path = Options['h1']['value'] + '/' + graph_heading
                graph_path = UsersIP + '/' + graph_heading
            else:
                graph_heading = host + '-' + mgid + '-' + str(Options['ta']['value']) + '-' + str(Options['tr']['value']) + '-' + str(Options['ht']['value']) + 'x' + str(Options['wd']['value']) + image_format[0]
#                graph_path = Options['h1']['value'] + '/' + graph_heading
                graph_path = UsersIP + '/' + graph_heading

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
                MC['ImageDir'] + '/' + graph_path,
                ]

            if Options['gt']['value'] != '':
                graph_command += [
                    '--title',
                    Options['gt']['value'],
                    ]
            elif PC['config'][PC['links'][host][plugin]][mgid].has_key('graph_title'):
                graph_command += [
                    '--title',
                    PC['config'][PC['links'][host][plugin]][mgid]['graph_title'],
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

            if PC['config'][PC['links'][host][plugin]][mgid].has_key('graph_vlabel'):
                graph_command += [
                    '--vertical-label',
                    PC['config'][PC['links'][host][plugin]][mgid]['graph_vlabel'],
                    ]

            if PC['config'][PC['links'][host][plugin]][mgid].has_key('graph_args'):
                graph_command += PC['config'][PC['links'][host][plugin]][mgid]['graph_args'].split()


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
                ds_path = data_path + '-' + ds + MCutils.MuninType(PC['config'][PC['links'][host][plugin]][mgid], ds) + '.rrd'
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
                    if PC['config'][PC['links'][host][plugin]][mgid].has_key(ds + '.cdef'):
                        ds_prefix = 'x'
                        graph_command += [
                            'CDEF:xv' + ds + '=v' + PC['config'][PC['links'][host][plugin]][mgid][ds + '.cdef'],
                            'CDEF:xa' + ds + '=a' + PC['config'][PC['links'][host][plugin]][mgid][ds + '.cdef'],
                            'CDEF:xi' + ds + '=i' + PC['config'][PC['links'][host][plugin]][mgid][ds + '.cdef'],
                            ]

            ds_ix = 0
            for ds in data_sources:
                ds_path = data_path + '-' + ds + MCutils.MuninType(PC['config'][PC['links'][host][plugin]][mgid], ds) + '.rrd'
                if os.path.exists(ds_path):
                    if PC['config'][PC['links'][host][plugin]][mgid].has_key(ds + '.draw'):
                        ds_draw = PC['config'][PC['links'][host][plugin]][mgid][ds + '.draw']

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

                    if PC['config'][PC['links'][host][plugin]][mgid].has_key(ds + '.colour'):
                        ds_colour = PC['config'][PC['links'][host][plugin]][mgid][ds + '.colour']
                    else:
                        ds_colour = Palette[ds_ix % len(Palette)]

                    ds_label = ds
                    if PC['config'][PC['links'][host][plugin]][mgid].has_key(ds + '.label'):
                        ds_label = PC['config'][PC['links'][host][plugin]][mgid][ds + '.label']

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
            
            if 'lazy' in MC['Options']:
                graph_command += [
                    '--lazy',
                    ]

            p = Popen(graph_command, stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()

            Selections += [(graph_heading + stderr, graph_path)]
            # End of Graph Generation.



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
        # Set parameter defaults. NB: enabled parameters will have a 'disabled' value equal to their parameter name.
        Options = {
#            # Munin graph subdirectory (hidden value)
#            'h1': {'type': 'dir', 'disabled': 'h1', 'value': str(int(Now))},

            # Checkbox selections (hidden value)
            'h2': {'type': 'str', 'disabled': 'h2', 'value': ''},           

            # Current time (hidden value), output only used by javascript. 
            'h3': {'type': 'int', 'disabled': 'disabled', 'value': Now, 'min': 1, 'max': 0},            

            # Absolute start time
            'ta': {'type': 'int', 'disabled': 'disabled', 'value': 0, 'min': int(Now-360000000), 'max': int(Now-1800)},

            # Relative start time/time range
            'tr': {'type': 'flt', 'disabled': 'disabled', 'value': 30, 'min': .5, 'max': 100000},

            # Timeout
            'to': {'type': 'int', 'disabled': 'disabled', 'value': 300, 'min': 10, 'max': 3600},

            # Graph height
            'ht': {'type': 'int', 'disabled': 'disabled', 'value': 100, 'min': 100, 'max': 2400},

            # Graph width
            'wd': {'type': 'int', 'disabled': 'disabled', 'value': 300, 'min': 100, 'max': 2400},

            # Title font size
            'ft': {'type': 'int', 'disabled': 'disabled', 'value': 8, 'min': 6, 'max': 32},

            # Axis font size
            'fa': {'type': 'int', 'disabled': 'disabled', 'value': 8, 'min': 6, 'max': 32},

            # Vertical Label (UNIT) font size
            'fv': {'type': 'int', 'disabled': 'disabled', 'value': 8, 'min': 6, 'max': 32},

            # Statistics (LEGEND) font size
            'fs': {'type': 'int', 'disabled': 'disabled', 'value': 0, 'min': 0, 'max': 32},

            # Graph columns
            'gc': {'type': 'int', 'disabled': 'disabled', 'value': 2, 'min': 1, 'max': 24},

            # Graph title
            'gt': {'type': 'str', 'disabled': 'disabled', 'value': ''},

            # Graph title
            'if': {'type': 'str', 'disabled': 'if', 'value': 'PNG'},

            # Display graphs for a comma separated list of plugins.
            'p': {'type': 'str', 'disabled': 'disabled', 'value': ''},

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

#        # Ensure image sub-directory (h1 parameter) exists.
#        if not os.path.exists(MCconfig['ImageDir'] + "/" + Options['h1']['value']):
#            p = Popen(['mkdir', '-p',  MCconfig['ImageDir'] + '/' + Options['h1']['value']], stdout=PIPE, stderr=PIPE)
#            stdout, stderr = p.communicate()
#            if stderr != '':
#                return Response('munin-collector-show: unable to create image sub-directory.\n')

        # Ensure image sub-directory (uses client's IP address) exists.
        if not os.path.exists(MCconfig['ImageDir'] + "/" + self.request.remote_addr):
            p = Popen(['mkdir', '-p',  MCconfig['ImageDir'] + '/' + self.request.remote_addr], stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()
            if stderr != '':
                return Response('munin-collector-show: unable to create image sub-directory.\n')

        # Process the resource selection (h2) parameter.
        CheckedBoxes = Options['h2']['value'].split('_')

        # Process the plugin selection (p) parameter.
        Plugins = Options['p']['value'].split(',')

        # Rationalize absolute start time ("ta") and relative start time/range ("tr") parameters.
        if (Options['ta']['disabled'] == 'disabled'):
            Options['ta']['value'] = int(Now - (Options['tr']['value'] * 3600.0))

        elif (int(Options['ta']['value'] + (Options['tr']['value'] * 3600.0)) > Now):
            Options['tr']['value'] = float((Now - Options['ta']['value']) / 3600.0)

        # Scan selections array to generate selected graphs.
        Selections = []
        if CheckedBoxes[0] == 'p':
            for plugin in sorted(PluginConfigs['PluginTree'].keys()):
                for mgid in sorted(PluginConfigs['PluginTree'][plugin].keys()):
                    for domain in sorted(PluginConfigs['PluginTree'][plugin][mgid].keys()):
                        for host in sorted(PluginConfigs['PluginTree'][plugin][mgid][domain]):
                            DrawGraphs(MCconfig, PluginConfigs, Plugins, CheckedBoxes, Options, Selections, self.request.remote_addr, plugin, mgid, domain, host)

        else:
            for domain in sorted(PluginConfigs['DomainTree'].keys()):
                for host in sorted(PluginConfigs['DomainTree'][domain].keys()):
                    for plugin in sorted(PluginConfigs['DomainTree'][domain][host].keys()):
                        for mgid in sorted(PluginConfigs['DomainTree'][domain][host][plugin]):
                            DrawGraphs(MCconfig, PluginConfigs, Plugins, CheckedBoxes, Options, Selections, self.request.remote_addr, plugin, mgid, domain, host)

        return render_to_response('munincollector:templates/show.pt', {
            'request': self.request,
            'DT': PluginConfigs['DomainTree'],
            'PT': PluginConfigs['PluginTree'],
            'DX': PluginConfigs['DomainXref'],
            'HX': PluginConfigs['HostXref'],
            'PX': PluginConfigs['PluginXref'],
            'MX': PluginConfigs['MgidXref'],
            'Selections': Selections,
            'Options': Options,
            })
#            'Hosts': Hosts,
#            'PluginConfigs': PluginConfigs,
