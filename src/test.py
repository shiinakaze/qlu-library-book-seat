import time
import sys
import requests
import ddddocr
from datetime import datetime, timedelta

# 设置 headers
headers = {
    'Referer': 'http://yuyue.lib.qlu.edu.cn/home/web/index',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
}

# 获取验证码


def get_captcha(session):
    headers['Content-Type'] = 'image/png'
    resp = session.get(
        'http://yuyue.lib.qlu.edu.cn/api.php/check', headers=headers)
    set_cookie = resp.headers['Set-Cookie'][:-8]
    captcha = ddddocr.DdddOcr(show_ad=False).classification(resp.content)
    return set_cookie, captcha

# 登录


def login(session, set_cookie, library_username, library_password, captcha):
    headers['Cookie'] = set_cookie
    headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
    payload = 'username=' + library_username + \
        '&password=' + library_password + '&verify=' + captcha
    resp = session.post(
        'http://yuyue.lib.qlu.edu.cn/api.php/login', headers=headers, data=payload)
    access_token = resp.json()['data']['_hash_']['access_token']
    return access_token

# 获取 segment


def get_segment(session, areaID):
    segment = ''
    resp = session.get(
        'http://yuyue.lib.qlu.edu.cn/api.php/areadays/'+areaID, headers=headers)
    for areaInfo in resp.json()['data']['list']:
        segment = str(areaInfo['id'])
    return segment


def get_time(target_time_hour, target_time_min):
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
        beijing_time+timedelta(days=1)).strftime('%Y-%#m-%#d')
    return utc_time, beijing_time, target_time, booked_day


def book_seat(session, access_token, segment, library_username, booked_day, areaID, seatID):

    # 修改headers
    # http://yuyue.lib.qlu.edu.cn/web/seat3?area=19&segment=1558553&day=2023-9-5&startTime=08:30&endTime=22:00
    headers['Referer'] = f'http://yuyue.lib.qlu.edu.cn/web/seat3?area={areaID}&segment={segment}&day={booked_day}&startTime=08:30&endTime=22:00'

    # 准备预约请求的payload
    bookPayload = f'access_token={access_token}&userid={library_username}&segment={segment}&type=1'

    # 发送预约请求
    resp = session.post(
        f'http://yuyue.lib.qlu.edu.cn/api.php/spaces/{seatID}/book', headers=headers, data=bookPayload)

    return resp


def run_script(library_username, library_password,  areaID, seatID, interval_time, target_time_hour, target_time_min):
    try:
        # 强制类型转换
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
                target_time_hour, target_time_min)
            if beijing_time >= target_time:
                print('到达目标时间')
                break
            resp_result = book_seat(
                session, access_token, segment, library_username, booked_day, areaID, seatID)
            # 打印结果
            result_msg = resp_result.json()['msg']
            utc_time = utc_time.strftime('%Y-%m-%d %H:%M:%S')
            beijing_time = beijing_time.strftime('%Y-%m-%d %H:%M:%S')
            target_time = target_time.strftime('%Y-%m-%d %H:%M:%S')
            msg = f'utc time={utc_time},beijing_time={beijing_time},target_time={target_time},booked_day={booked_day},result={result_msg}'
            print(msg)
            time.sleep(interval_time)
    except Exception as e:
        print(e)
        time.sleep(interval_time)
        run_script(library_username, library_password,
                   areaID, seatID, interval_time, target_time_hour, target_time_min)


if __name__ == '__main__':
    # 2020030400xx,qlu1700xx,19,7274,2,23,0
    parse_input_str = str(sys.argv[1]).split(',')
    run_script(parse_input_str[0], parse_input_str[1], parse_input_str[2], parse_input_str[3],
               parse_input_str[4], parse_input_str[5], parse_input_str[6])
