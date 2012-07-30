#!/usr/bin/perl
#
# 	Set command paths.
#
	$ENV{'PATH'} = '/bin:/usr/bin:/usr/local/bin:/sbin:/usr/sbin:/usr/local/sbin';

#
#       Check that the current directory is where the munin-redis package resides.
#
	if (!(-e 'bin/munin-node-redis')) {
		print "INSTALL-munin-node: You need to change directory to where the munin-redis package resides.\n";
		exit;
	}

#
# 	Check for prerequisites.
#
	@x = `rpm -qa | grep 'redis'`;
	if ($#x < 0) {
		print "INSTALL-munin-node: You need to install redis.\n";
		exit;
	}

	@x = `rpm -qa | grep 'munin-node-1.4'`;
	if ($#x < 0) {
		print "INSTALL-munin-node: You need to install munin-node-1.4.\n";
		exit;
	}

#
# 	Ensure we're running as root.
#
        if (`whoami` ne "root\n") {
			print "INSTALL-munin-node: MUST be run as user 'root'.\n";
			exit;
		}

#
#	Install the files.
#
	system('cp bin/munin-node-redis /usr/sbin/');
	system('cp cron/munin-node-redis /etc/cron.d/');
	system('cp etc/munin-node-redis.conf /etc/munin/') if !(-e '/etc/munin/munin-node-redis.conf');

