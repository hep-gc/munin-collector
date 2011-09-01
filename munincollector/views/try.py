#!/usr/bin/env /usr/bin/python
import ConfigParser
import os
from subprocess import PIPE, Popen, STDOUT
import time

os.environ['PATH'] = '/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin'

config_path = os.path.expanduser('~') + "/.blender-submit.conf"
condor_host = 'elephant07.heprc.uvic.ca'
condor_port = '3121'
movie_viewer = 'vlc'
picture_viewer = 'eog'
text_editor = 'gedit'

submit_parms = []

def StrToInt( str ):
	# convert the given string to an integer.
	try:
		result = int(str)
	except ValueError:
		result = 0
	return result

def main():
    a=[('g', '1_3'), ('g', '1_8')]

    for item in a:
        print item[0] + " " + item[1]
    return;
    hashoffset = len('/tmp/munin-collector/config/data/')
    p = Popen(['ls', '/tmp/munin-collector/config/links'], stdout=PIPE, stderr=PIPE)
    hosts, stderr = p.communicate()
    if stderr == '':
        hosts = hosts.splitlines()
        for host in hosts:
            p = Popen(['ls', '-l', '/tmp/munin-collector/config/links/' + host], stdout=PIPE, stderr=PIPE)
            links, stderr = p.communicate()
            if stderr == '':
                links = links.splitlines()
                for link in links:
                    x = link.split()
                    if len(x) >= 11:
                        a = 0
                #        print host + ' -> ' + x[10][hashoffset:] + ' <- ' + x[8]

    p = Popen(['ls', '/tmp/munin-collector/config/data'], stdout=PIPE, stderr=PIPE)
    plugins, stderr = p.communicate()
    if stderr == '':
        plugins = plugins.splitlines()
        for plugin in plugins:
            plugin_graph = plugin
            plugin_config = open('/tmp/munin-collector/config/data/' + plugin, 'r')
            lines = plugin_config.readlines()
            for line in lines:
                line = line.strip()
                if line == '' or line == '(nil)':
                    continue
                elif line.split(' ', 1)[0] == 'multigraph':
                    plugin_graph = plugin + '_' + line.split(' ', 1)[1]
                    continue
                else:
                    print plugin_graph + ' ' + line.split(' ', 1)[0] + ' ' + line.split(' ', 1)[1]

#	global condor_host, condor_port, movie_viewer, picture_viewer, text_editor
#
#	if os.path.exists(config_path):
#		config_file = ConfigParser.ConfigParser()
#
#		try:
#			config_file.read(config_path)
#		except IOError:
#			print "Configuration file problem: There was a " \
#			"problem reading %s. Check that it is readable," \
#			"and that it exists. " % config_path
#			raise
#		except ConfigParser.ParsingError:
#			print "Configuration file problem: Couldn't " \
#			"parse your file. Check for spaces before or after variables."
#			raise
#		except:
#			print "Configuration file problem: There is something wrong with " \
#			"your config file."
#			raise
#
#		if config_file.has_option("global", "condor_host"):
#			condor_host = config_file.get("global", "condor_host")
#
#		if config_file.has_option("global", "condor_port"):
#			condor_port = config_file.get("global", "condor_port")
#
#		if config_file.has_option("global", "movie_viewer"):
#			movie_viewer = config_file.get("global", "movie_viewer")
#
#		if config_file.has_option("global", "picture_viewer"):
#			picture_viewer = config_file.get("global", "picture_viewer")
#
#		if config_file.has_option("global", "text_editor"):
#			text_editor = config_file.get("global", "text_editor")
#
#	global tk_JobStatus, tk_InputStatus, tk_OutputStatus, tk_StartFrame, tk_EndFrame
#
#	root = Tkinter.Tk()
#
#	tk_JobStatus = Tkinter.StringVar()
#	tk_JobStatus.set('None yet')
#
#	tk_InputStatus = Tkinter.StringVar()
#	tk_InputStatus.set('')
#
#	tk_OutputStatus = Tkinter.StringVar()
#	tk_OutputStatus.set('')
#
#	tk_StartFrame = Tkinter.StringVar()
#	tk_StartFrame.set('1')
#
#	tk_EndFrame = Tkinter.StringVar()
#	tk_EndFrame.set('1')
#
#	Job_Poller = JobPoller()
#	Job_Poller.start()
#
#	Job_Returner = JobReturner()
#	Job_Returner.start()
#
#	Job_Submitter = JobSubmitter()
#	Job_Submitter.start()
#
#	BatchBlender(root).grid()
#	root.mainloop()
#
#	Job_Submitter.stop()
#	Job_Returner.stop()
#	Job_Poller.stop()
#
#	time.sleep(2)
#
main()
