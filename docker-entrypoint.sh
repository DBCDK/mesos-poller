#!/bin/bash

set -e

shopt -s nullglob

if [ -d /docker-entrypoint-confd.d ]; then
	for script in /docker-entrypoint-confd.d/*.sh; do
    	echo "===> Executing confd script " $script
		$script
	done
fi

exec python3 /var/lib/mpoller/mesos-poller.py -d /var/lib/mpoller/ --port $HTTP_PORT --user $USER --password $PASSWORD

