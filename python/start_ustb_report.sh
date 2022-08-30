nohup /home/hfy/miniconda3/envs/ustb_report/bin/python -u /home/hfy/USTB-daily-report/python/ustb_report.py $1 >> ustb_report.log 2>&1 &
ps -ef | grep ustb_report

