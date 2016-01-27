from pyramid.config import Configurator
from munincollector.resources import Root
from subprocess import PIPE, Popen, STDOUT
from stat import *
import ConfigParser
import MCutils
import os
import glob
import cPickle

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    # Read and process our configuration file.
    ConfigurationFile = '/usr/local/etc/munin-collector.conf'
    if not os.path.exists(ConfigurationFile):
        ConfigurationFile = global_config['here'] + '/munincollector/samples/etc/munin/munin-collector.conf'

    AllowedDomains = []
    HostAllowed = {}
    Options = []

    if not os.path.exists(ConfigurationFile):
        print "Configuration file '%s' does not exist." % ConfigurationFile
        quit()
    else:
        config_file = ConfigParser.ConfigParser()

        try:
            config_file.read(ConfigurationFile)
        except IOError:
            print "Configuration file problem: There was a " \
            "problem reading %s. Check that it is readable," \
            "and that it exists. " % ConfigurationFile
            quit()
        except ConfigParser.ParsingError:
            print "Configuration file problem: Couldn't " \
            "parse your file. Check for spaces before or after variables."
            quit()
        except:
            print "Configuration file problem: There is something wrong with " \
            "your config file."
            quit()

        if config_file.has_option("munin-collector", "DataDir"):
            DataDir = config_file.get("munin-collector", "DataDir")
        else:
            print "Configuration file did not specify a path for 'DataDir'."
            quit()

        if config_file.has_option("munin-collector", "ImageDir"):
            ImageDir = config_file.get("munin-collector", "ImageDir")
        else:
            print "Configuration file did not specify a path for 'ImageDir'."
            quit()

        if config_file.has_option("munin-collector", "LockDir"):
            LockDir = config_file.get("munin-collector", "LockDir")
        else:
            print "Configuration file did not specify a path for 'LockDir'."
            quit()

        if config_file.has_option("munin-collector", "LogLevel"):
            LogLevel = int(config_file.get("munin-collector", "LogLevel"))
        else:
            print "Configuration file did not specify a value for 'LogLevel'."
            quit()

        if config_file.has_option("munin-collector", "PluginDir"):
            PluginDir = config_file.get("munin-collector", "PluginDir")
        else:
            print "Configuration file did not specify a path for 'PluginDir'."
            quit()

        if config_file.has_option("munin-collector", "Domains"):
            domain_string = config_file.get("munin-collector", "Domains")

            domains = domain_string.split(',')
            for domain in domains:
                words = domain.strip().split('/')
                if len(words) < 1 or len(words) > 2:
                    print "Domains contained an invalid specification: '%s' - too many '/'s." % domain
                    quit()

                if ':' in words[0]:
                    partitions = words[0].partition('::')
                    nibbles_1 =  partitions[0].split(':')
                    if partitions[1] == '::':
                        nibbles_2 =  partitions[2].split(':')
                    nibble_bits = 16
                    nibble_count = 8
                else:
                    nibbles_1 = words[0].split('.')
                    nibbles_2 = ()
                    nibble_bits = 8
                    nibble_count = 4

                if len(words) == 1:
                    subnet_bits = nibble_bits * nibble_count
                else:
                    subnet_bits = MCutils.StrToInt(words[1])

                if len(nibbles_1) + len(nibbles_2) > nibble_count:
                    print "Domains contained an invalid specification: '%s' - too many octets/hextets." % domain
                    quit()

                if subnet_bits > nibble_bits * nibble_count:
                    print "Domains contained an invalid specification: '%s' - too many subnet bits." % domain
                    quit()

                host_bits = (nibble_bits * nibble_count) - subnet_bits
                max_domain_host_count = (2 ** host_bits)

                domain_min_ip_1 = 0
                for ix in range(nibble_count):
                    domain_min_ip_1 = domain_min_ip_1 * (2 ** nibble_bits)
                    if len(nibbles_1) > ix:
                        domain_min_ip_1 += MCutils.StrToInt(nibbles_1[ix])

                domain_min_ip_2 = 0
                for ix in range(len(nibbles_2)):
                    domain_min_ip_2 = domain_min_ip_2 * (2 ** nibble_bits)
                    domain_min_ip_2 += MCutils.StrToInt(nibbles_2[ix])

                domain_min_ip = int((domain_min_ip_1 + domain_min_ip_2) / max_domain_host_count) * max_domain_host_count
                domain_max_ip = domain_min_ip + (2 ** host_bits) - 1
                AllowedDomains += [(domain_min_ip, domain_max_ip)]

            AllowedDomains = sorted(AllowedDomains)

        if config_file.has_option("munin-collector", "Options"):
            option_string = config_file.get("munin-collector", "Options")

            options = option_string.split(',')
            for option in options:
                option = option.strip()
                if not option in Options:
                    Options += [option]

            Options = sorted(Options)

    # Ensure that each required directory exists.
    p = Popen(['mkdir', '-p', DataDir], stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()

    p = Popen(['mkdir', '-p', ImageDir], stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()

    p = Popen(['mkdir', '-p', LockDir], stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()

    p = Popen(['mkdir', '-p', PluginDir + '/config'], stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()

    p = Popen(['mkdir', '-p', PluginDir + '/links'], stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()

    p = Popen(['mkdir', '-p', PluginDir + '/pickles'], stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()

    MCconfig = {
        'DataDir': DataDir,
        'ImageDir': ImageDir,
        'LockDir': LockDir,
        'LogLevel': LogLevel,
        'PluginDir': PluginDir,
        'AllowedDomains': AllowedDomains,
        'HostAllowed': HostAllowed,
        'Options': Options,
        }

    MCutils.Logger(MCconfig, 3, '__init__', 'Started.')
    MCutils.Logger(MCconfig, 3, '__init__', 'Configuration:')
    MCutils.Logger(MCconfig, 3, '__init__', '   AllowedDomains : ' + str(MCconfig['AllowedDomains']))
    MCutils.Logger(MCconfig, 3, '__init__', '   DataDir        : ' + MCconfig['DataDir'])
    MCutils.Logger(MCconfig, 3, '__init__', '   HostAllowed    : ' + str(MCconfig['HostAllowed']))
    MCutils.Logger(MCconfig, 3, '__init__', '   ImageDir       : ' + MCconfig['ImageDir'])
    MCutils.Logger(MCconfig, 3, '__init__', '   LockDir        : ' + MCconfig['LockDir'])
    MCutils.Logger(MCconfig, 3, '__init__', '   LogLevel       : ' + str(MCconfig['LogLevel']))
    MCutils.Logger(MCconfig, 3, '__init__', '   Options        : ' + str(MCconfig['Options']))
    MCutils.Logger(MCconfig, 3, '__init__', '   PluginDir      : ' + MCconfig['PluginDir'])

    # Initialize plugin configuration cache.
    PluginConfigs = cPickle.load( open( MCconfig['PluginDir'] + '/pickles/PluginConfigs', "rb" ) )
    PluginConfigs['Timestamp'] = os.stat(MCconfig['PluginDir'] + '/pickles/PluginConfigs').st_mtime

    # Initialize statistics activity cache.
    StatisticsActivity = cPickle.load( open( MCconfig['PluginDir'] + '/pickles/StatisticsActivity', "rb" ) )
    StatisticsActivity['Timestamp'] = os.stat(MCconfig['PluginDir'] + '/pickles/StatisticsActivity').st_mtime

    config = Configurator(root_factory=Root, settings=settings)
    config.include('pyramid_chameleon')
    config.add_settings({'MCconfig': MCconfig})
    config.add_settings({'PluginConfigs': PluginConfigs})
    config.add_settings({'StatisticsActivity': StatisticsActivity})
    config.add_view('munincollector.views.alive.Check', name='alive')
    config.add_view('munincollector.views.config.ReadConfig', name='config')
    config.add_view('munincollector.views.debug.ShowValues', name='debug')
    config.add_view('munincollector.views.show.DisplayMetrics')
    config.add_view('munincollector.views.value.ReadValue', name='value')
    config.add_static_view('static', 'munincollector:static')
    return config.make_wsgi_app()

