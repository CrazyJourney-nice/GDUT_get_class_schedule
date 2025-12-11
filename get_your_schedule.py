"""
A program to automatically scrape your class schedule of semester and output with a .ics file
which can be added into your phone's calendar.
"""

import html
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import time
import sys
import concurrent.futures
from typing import Tuple, Optional, Dict, List, Any
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from ics import Calendar, Event

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

# Constants
ENTIRE_SEMESTER_WEEKS = 20
CLASS_TIMES = {
    "01": ("08:30", "09:15"),
    "02": ("09:20", "10:05"),
    "03": ("10:25", "11:10"),
    "04": ("11:15", "12:00"),
    "05": ("13:50", "14:35"),
    "06": ("14:40", "15:25"),
    "07": ("15:30", "16:15"),
    "08": ("16:30", "17:15"),
    "09": ("17:20", "18:05"),
    "10": ("18:30", "19:15"),
    "11": ("19:20", "20:05"),
    "12": ("20:10", "20:55"),
}
CST_TZ = ZoneInfo("Asia/Shanghai")

# Initialize Rich Console
console = Console(
    theme=Theme(
        {
            "info": "dim cyan",
            "warning": "yellow",
            "danger": "bold red",
            "success": "bold green",
            "highlight": "bold cyan",
        }
    )
)


def print_welcome_message() -> None:
    welcome_text = """
该工具会自动爬取你的课程表，并生成一份可以将课程表导入手机日历的 .ics 文件。

[highlight]使用方法:[/highlight]
1. 登录广东工业大学教务系统 ([link]jxfw.gdut.edu.cn[/link])。
2. 找到您想查询的[bold]学期代码[/bold] (例如: 2025年秋季 -> '202501'; 2026年春季 -> '202602')。
3. 打开开发者工具 (F12) -> 网络 (Network) 标签。
4. 刷新页面，找到任意发送到 [italic]jxfw.gdut.edu.cn[/italic] 的请求。
5. 在 Headers -> Request Headers 中复制完整的 [bold]Cookie[/bold] 字符串（JSESSIONID=......）。
6. 将完整的 Cookie 粘贴到本程序中。

[highlight]注意事项:[/highlight]
• 确保已登录教务系统。
• 成功后会生成 [bold]my_schedule.ics[/bold] 文件。
    """
    console.print(
        Panel(
            welcome_text.strip(),
            title="[bold blue]GDUT Class Schedule Fetcher[/bold blue]",
            subtitle="Created by @ycj",
            border_style="blue",
            expand=False,
        )
    )
    console.print()


def get_user_input() -> Tuple[str, str]:
    max_retries = 3
    semester_code = ""

    for attempt in range(max_retries):
        semester_code = console.input(
            "[bold]请输入学期代码[/bold] (如2025秋季：202501; 2026春季：202602): "
        ).strip()

        if not semester_code:
            console.print("[danger]ERROR: 学期代码不能为空![/danger]")
        elif not semester_code.endswith(("01", "02")):
            console.print(
                "[danger]ERROR: 学期代码格式不正确![/danger] 代码必须以 '01' (秋季) 或 '02' (春季) 结尾。"
            )
        else:
            break  # Valid input

        if attempt < max_retries - 1:
            console.print(
                f"[warning]请重新输入 (剩余尝试次数: {max_retries - 1 - attempt}).[/warning]\n"
            )
        else:
            console.print("\n[danger]错误次数过多，程序即将退出。[/danger]")
            time.sleep(3)
            sys.exit(1)

    cookie = ""
    for attempt in range(max_retries):
        cookie = console.input(
            "\n[bold]输入 Cookie[/bold] (以 'JSESSIONID=' 开头, 按回车继续):\n> "
        ).strip()

        if not cookie:
            console.print("[danger]ERROR: Cookie不能为空![/danger]")
        elif not cookie.startswith("JSESSIONID="):
            console.print(
                "[danger]ERROR: Cookie 格式不正确![/danger] 必须以 'JSESSIONID=' 开头。"
            )
            console.print("请检查是否复制了正确的 Cookie 值 (不包含 'Cookie: ' 前缀)。")
        else:
            break  # Valid input

        if attempt < max_retries - 1:
            console.print(
                f"[warning]请重新输入 (剩余尝试次数: {max_retries - 1 - attempt}).[/warning]"
            )
        else:
            console.print("\n[danger]错误次数过多，程序即将退出。[/danger]")
            time.sleep(3)
            sys.exit(1)

    return semester_code, cookie


