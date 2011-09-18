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
        return Response('debug: ' + str(PluginConfigs['DomainTree']) + '>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>' + str(PluginConfigs['PluginTree']) + '\n')

