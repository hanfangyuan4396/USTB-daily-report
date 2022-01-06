import re
import time
import datetime
import random
import configparser
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from wechat_api import wechat_api


url='https://isport.ustb.edu.cn/app.RSPWxClient/index.jsp'

def str_to_dict(data_str):
    data_list = data_str.split('&')
    data_dict = {}
    for item in data_list:
        key, vaule = item.split('=')
        data_dict[key] = vaule
    return data_dict

def get_user_list():
    config_parser = configparser.ConfigParser()
    config_parser.read(filenames='users.ini', encoding='utf-8')
    user_list = []
    for section in config_parser.sections():
        user_dict = {}
        user_dict['name'] = section
        user_dict['cookie'] = config_parser[section]['cookie']
        user_dict['data'] = str_to_dict(config_parser[section]['data'])
        user_list.append(user_dict)
    return user_list

def ping():
    for user_dict in get_user_list():
        retry_number = 0
        while retry_number < max_retry:
            try:
                requests.get(url, headers={'Cookie':user_dict['cookie']})
                break
            except:
                print('Ping failed.')
                retry_number += 1
        
        if retry_number >= max_retry:
            wechat_api.send_text_message(f"{user_dict['name']} ping", 'ping failed')
        

random_delay = True
max_retry = 5
max_delay = 5 # minutes
retry_interval = 20 # seconds
debug = True

def one_submit(user_dict):
    if random_delay:
        delay_minutes = random.randint(0, max_delay)
        print(f'Delay for {delay_minutes} minutes.')
        time.sleep(delay_minutes * 60)
    try:
        response = requests.post(url, headers={'Cookie':user_dict['cookie']}, data=user_dict['data'])
        message = re.search(r'.*"message":\s*"(?P<message>.*?)"', response.text).group('message')
        print(message)
        return message == '当天已上报You have submitted today.'
    except:
        print('Submit failed.')
        return False

def submit():
    for user_dict in get_user_list():
        retry_number = 0
        while retry_number < max_retry:
            if one_submit(user_dict):
                wechat_api.send_text_message(f"{user_dict['name']} submit", f'{datetime.datetime.now()} submit succeeded')
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
    scheduler.add_job(ping, 'cron', minute='*/10')
    scheduler.add_job(submit, 'cron', hour=21, minute=38)
    scheduler.start()