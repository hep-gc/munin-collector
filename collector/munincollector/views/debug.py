from pyramid.response import Response
from subprocess import PIPE, Popen, STDOUT
import os
import re
import lockfile
import MCutils

os.environ['PATH'] = '/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin'

class ShowValues(object):
    def __init__(self, request):
        self.request = request

    def __call__(self):
        MCconfig = self.request.registry.settings['MCconfig']
        Params = self.request.params
        PluginConfigs = self.request.registry.settings['PluginConfigs']

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

        return Response(DT + PT + DX + HX + PX + MX + '\n')

