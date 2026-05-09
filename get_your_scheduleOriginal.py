"""
GDUT Class Schedule Fetcher (Original - 极简自动化版)
该工具结合 gdut_login.py，实现全自动课表爬取。
用户只需输入学号密码，程序会自动识别学期并生成日历。
"""

import html
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import time
import sys
import os
import concurrent.futures
from typing import Tuple, Optional, Dict, List, Any
from datetime import datetime
from zoneinfo import ZoneInfo
from ics import Calendar, Event
from getpass import getpass

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.theme import Theme

# 导入自动登录模块
try:
    from gdut_login import login as auto_login
except ImportError:
    auto_login = None

# Constants
ENTIRE_SEMESTER_WEEKS = 20
CLASS_TIMES = {
    "01": ("08:30", "09:15"), "02": ("09:20", "10:05"),
    "03": ("10:25", "11:10"), "04": ("11:15", "12:00"),
    "05": ("13:50", "14:35"), "06": ("14:40", "15:25"),
    "07": ("15:30", "16:15"), "08": ("16:30", "17:15"),
    "09": ("17:20", "18:05"), "10": ("18:30", "19:15"),
    "11": ("19:20", "20:05"), "12": ("20:10", "20:55"),
}
CST_TZ = ZoneInfo("Asia/Shanghai")

console = Console(theme=Theme({
    "info": "dim cyan", "warning": "yellow", "danger": "bold red",
    "success": "bold green", "highlight": "bold cyan"
}))

def get_auto_semester_code() -> str:
    """自动推算当前学期代码"""
    now = datetime.now()
    month, year = now.month, now.year
    # 8月-1月为秋季(01)，2月-7月为春季(02)
    if month >= 8: return f"{year}01"
    elif month == 1: return f"{year - 1}01"
    else: return f"{year - 1}02"

def print_welcome_message() -> None:
    welcome_text = """
该工具将自动登录广工教务系统，并生成 [bold]my_schedule.ics[/bold] 日历文件。

[highlight]操作指引:[/highlight]
1. 输入学号。
2. 输入密码（密码输入时屏幕不会显示，输入完按回车即可）。
3. 程序将自动识别当前学期并开始同步。
    """
    console.print(Panel(welcome_text.strip(), title="[bold blue]GDUT Schedule Fetcher[/bold blue]", subtitle="Auto Edition", border_style="blue", expand=False))

def get_session_and_semester() -> Tuple[requests.Session, str]:
    """全自动获取 Session 和学期代码"""
    semester_code = get_auto_semester_code()
    
    username = console.input(f"\n[bold]请输入学号[/bold]: ").strip()
    if not username:
        console.print("[danger]学号不能为空！[/danger]")
        sys.exit(1)
        
    password = getpass("请输入密码: ").strip()
    if not password:
        console.print("[danger]密码不能为空！[/danger]")
        sys.exit(1)

    if not auto_login:
        console.print("[danger]错误: 找不到 gdut_login.py，请确保文件在同一目录。[/danger]")
        sys.exit(1)

    console.print(f"\n[info][*] 正在尝试自动登录... (识别学期: {semester_code})[/info]")
    session = auto_login(username, password)
    
    if not session:
        console.print("[danger]登录失败，请检查学号密码。[/danger]")
        sys.exit(1)
        
    return session, semester_code

def fetch_week_data(session, semester_code, week):
    url = f"https://jxfw.gdut.edu.cn/xsgrkbcx!getKbRq.action?xnxqdm={semester_code}&zc={week}"
    headers = {"Referer": "https://jxfw.gdut.edu.cn/xsgrkbcx!xsjkbcx.action"}
    try:
        res = session.get(url, headers=headers, timeout=10)
        return res
    except: return None

def process_week_data(calendar, response, week):
    if not response or response.status_code != 200 or not response.text.startswith("["): return
    try:
        data = response.json()
        class_schedule, week_dates = data[0], data[1]
        date_map = {day["xqmc"]: day["rq"] for day in week_dates}
        for course in class_schedule:
            add_course_to_calendar(calendar, course, date_map)
    except: pass

def add_course_to_calendar(calendar, course, date_map):
    course_name = course.get("kcmc", "N/A").strip()
    teacher = course.get("teaxms", "N/A").strip()
    location = course.get("jxcdmc", "Online/TBD")
    day_of_week, periods = course.get("xq", "?"), course.get("jcdm", "")

    if day_of_week in date_map and len(periods) >= 2:
        event_date_str = date_map[day_of_week]
        start_p, end_p = periods[:2], periods[-2:]
        if start_p in CLASS_TIMES and end_p in CLASS_TIMES:
            start_dt = datetime.fromisoformat(f"{event_date_str} {CLASS_TIMES[start_p][0]}:00").replace(tzinfo=CST_TZ)
            end_dt = datetime.fromisoformat(f"{event_date_str} {CLASS_TIMES[end_p][1]}:00").replace(tzinfo=CST_TZ)
            e = Event()
            e.name = html.unescape(course_name)
            e.begin, e.end, e.location = start_dt, end_dt, location
            e.description = f"Teacher: {teacher}\nRemarks: {course.get('sknrjj', '')}"
            calendar.events.add(e)

def main():
    print_welcome_message()
    session, semester_code = get_session_and_semester()

    # 重试策略
    retry = Retry(total=3, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))

    calendar = Calendar()
    console.print("\n[info]正在同步课表数据...[/info]\n")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), 
                  TextColumn("[progress.percentage]{task.percentage:>3.0f}%"), TimeRemainingColumn(), console=console) as progress:
        task_id = progress.add_task("[cyan]获取课表...", total=ENTIRE_SEMESTER_WEEKS)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(fetch_week_data, session, semester_code, week): week for week in range(1, ENTIRE_SEMESTER_WEEKS + 1)}
            for future in concurrent.futures.as_completed(futures):
                process_week_data(calendar, future.result(), futures[future])
                progress.update(task_id, advance=1)

    filename = "my_schedule.ics"
    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(calendar.serialize_iter())
    
    console.print(Panel(f"成功！课表已保存至 [bold green]{filename}[/bold green]\n请将其发送至手机导入日历。", title="[success]完成[/success]", border_style="green"))
    time.sleep(3)

if __name__ == "__main__":
    main()
