#!/usr/bin/perl
#
# 	Set command paths.
#
	$ENV{'PATH'} = '/bin:/usr/bin:/usr/local/bin:/sbin:/usr/sbin:/usr/local/sbin';

#
#       Check that the current directory is where the munin-reporter package resides.
#
	if (!(-e 'bin/munin-node-reporter')) {
		print "INSTALL.sh: You need to change directory to where the munin-reporter package resides.\n";
		exit;
	}

#
# 	Check for prerequisites.
#
	@x = `rpm -qa | grep 'redis'`;
	if ($#x < 0) {
		print "INSTALL.sh: You need to install redis.\n";
		exit;
	}

	@x = `rpm -qa | grep 'munin-node-1.4'`;
	if ($#x < 0) {
		print "INSTALL.sh: You need to install munin-node-1.4.\n";
		exit;
	}

#
# 	Ensure we're running as root.
#
        if (`whoami` ne "root\n") {
			print "INSTALL.sh: MUST be run as user 'root'.\n";
			exit;
		}

#
#	Install the files.
#
	system('cp bin/munin-node-redis /usr/local/sbin/');
	system('cp cron/munin-node-redis /etc/cron.d/');
	system('cp etc/munin-node-redis.conf /usr/local/etc/ if !(-e '/usr/local/etc/munin-node-redis.conf');

	system('cp bin/munin-node-reporter /usr/local/sbin/');
	system('cp cron/munin-node-reporter /etc/cron.d/');
	system('cp etc/munin-node-reporter.conf /usr/local/etc/ if !(-e '/usr/local/etc/munin-node-reporter.conf');

