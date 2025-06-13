"""
a program automatically scrape your class schedule of semester and output with a .ics file whcih can be added into you phone's calendar 
"""

import html
import requests
import json
import time
import sys
from datetime import datetime, timedelta, timezone 
from ics import Calendar, Event

print("获取GDUT课程表")
print("="*30)
print("该工具会自动爬取你的课程表，并生成一份可以将课程表导入手机日历的.ics文件。")
print("\n使用方法:")
print("1. 登录广东工业大学教务系统（jxfw.gdut.edu.cn）。")
print("2. 打开浏览器的开发者工具（F12），切换到“网络(Network)”标签。")
print("3. 点击“课表查询”。")
print("4. 找到名为“sgrkbcx!getKbRq.action?xnxqdm”的请求，并在Headers标签中的Request Headers栏找到“Cookie”（注意，一定不能泄露cookie给其他任何人）。")
print("5. 复制整个Cookie字符串。")
print("6. 将复制的内容粘贴到本程序中，并按提示输入你的Cookie。")
print("\n注意事项:")
print("1. 请确保你已经登录教务系统，并且课程表数据已加载。")
print("2. 如果课程表数据未加载，请尝试刷新页面或检查网络连接。")
print("3. 程序运行成功后会生成名为“my_schedule”的.ics文件，并存储在与.exe文件同一目录下。")
print("\n请确保你已经登录广东工业大学教务系统，并且课程表数据已加载。")
print("="*30)

YOUR_COOKIE = input("\n输入你复制的cookie(按“回车键”继续):\n>") # Adding your cookie here
if not YOUR_COOKIE.strip():
    print("\nERROR: Cookie不能为空! 请重新运行程序并输入有效的Cookie。")
    time.sleep(3)
    sys.exit()

ACADEMIC_SEMESTER_CODE = "202402" # enter the semester that you want to get
ENTIRE_SEMESTER_WEEKS  = 20

# !!! DO NOT CHANGE ANY CODES BELOW !!!

# 
CLASS_TIMES = {
    '01': ('08:30', '09:15'), '02': ('09:20', '10:05'),
    '03': ('10:25', '11:10'), '04': ('11:15', '12:00'),
    '05': ('13:50', '14:35'), '06': ('14:40', '15:25'),
    '07': ('15:30', '16:15'), '08': ('16:30', '17:15'),
    '09': ('17:20', '18:05'), '10': ('18:30', '19:15'),
    '11': ('19:20', '20:05'), '12': ('20:10', '20:55'),
}


headers = {
    'Cookie': YOUR_COOKIE,
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
}

c = Calendar()
cst_tz = timezone(timedelta(hours=8))

print("Attempting to fetch your class schedule...")


for week in range(1, ENTIRE_SEMESTER_WEEKS + 1):
    API_URL = f"https://jxfw.gdut.edu.cn/xsgrkbcx!getKbRq.action?xnxqdm={ACADEMIC_SEMESTER_CODE}&zc={week}"
    REFERER_URL = f"https://jxfw.gdut.edu.cn/xsgrkbcx!getKbRq.action?xnxqdm={ACADEMIC_SEMESTER_CODE}&zc={week}"
    headers['Referer'] = REFERER_URL

    print("-----------------------------------------------------------------")
    print(f"Fetching data for week {week}...")


    try:
        response = requests.get(API_URL, headers=headers) 

        if response.status_code == 200:
            if not response.text or not response.text.strip().startswith('['):
                print(f"No class schedule data found for week {week}. It might be a")
                time.sleep(1)
                continue
            print("Successfully connected and received data!\n")
        
            try:
                data = response.json()
                class_schedule = data[0]
                week_dates = data[1]

                date_map = {day['xqmc']: day['rq'] for day in week_dates}

            
                

                print(f"Found {len(class_schedule)} classes in your schedule for the {week}:\n")
                print("-----------------------------------------------------------------")

                for course in class_schedule:
                    course_name = course.get('kcmc', 'N/A').strip()
                    teacher = course.get('teaxms', 'N/A').strip()
                    location = course.get('jxcdmc', 'Online/TBD')
                    day_of_week = course.get('xq', '?')
                    time_slots = course.get('jcdm', 'N/A')


                    if day_of_week and day_of_week in date_map:
                        event_date_str = date_map[day_of_week]
                        periods = course.get('jcdm', '')

                        if periods and len(periods) >= 2:
                            start_period, end_period = periods[:2], periods[-2:]

                            if start_period in CLASS_TIMES and end_period in CLASS_TIMES:
                                start_time_str = CLASS_TIMES[start_period][0]
                                end_time_str = CLASS_TIMES[end_period][1]

                                

                                start_datetime = datetime.fromisoformat(f"{event_date_str} {start_time_str}:00").replace(tzinfo=cst_tz)
                                end_datetime = datetime.fromisoformat(f"{event_date_str} {end_time_str}:00").replace(tzinfo=cst_tz)

                                e = Event()
                                e.name = html.unescape(course_name)
                                e.begin = start_datetime
                                e.end = end_datetime
                                e.location = location
                                e.description = f"Teacher: {teacher}\nRemarks: {course.get('sknrjj', '')}"
                            
                                c.events.add(e)
                    
                
            except (json.JSONDecodeError, IndexError, TypeError) as e:
                print(f"Error processing the data: {e}")
                print("Response:", response.text if 'response' in locals() else 'No response object')

        else:
            print(f"Error: Failed to fetch data. Status Code: {response.status_code}")
            print("Response Text:", response.text)

    except requests.exceptions.RequestException as e:
        print(f"A network error occurred for week {week}: {e}")

        time.sleep(5)

    time.sleep(1)


try:
    with open('my_schedule.ics', 'w', encoding='utf-8') as f:
        f.writelines(c.serialize_iter())
    
    print("-----------------------------------------------------------------")
    print("\nSUCCESS! Your schedule has been saved to 'my_schedule.ics'")
    print("You can now send this file to your iPhone and import it into your calendar.")

except Exception as e:
    print(f"\nAn error occurred while writing the file: {e}")


print("\n已成功运行， 该程序会在10s后自动退出。")
time.sleep(10)
# created by @ycj with love