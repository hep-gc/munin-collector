from pyramid.response import Response
from pyramid.renderers import render_to_response
from subprocess import PIPE, Popen, STDOUT
import os
import lockfile
import MCutils

os.environ['PATH'] = '/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin'

class DisplayMetrics(object):
    def __init__(self, request):
        self.request = request

    def __call__(self):
        PluginConfigs = self.request.registry.settings['PluginConfigs']
        return render_to_response('munincollector:templates/show.pt', 
            {'project':'Munin-Collector', 'PluginConfigs': PluginConfigs},
            request=self.request)


