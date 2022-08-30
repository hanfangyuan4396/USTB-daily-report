ps -ef | grep ustb_report | grep -v grep | awk '{print $2}' | xargs kill -9
ps -ef | grep ustb_report
