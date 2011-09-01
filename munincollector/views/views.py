def my_view(request):
    return {'project':'Munin-Collector', 'request': request.registry.settings['PluginConfigs']}
