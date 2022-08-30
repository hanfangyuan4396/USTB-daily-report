ps -ef | grep ustb_report | grep -v grep | grep -v deploy | awk '{print $2}' | xargs kill -9
ps -ef | grep ustb_report
