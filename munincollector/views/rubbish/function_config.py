from pyramid.response import Response
from subprocess import PIPE, Popen, STDOUT
import os

os.environ['PATH'] = '/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin'

mc = '/tmp/munin-collector/'

def put(request):
	method = request.method
	if ('host' in request.params.keys() and
		'plugin' in request.params.keys() and
		'hash' in request.params.keys() and
		'sequence' in request.params.keys() and
		'data' in request.params.keys()): 
		host = request.params['host']
		plugin = request.params['plugin']
		hash = request.params['hash']
		sequence = request.params['sequence']
		data = request.params['data']

		p = Popen(['ln', '-s', '-f', mc + 'config/data/' + hash, mc + 'config/links/' + host + '-' + plugin], stdout=PIPE, stderr=PIPE)
		stdout, stderr = p.communicate()
		if stderr == '':
			i = StrToInt(sequence)
			if i < 1:
				if os.path.exists(mc + 'config/data/' + hash):
					return Response('munin-collector-config: config already saved.\n')
				else:
					mode = 'w'
			else:
					mode = 'a'
			file = open(mc + 'config/data/' + hash, mode)
			file.write(data + '\n')
			file.close()
			return Response('OK\n')
		else:
			return Response('munin-collector-config: unable to link.\n')
	else:
		return Response('munin-collector-config: missing parameters.\n')

def StrToInt( str ):
	# convert the given string to an integer.
	try:
		result = int(str)
	except ValueError:
		result = 0
	return result


