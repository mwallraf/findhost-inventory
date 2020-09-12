## Docker entrypoint to create the crontab scheduler

#!/bin/bash

# Start the run once job.
echo "Docker container has been started"

# Setup a cron schedule
echo "0 6 * * * cd /opt/findhost-inventory && /bin/bash /opt/findhost-inventory/findhost-populate.sh --collect --consolidate run >> /var/log/cron.log 2>&1
0 18 * * * cd /opt/findhost-inventory && /bin/bash /opt/findhost-inventory/findhost-populate.sh archive >> /var/log/cron.log 2>&1
@weekly rm -rf /var/log/cron.log; rm -rf /opt/findhost-inventory/log/*
# This extra line makes it a valid cron" > scheduler.txt

crontab scheduler.txt
crond -f
