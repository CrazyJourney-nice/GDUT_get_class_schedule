import requests
import re
import base64
import random
import os
import sys
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# Constants
LOGIN_URL = "https://authserver.gdut.edu.cn/authserver/login?service=https%3A%2F%2Fjxfw.gdut.edu.cn%2Fnew%2FssoLogin"
CHARS = "ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678"

def encrypt_password(password, salt):
    iv = "".join(random.choice(CHARS) for _ in range(16))
    random_str = "".join(random.choice(CHARS) for _ in range(64))
    plaintext = random_str + password
    key = salt.encode('utf-8')
    iv_bytes = iv.encode('utf-8')
    cipher = AES.new(key, AES.MODE_CBC, iv_bytes)
    ct_bytes = cipher.encrypt(pad(plaintext.encode('utf-8'), AES.block_size))
    return base64.b64encode(ct_bytes).decode('utf-8')

def login(username, password):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    })

    print(f"[*] Step 1: Fetching login page params...")
    try:
        res = session.get(LOGIN_URL, timeout=10)
        execution = re.search(r'name="execution" value="([^"]+)"', res.text).group(1)
        salt = re.search(r'id="pwdEncryptSalt" value="([^"]+)"', res.text).group(1)
    except Exception as e:
        print(f"[-] Error fetching params: {e}")
        return None

    data = {
        "username": username,
        "password": encrypt_password(password, salt),
        "captcha": "",
        "_eventId": "submit",
        "cllt": "userNameLogin",
        "dllt": "generalLogin",
        "lt": "",
        "execution": execution
    }

    print("[*] Step 2: Authenticating with CAS...")
    # This POST will trigger a series of redirects to jxfw.gdut.edu.cn
    res = session.post(LOGIN_URL, data=data, allow_redirects=True, timeout=15)

    # Crucial: Ensure we have hit the service URL and got the local session
    print(f"[*] Landing URL: {res.url}")
    
    # Check for JSESSIONID in the correct domain
    jw_cookies = session.cookies.get_dict(domain="jxfw.gdut.edu.cn")
    if "JSESSIONID" in jw_cookies:
        print(f"[+] Login Success! Found JSESSIONID: {jw_cookies['JSESSIONID'][:10]}...")
        return session
    else:
        print("[-] Login Success at CAS, but JSESSIONID for 教务系统 not found.")
        print("[*] Current Session Cookies:", session.cookies.get_dict())
        return None

def verify_data_access(session):
    """
    Attempt to fetch real JSON data to verify session
    """
    # Use a likely valid semester code (e.g., 202401 for 2024 Autumn)
    # We'll try to fetch week 1 data
    test_url = "https://jxfw.gdut.edu.cn/xsgrkbcx!getKbRq.action?xnxqdm=202401&zc=1"
    headers = {
        "Referer": "https://jxfw.gdut.edu.cn/xsgrkbcx!xsjkbcx.action",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    print(f"[*] Step 3: Verifying data access via API...")
    try:
        res = session.get(test_url, headers=headers, timeout=10)
        # The API returns a JSON list [class_list, date_list]
        if res.status_code == 200 and res.text.strip().startswith("["):
            print("[+]] SUCCESS! You can now fetch class schedules automatically.")
            return True
        else:
            print(f"[-] API Verification failed. Status: {res.status_code}, Preview: {res.text[:50]}")
    except Exception as e:
        print(f"[-] API Error: {e}")
    return False

if __name__ == "__main__":
    if len(sys.argv) == 3:
        user, pwd = sys.argv[1], sys.argv[2]
        sess = login(user, pwd)
        if sess:
            verify_data_access(sess)
    else:
        print("Usage: python gdut_login.py <username> <password>")
