import time
import sys
import threading
import requests
import ddddocr
from datetime import datetime, timedelta

#多线程版本

# 线程锁
lock = threading.Lock()
# 设置 headers
headers = {
    'Referer': 'http://yuyue.lib.qlu.edu.cn/home/web/index',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
}


def get_captcha(session):
    lock.acquire()
    try:
        headers['Content-Type'] = 'image/png'
        # 获取验证码
        resp = session.get(
            'http://yuyue.lib.qlu.edu.cn/api.php/check', headers=headers)
        set_cookie = resp.headers['Set-Cookie'][:-8]
        captcha = ddddocr.DdddOcr(show_ad=False).classification(resp.content)
    finally:
        lock.release()
    return set_cookie, captcha


def login(session, set_cookie, library_username, library_password, captcha):
    lock.acquire()
    try:
        headers['Cookie'] = set_cookie
        headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        payload = 'username=' + library_username + \
            '&password=' + library_password + '&verify=' + captcha
        resp = session.post(
            'http://yuyue.lib.qlu.edu.cn/api.php/login', headers=headers, data=payload)
        access_token = resp.json()['data']['_hash_']['access_token']
    finally:
        lock.release()
    return access_token


def get_segment(session, areaID):
    lock.acquire()
    try:
        segment = ''
        resp = session.get(
            'http://yuyue.lib.qlu.edu.cn/api.php/areadays/'+areaID, headers=headers)
        for areaInfo in resp.json()['data']['list']:
            segment = str(areaInfo['id'])
    finally:
        lock.release()
    return segment


def get_time(target_time_hour, target_time_min, booked_day_ID):
    # 获取当前的UTC时间
    utc_time = datetime.utcnow()
    # 计算时差
    time_difference = timedelta(hours=8)  # 北京时间比UTC时间提前8小时
    # 将UTC时间加上时差得到北京时间
    beijing_time = utc_time + time_difference
    # 设置结束时间
    target_time = datetime(
        beijing_time.year, beijing_time.month, beijing_time.day, target_time_hour, target_time_min)
    # 设置预定时间
    booked_day = (
        beijing_time+timedelta(days=booked_day_ID)).strftime('%Y-%#m-%#d')
    return utc_time, beijing_time, target_time, booked_day


def book_seat(session, access_token, segment, library_username, booked_day, areaID, seatID):
    lock.acquire()
    try:
        # 修改headers
        # http://yuyue.lib.qlu.edu.cn/web/seat3?area=19&segment=1558553&day=2023-9-5&startTime=08:30&endTime=22:00
        headers['Referer'] = f'http://yuyue.lib.qlu.edu.cn/web/seat3?area={areaID}&segment={segment}&day={booked_day}&startTime=08:30&endTime=22:00'

        # 准备预约请求的payload
        bookPayload = f'access_token={access_token}&userid={library_username}&segment={segment}&type=1'

        # 发送预约请求
        resp = session.post(
            f'http://yuyue.lib.qlu.edu.cn/api.php/spaces/{seatID}/book', headers=headers, data=bookPayload)
    finally:
        lock.release()
    return resp


def run_script(library_username, library_password, booked_day_ID, areaID, seatID, interval_time, target_time_hour, target_time_min):
    try:
        #
        booked_day_ID = int(booked_day_ID)
        interval_time = int(interval_time)
        target_time_hour = int(target_time_hour)
        target_time_min = int(target_time_min)
        # 设置 session
        session = requests.Session()
        # 获取 cookie captcha
        set_cookie, captcha = get_captcha(
            session)
        # 登录
        access_token = login(session, set_cookie,
                             library_username, library_password, captcha)
        # 获取 segment
        segment = get_segment(session, areaID)

        while True:
            utc_time, beijing_time, target_time, booked_day = get_time(
                target_time_hour, target_time_min, booked_day_ID)
            if beijing_time >= target_time:
                print('到达目标时间')
                break
            resp_result = book_seat(
                session, access_token, segment, library_username, booked_day, areaID, seatID)
            # 打印结果
            result_msg = resp_result.json()['msg']
            msg = f'{threading.current_thread().name}:utc time={utc_time},beijing_time={beijing_time},target_time={target_time},booked_day={booked_day},result={result_msg}'
            lock.acquire()
            try:
                print(msg)
            finally:
                lock.release()
            time.sleep(int(interval_time))
    except Exception as e:
        print(e)
        time.sleep(int(interval_time))
        run_script(library_username, library_password, booked_day_ID,
                   areaID, seatID, interval_time, target_time_hour, target_time_min)


if __name__ == '__main__':
    # 202003040046,qlu170014,1,19,7274,0,23,0\n202003040048,qlu230018,1,19,7274,0,23,0
    argv_inputs = str(sys.argv[1]).splitlines()

    # 创建一个线程列表
    threads = []

    # 遍历每个输入，为每个输入创建并启动一个线程
    for input_str in argv_inputs:
        parse_input_str = input_str.split(',')
        thread = threading.Thread(target=run_script, args=(
            parse_input_str[0], parse_input_str[1], parse_input_str[2], parse_input_str[3], parse_input_str[4], parse_input_str[5], parse_input_str[6], parse_input_str[7]))
        threads.append(thread)
        thread.start()

    # 等待所有线程执行结束
    for thread in threads:
        thread.join()
