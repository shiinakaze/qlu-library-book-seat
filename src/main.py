import time
import sys
import requests
import ddddocr
from datetime import datetime, timedelta
# 预约天数
# 当天为 0
# 第二天为 1
booked_date = 1
# 设置区域ID
areaID = '19'

# 设置座位ID
seatID = '7274'

# 设置访问间隔时间(s)
interval_time = 1

# 设置目标结束时间
target_time_hour = 6
target_time_min = 1


def run_script_directly(library_username, library_password):
    try:
        # 设置 headers
        headers = {
            'Referer': 'http://yuyue.lib.qlu.edu.cn/home/web/index',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
        }
        headers['Content-Type'] = 'image/png'
        # 获取验证码
        resp1 = requests.get(
            'http://yuyue.lib.qlu.edu.cn/api.php/check', headers=headers)
        set_cookie = resp1.headers['Set-Cookie'][:-8]
        verify = ddddocr.DdddOcr(show_ad=False).classification(resp1.content)

        # 登录
        headers['Cookie'] = set_cookie
        headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        payload = 'username=' + library_username + \
            '&password=' + library_password + '&verify=' + verify
        resp2 = requests.post(
            'http://yuyue.lib.qlu.edu.cn/api.php/login', headers=headers, data=payload)
        access_token = resp2.json()['data']['_hash_']['access_token']

        # 获取 segment
        segment = ''
        resp4 = requests.get(
            'http://yuyue.lib.qlu.edu.cn/api.php/areadays/'+areaID, headers=headers)
        for areaInfo in resp4.json()['data']['list']:
            segment = str(areaInfo['id'])

        while True:
            # 获取当前的UTC时间
            utc_time = datetime.utcnow()
            print("UTC Time: ", utc_time.strftime('%Y-%m-%d %H:%M:%S'))
            # 计算时差
            time_difference = timedelta(hours=8)  # 北京时间比UTC时间提前8小时
            # 将UTC时间加上时差得到北京时间
            beijing_time = utc_time + time_difference
            print('Beijing Time:', beijing_time.strftime('%Y-%m-%d %H:%M:%S'))
            # 设置目标结束时间为北京时间
            target_time = datetime(
                beijing_time.year, beijing_time.month, beijing_time.day, target_time_hour, target_time_min)
            print('Target Time: ', target_time.strftime('%Y-%m-%d %H:%M:%S'))
            # 设置预定时间
            formatted_next_day = (
                beijing_time+timedelta(days=booked_date)).strftime('%Y-%#m-%#d')
            print('Booked Day: ', formatted_next_day)
            # 判断是否达到目标结束时间
            if beijing_time >= target_time:
                print('到达目标时间')
                break

            # 修改headers
            # http://yuyue.lib.qlu.edu.cn/web/seat3?area=19&segment=1558553&day=2023-9-5&startTime=08:30&endTime=22:00
            headers['Referer'] = 'http://yuyue.lib.qlu.edu.cn/web/seat3?area=' + areaID + '&segment=' + \
                segment + '&day=' + formatted_next_day + '&startTime=08:30&endTime=22:00'

            # 准备预约请求的payload
            bookPayload = 'access_token=' + access_token + '&userid=' + \
                library_username + '&segment=' + segment + '&type=1'

            # 发送预约请求
            resp6 = requests.post('http://yuyue.lib.qlu.edu.cn/api.php/spaces/' +
                                  seatID + '/book', headers=headers, data=bookPayload)

            # 打印结果
            print(resp6.json()['msg'])

            time.sleep(interval_time)
    except Exception as e:
        print(e)
        time.sleep(interval_time)
        run_script_directly(library_username, library_password)


if __name__ == "__main__":
    run_script_directly(str(sys.argv[1]), str(sys.argv[2]))
