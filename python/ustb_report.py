import re
import time
import random
import configparser
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from wechat_api import wechat_api


url='https://isport.ustb.edu.cn/app.RSPWxClient/index.jsp'
#添加请求头
headers = {
    'X-Requested-With': 'XMLHttpRequest',
    'Cookie': 'JSESSIONID=1630476FC222D8D6C613426330495C15'
}

def str_to_dict(data_str):
    data_list = data_str.split('&')
    data_dict = {}
    for item in data_list:
        key, vaule = item.split('=')
        data_dict[key] = vaule
    return data_dict

config_parser = configparser.ConfigParser()
config_parser.read(filenames='users.ini', encoding='utf-8')
user_list = []
for section in config_parser.sections():
    user_dict = {}
    user_dict['name'] = section
    user_dict['cookie'] = config_parser[section]['cookie']
    user_dict['data'] = str_to_dict(config_parser[section]['data'])
    user_list.append(user_dict)
print(user_list)

def ping():
    retry_number = 0
    while retry_number < max_retry:
        try:
            requests.get(url, headers=headers)
            break
        except:
            print('Ping failed.')
            retry_number += 1
    
    if retry_number >= max_retry:
        wechat_api.send_text_message('ping', 'ping failed')
        

random_delay = True
max_retry = 5
max_delay = 5 # minutes
retry_interval = 20 # seconds
debug = False

def one_submit(user_dict):
    if random_delay:
        delay_minutes = random.randint(0, max_delay)
        print(f'Delay for {delay_minutes} minutes.')
        time.sleep(delay_minutes * 60)
    try:
        response = requests.post(url, headers={'Cookie':user_dict['cookie']}, data=user_dict['data'])
        message = re.search(r'.*"message":\s*"(?P<message>.*?)"', response.text).group('message')
        print(message)
        wechat_api.send_text_message('submit', message, touser=user_dict['name'])
        return message == '当天已上报You have submitted today.'
    except:
        print('Submit failed.')
        return False

def submit():
    for user_dict in user_list:
        retry_number = 0
        while retry_number < max_retry:
            if one_submit(user_dict):
                break
            else:
                global random_delay
                random_delay = False
                print(f'Retry will be run after {retry_interval} seconds.')
                time.sleep(retry_interval)
                retry_number += 1

        if retry_number >= max_retry:
            wechat_api.send_text_message('submit', 'submit failed')

if __name__ == '__main__':
    if debug:
        random_delay = False
        retry_interval = 2
    scheduler = BlockingScheduler(timezone="Asia/Shanghai")
    wechat_api.send_text_message('test', 'test')
    scheduler.add_job(ping, 'cron', minute='*/10')
    scheduler.add_job(submit, 'cron', hour=20, minute=0)
    # scheduler.start()