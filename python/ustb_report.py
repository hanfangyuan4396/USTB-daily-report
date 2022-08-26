import re
import sys
import time
import datetime
import random
import configparser
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from wechat_api import wechat_api

config_parser = configparser.ConfigParser()
config_parser.read(filenames='config.ini')
submit_url = config_parser['ustb_report']['submit_url']
ping_url = config_parser['ustb_report']['ping_url']
debug = bool(int(sys.argv[1]))
random_delay = bool(int(config_parser['ustb_report']['random_delay']))
max_retry = int(config_parser['ustb_report']['max_retry'])
max_delay = int(config_parser['ustb_report']['max_delay'])
retry_interval = int(config_parser['ustb_report']['retry_interval'])

def str_to_dict(data_str):
    data_list = data_str.split('&')
    data_dict = {}
    for item in data_list:
        key, vaule = item.split('=')
        data_dict[key] = vaule
    return data_dict

def add_time(s):
    return f"{datetime.datetime.now().strftime('%m-%d %H:%M:%S')} {s}"

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
        if user_dict['name'] == 'AQiuachooo':
            continue
        retry_number = 0
        while retry_number < max_retry:
            try:
                response = requests.get(ping_url, headers={'Cookie':user_dict['cookie']})
                match_result = re.search('体温', response.text)
                if match_result is None:
                    wechat_api.send_text_message(f"{user_dict['name']} ping", f'session过期或响应异常\n{response.text}', touser="HanFangYuan")
                break
            except Exception as e:
                print('Ping failed.')
                print('excetion:', e)
                retry_number += 1
        
        if retry_number >= max_retry:
            wechat_api.send_text_message(f"{user_dict['name']} ping", 'connect failed', touser="HanFangYuan")

def one_submit(user_dict):
    if random_delay:
        delay_minutes = random.randint(0, max_delay)
        print(f'Delay for {delay_minutes} minutes.')
        time.sleep(delay_minutes * 60)
    try:
        response = requests.post(submit_url, headers={'Cookie':user_dict['cookie']}, data=user_dict['data'])
        print('submit_response:', response.text)
        #message = re.search(r'.*"message":\s*"(?P<message>.*?)"', response.text).group('message')
        return response.text == ''
    except Exception as e:
        print('Submit failed.')
        print('exception:', e)
        return False

def submit():
    for user_dict in get_user_list():
        # data中有null标志的不用填报
        if user_dict['data'].get('null') == 'null':
            continue
        retry_number = 0
        while retry_number < max_retry:
            if one_submit(user_dict):
                wechat_api.send_text_message(f"{user_dict['name']} submit", f"{add_time('自动上报成功')}", touser="HanFangYuan")
                break
            else:
                global random_delay
                # random_delay = False # 由于是全局变量，更改为False之后，就不能改回来了
                print(f'Retry will be run after {retry_interval} seconds.')
                time.sleep(retry_interval)
                retry_number += 1

        if retry_number >= max_retry:
            wechat_api.send_text_message(f"{user_dict['name']} submit", f"{add_time('自动上报失败')}", touser="HanFangYuan")

def reminder():
    for user_dict in get_user_list():
        report_link = f'<a href="{ping_url}">点击填写平安报</a>'
        response = requests.get(ping_url, headers={'Cookie': user_dict['cookie']})
        disabled_list = re.findall('disabled', response.text)
        # 测试发现，如果上报了，会有100多个带有disabled标志的标签
        # 但是session过期也匹配不到，也会提醒
        if len(disabled_list) < 50:
            wechat_api.send_text_message(f"{user_dict['name']} reminder", f"{add_time('今天还未上报')}\n{report_link}")
        # else:
        #     wechat_api.send_text_message(f"{user_dict['name']} reminder", f"{add_time('今天已经上报')}", touser="HanFangYuan")

if __name__ == '__main__':
    if debug:
        random_delay = False
        retry_interval = 2
        ping()
        submit()
        #reminder()
    else:
        scheduler = BlockingScheduler(timezone="Asia/Shanghai")
        scheduler.add_job(ping, 'cron', minute='*/10')
        scheduler.add_job(submit, 'cron', hour=9, minute=0)
        #scheduler.add_job(reminder, 'cron', hour=9, minute=0)
        scheduler.start()
