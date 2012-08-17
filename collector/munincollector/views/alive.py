from pyramid.response import Response
from subprocess import PIPE, Popen, STDOUT
import os
import re
import lockfile
import MCutils

os.environ['PATH'] = '/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin'

class Check(object):
    def __init__(self, request):
        self.request = request

    def __call__(self):
        return Response('OK')

