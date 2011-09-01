from pyramid.response import Response
def put(request):
	method = request.method
	if ('host' in request.params.keys() and
		'plugin' in request.params.keys() and
		'time' in request.params.keys() and
		'data' in request.params.keys()): 
		host = request.params['host']
		plugin = request.params['plugin']
		time = request.params['time']
		data = request.params['data']
		return Response('value ' + method + ', ' + host + ', ' + plugin + ', ' + time + ', ' + data)
	else:
		return Response('Bad "value" parameters.')

