from pyramid.response import Response
from subprocess import PIPE, Popen, STDOUT
import os
import re
import time
import lockfile
import MCutils
import cPickle

os.environ['PATH'] = '/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin'

class ShowValues(object):
    def __init__(self, request):
        self.request = request

    def __call__(self):
        MCconfig = self.request.registry.settings['MCconfig']
        Params = self.request.params
        PluginConfigs = self.request.registry.settings['PluginConfigs']
        StatisticsActivity = self.request.registry.settings['StatisticsActivity']

        # ensure the plugin configuration cache is up to date.
        if MCutils.ReloadPluginConfig(MCconfig, PluginConfigs):
            PluginConfigs = cPickle.load( open( MCconfig['PluginDir'] + '/pickles/PluginConfigs', "rb" ) )
            PluginConfigs['Timestamp'] = os.stat(MCconfig['PluginDir'] + '/pickles/PluginConfigs').st_mtime

        # ensure the statistics activity cache is up to date.
        if MCutils.ReloadStatisticsActivity(MCconfig, StatisticsActivity):
            StatisticsActivity = cPickle.load( open( MCconfig['PluginDir'] + '/pickles/StatisticsActivity', "rb" ) )
            StatisticsActivity['Timestamp'] = os.stat(MCconfig['PluginDir'] + '/pickles/StatisticsActivity').st_mtime

        # Format the plugin links: {host: {plugin: hash, ... }, ... }
        PL = '<br/><br/>PluginConfigs[\'links\']:'
        for host in PluginConfigs['links']:
            PL += '<br/>' + \
                  '&nbsp&nbsp&nbsp&nbsp' + \
                  host 
            for plugin in PluginConfigs['links'][host]:
                PL += '<br/>' + \
                      '&nbsp&nbsp&nbsp&nbsp' + \
                      '&nbsp&nbsp&nbsp&nbsp' + \
                      plugin + ' = ' + PluginConfigs['links'][host][plugin]

        # Format the mgid config: {hash: {mgid: {key: value, ... }, ... }, ... }
        PC = '<br/><br/>PluginConfigs[\'config\']:'
        for hash in PluginConfigs['config']:
            PC += '<br/>' + \
                  '&nbsp&nbsp&nbsp&nbsp' + \
                  hash 
            for mgid in PluginConfigs['config'][hash]:
                PC += '<br/>' + \
                      '&nbsp&nbsp&nbsp&nbsp' + \
                      '&nbsp&nbsp&nbsp&nbsp' + \
                      mgid
                for key in PluginConfigs['config'][hash][mgid]:
                    PC += '<br/>' + \
                          '&nbsp&nbsp&nbsp&nbsp' + \
                          '&nbsp&nbsp&nbsp&nbsp' + \
                          '&nbsp&nbsp&nbsp&nbsp' + \
                          key + ' = ' + PluginConfigs['config'][hash][mgid][key]

        # Format the domain tree: {domain: {host: {plugin: [mgid, ...], ... }, ... }, ... }
        DT = '<br/><br/>PluginConfigs[\'DomainTree\'] ->'
        for domain in PluginConfigs['DomainTree']:
            DT += '<br/>' + \
                  '&nbsp&nbsp&nbsp&nbsp' + \
                  domain + ':'
            for host in PluginConfigs['DomainTree'][domain]:
                DT += '<br/>' + \
                      '&nbsp&nbsp&nbsp&nbsp' + \
                      '&nbsp&nbsp&nbsp&nbsp' + \
                      host + ':'
                for plugin in PluginConfigs['DomainTree'][domain][host]:
                    DT += '<br/>' + \
                          '&nbsp&nbsp&nbsp&nbsp' + \
                          '&nbsp&nbsp&nbsp&nbsp' + \
                          '&nbsp&nbsp&nbsp&nbsp' + \
                          plugin + ':'
                    for mgid in PluginConfigs['DomainTree'][domain][host][plugin]:
                        DT += '<br/>' + \
                              '&nbsp&nbsp&nbsp&nbsp' + \
                              '&nbsp&nbsp&nbsp&nbsp' + \
                              '&nbsp&nbsp&nbsp&nbsp' + \
                              '&nbsp&nbsp&nbsp&nbsp' + \
                              mgid

        # Format the plugin tree: {plugin: {mgid: {domain: [host, ...], ... }, ... }, ... }
        PT = '<br/><br/>PluginConfigs[\'PluginTree\'] ->'
        for plugin in PluginConfigs['PluginTree']:
            PT += '<br/>' + \
                  '&nbsp&nbsp&nbsp&nbsp' + \
                  plugin + ':'
            for mgid in PluginConfigs['PluginTree'][plugin]:
                PT += '<br/>' + \
                      '&nbsp&nbsp&nbsp&nbsp' + \
                      '&nbsp&nbsp&nbsp&nbsp' + \
                      mgid + ':'
                for domain in PluginConfigs['PluginTree'][plugin][mgid]:
                    PT += '<br/>' + \
                          '&nbsp&nbsp&nbsp&nbsp' + \
                          '&nbsp&nbsp&nbsp&nbsp' + \
                          '&nbsp&nbsp&nbsp&nbsp' + \
                          domain + ':'
                    for host in PluginConfigs['PluginTree'][plugin][mgid][domain]:
                        PT += '<br/>' + \
                              '&nbsp&nbsp&nbsp&nbsp' + \
                              '&nbsp&nbsp&nbsp&nbsp' + \
                              '&nbsp&nbsp&nbsp&nbsp' + \
                              '&nbsp&nbsp&nbsp&nbsp' + \
                              host

        # Format the domain cross reference: [domain, ...]
        S1 = '<br/><br/>PluginConfigs[\'Timestamps\'][\'s1\'] = ' + str(sorted(PluginConfigs['Timestamps']['s1']))

        # Format the domain cross reference: [domain, ...]
        S2 = '<br/><br/>PluginConfigs[\'Timestamps\'][\'s2\'] = ' + str(sorted(PluginConfigs['Timestamps']['s2']))

        # Format the domain cross reference: [domain, ...]
        ix = 0
        DX = '<br/><br/>PluginConfigs[\'DomainXref\'] ->'
        for domain in PluginConfigs['DomainXref']:
            DX += '<br/>' + \
                  '&nbsp&nbsp&nbsp&nbsp' + \
                  '%04d' % ix + ' - ' + \
                  domain
            ix += 1

        # Format the host cross reference: [host, ...]
        ix = 0
        HX = '<br/><br/>PluginConfigs[\'HostXref\'] ->'
        for host in PluginConfigs['HostXref']:
            HX += '<br/>' + \
                  '&nbsp&nbsp&nbsp&nbsp' + \
                  '%04d' % ix + ' - ' + \
                  host
            ix += 1

        # Format the plugin cross reference: [plugin, ...]
        ix = 0
        PX = '<br/><br/>PluginConfigs[\'PluginXref\'] ->'
        for plugin in PluginConfigs['PluginXref']:
            PX += '<br/>' + \
                  '&nbsp&nbsp&nbsp&nbsp' + \
                  '%04d' % ix + ' - ' + \
                  plugin
            ix += 1

        # Format the mgid cross reference: [mgid, ...]
        ix = 0
        MX = '<br/><br/>PluginConfigs[\'MgidXref\'] ->'
        for mgid in PluginConfigs['MgidXref']:
            MX += '<br/>' + \
                  '&nbsp&nbsp&nbsp&nbsp' + \
                  '%04d' % ix + ' - ' + \
                  mgid
            ix += 1

        # Format time ranges
        TR = '<br/><br/>TimeRanges:'
        for tr in sorted(StatisticsActivity['TimeRanges'].keys()):
            TR += '<br/>' + \
                  '&nbsp&nbsp&nbsp&nbsp' + \
                  '%12d' % StatisticsActivity['TimeRanges'][tr][0] + \
                  '&nbsp' + \
                  '%12d' % StatisticsActivity['TimeRanges'][tr][1] + \
                  '&nbsp' + \
                  tr

        # Format timestamps
        current_time = int(time.time())
        plugin_config_time = int(PluginConfigs['Timestamp']) - current_time
        statistics_activity_time = int(StatisticsActivity['Timestamp']) - current_time
        TS = '<br/><br/>Timestamps: ' + \
             '%12d' % current_time + ', ' + \
             '%12d' % plugin_config_time + ', ' + \
             '%12d' % statistics_activity_time

        return Response(PL + PC + DT + PT + S1 + S2 + DX + HX + PX + MX + TR + TS + '\n')