def fetch_week_data(
    session: requests.Session, semester_code: str, week: int
) -> Optional[requests.Response]:
    """Fetches data for a specific week using the provided session."""
    url = f"https://jxfw.gdut.edu.cn/xsgrkbcx!getKbRq.action?xnxqdm={semester_code}&zc={week}"

    # We pass the Referer in a new dict so we don't modify the global session headers
    # which would be unsafe in a threaded environment.
    request_headers = {"Referer": url}

    try:
        response = session.get(url, headers=request_headers, timeout=10)
        return response
    except requests.exceptions.RequestException as e:
        return None


def process_week_data(
    calendar: Calendar, response: requests.Response, week: int
) -> None:
    """Parses the response and adds events to the calendar."""
    if response.status_code != 200:
        console.print(
            f"[danger]Week {week} Error:[/danger] Status Code {response.status_code}"
        )
        return

    if not response.text or not response.text.strip().startswith("["):
        # console.print(f"[warning]Week {week}: No data found or empty.[/warning]")
        return

    try:
        data = response.json()
        class_schedule = data[0]
        week_dates = data[1]
        date_map = {day["xqmc"]: day["rq"] for day in week_dates}

        for course in class_schedule:
            add_course_to_calendar(calendar, course, date_map)

    except (json.JSONDecodeError, IndexError, TypeError) as e:
        console.print(f"[danger]Week {week} Parse Error:[/danger] {e}")


def add_course_to_calendar(calendar, course, date_map):
    """Helper to create an Event object and add it to the calendar."""
    course_name = course.get("kcmc", "N/A").strip()
    teacher = course.get("teaxms", "N/A").strip()
    location = course.get("jxcdmc", "Online/TBD")
    day_of_week = course.get("xq", "?")
    periods = course.get("jcdm", "")

    if day_of_week and day_of_week in date_map:
        event_date_str = date_map[day_of_week]

        if periods and len(periods) >= 2:
            start_period, end_period = periods[:2], periods[-2:]

            if start_period in CLASS_TIMES and end_period in CLASS_TIMES:
                start_time_str = CLASS_TIMES[start_period][0]
                end_time_str = CLASS_TIMES[end_period][1]

                start_datetime = datetime.fromisoformat(
                    f"{event_date_str} {start_time_str}:00"
                ).replace(tzinfo=CST_TZ)
                end_datetime = datetime.fromisoformat(
                    f"{event_date_str} {end_time_str}:00"
                ).replace(tzinfo=CST_TZ)

                e = Event()
                e.name = html.unescape(course_name)
                e.begin = start_datetime
                e.end = end_datetime
                e.location = location
                e.description = (
                    f"Teacher: {teacher}\nRemarks: {course.get('sknrjj', '')}"
                )

                calendar.events.add(e)


def save_calendar(calendar: Calendar, filename: str = "my_schedule.ics") -> None:
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.writelines(calendar.serialize_iter())

        console.print(
            Panel(
                f"Your schedule has been saved to [bold green]'{filename}'[/bold green]\n"
                "You can now send this file to your phone and import it into your calendar.",
                title="[success]SUCCESS[/success]",
                border_style="green",
            )
        )
    except Exception as e:
        console.print(
            f"\n[danger]An error occurred while writing the file: {e}[/danger]"
        )


def main() -> None:
    print_welcome_message()
    semester_code, cookie = get_user_input()

    headers = {
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    }

    session = requests.Session()
    session.headers.update(headers)

    # Configure retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=0.3,
        status_forcelist=[500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    calendar = Calendar()
    console.print("\n[info]Attempting to fetch your class schedule...[/info]\n")

    # Use ThreadPoolExecutor with Rich Progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task(
            "[cyan]Fetching schedule...", total=ENTIRE_SEMESTER_WEEKS
        )

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_week = {
                executor.submit(fetch_week_data, session, semester_code, week): week
                for week in range(1, ENTIRE_SEMESTER_WEEKS + 1)
            }

            for future in concurrent.futures.as_completed(future_to_week):
                week = future_to_week[future]
                try:
                    response = future.result()
                    if response:
                        process_week_data(calendar, response, week)
                except Exception as exc:
                    console.print(f"[danger]Week {week} Exception: {exc}[/danger]")
                finally:
                    progress.update(task_id, advance=1)

    save_calendar(calendar)

    console.print("\n[dim]程序会在10s后自动退出...[/dim]")
    time.sleep(10)


if __name__ == "__main__":
    main()
# created by @ycj with love and passion
