import re
import time
import json
import email
import random
import string
import imaplib
from bs4 import BeautifulSoup
from datetime import datetime
from curl_cffi import requests
from urllib.parse import urlencode
from email.header import decode_header
from colorama import init, Fore, Style

init(autoreset=True)

AUTH_BASE_URL = "https://auth.casio-intl.com"
REGISTER_FORM_URL = f"{AUTH_BASE_URL}/user/registerForm"
REGISTRATION_COMPLETE_URL = f"{AUTH_BASE_URL}/user/provisionalRegisterCompleted"
USER_VALIDATE_EP = f"{AUTH_BASE_URL}/user/validate"
USER_REGISTER_EP = f"{AUTH_BASE_URL}/user/provisionalRegister"
USER_VERIFY_OTP_EP = f"{AUTH_BASE_URL}/user/regist/verify/code"

IMAP_SERVER = "imap.gmail.com"
CATCHALL_DOMAIN = ""
REGION_CODE = ""
ACCOUNT_PASSWORD = ""

class Colors:
    RED = Fore.RED
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    BLUE = Fore.WHITE
    CYAN = Fore.CYAN
    MAGENTA = Fore.MAGENTA
    RESET = Style.RESET_ALL

def get_timestamp():
    now = datetime.now()
    timestamp = now.strftime("%H:%M:%S") + f".{int(now.microsecond / 1000):03d}"
    return timestamp

def log(message: str, color: str = ""):
    print(f"{get_timestamp()} | {color}{message}{Colors.RESET}", flush=True)

def gen_random_string():
    length = 10
    result = ''.join(random.choices(string.ascii_letters, k=length))
    return result

def append_line(filename, text):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(text + "\n")

def login_imap():
    IMAP_EMAIL = ""
    IMAP_PASSWORD = ""
    global CATCHALL_DOMAIN
    global REGION_CODE
    global ACCOUNT_PASSWORD

    config_file = ""
    with open("config.json", "r", encoding="utf-8") as f:
        config_file = json.load(f)

    IMAP_EMAIL = config_file["IMAP Email"]
    IMAP_PASSWORD = config_file["IMAP Password"]
    CATCHALL_DOMAIN = config_file["Catchall Domain"]
    REGION_CODE = config_file["Region Code"]
    ACCOUNT_PASSWORD = config_file["Account Password"]

    log("Login in to IMAP email")
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(IMAP_EMAIL, IMAP_PASSWORD)
        log("Logged in to IMAP email!", Colors.GREEN)
        return mail
    except imaplib.IMAP4.error as e:
        if "Empty username or password" in str(e):
            log(f"Error logging in to IMAP email: check IMAP Email / IMAP Password in imap.json", Colors.RED)
        else:
            log(f"Error logging in to IMAP email: {e}", Colors.RED)
        return None
    except Exception as e:
        log(f"Exception error when logging in to IMAP email: {e}", Colors.RED)
        return None

def get_body(msg):
    if not msg.is_multipart():
        payload = msg.get_payload(decode=True)
        return payload.decode(msg.get_content_charset() or "utf-8", errors="ignore")

    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            payload = part.get_payload(decode=True)
            if payload:
                return payload.decode(part.get_content_charset() or "utf-8", errors="ignore")

    for part in msg.walk():
        if part.get_content_type() == "text/html":
            payload = part.get_payload(decode=True)
            if payload:
                return payload.decode(part.get_content_charset() or "utf-8", errors="ignore")
    return ""

def create_session():
    session = requests.Session(impersonate="chrome")
    return session

def post_user_validate(session, csrf, country_code, birthdate, email, password, first_name, last_name, register_key):
    user_attrs = {
        "singleValues": {
            "country": country_code,
            "birthdate": birthdate,
            "userName": email,
            "password1": password,
            "password2": password,
            "formatted": f"{first_name} {last_name}",
            "familyName": last_name,
            "givenName": first_name,
            "gender": "m",
            "mailMagazine": "N",
            "opt_consent1": "N",
            "opt_consent2": "N",
            "opt_consent3": "Y",
            "opt_consent4": "N",
            "opt_consent5": "N",
        },
        "state": {
            "uniid_terms_1": "1"
        },
        "registerKey": register_key
    }

    res = session.post(USER_VALIDATE_EP, json=user_attrs)
    validate_json = res.json()

    if validate_json.get("result") != "success":
        return validate_json

    form = {
        "_csrf": csrf,
        "userAttrs": json.dumps(user_attrs, separators=(",", ":")),
        "registerKey": register_key,
        "country": country_code,
        "birthdate": birthdate,
        "userName": email,
        "password1": password,
        "password2": password,
        "formatted": f"{first_name} {last_name}",
        "familyName": last_name,
        "givenName": first_name,
        "gender": "m",
        "mailMagazine": "N",
        "uniid_terms_1": "1",
        "opt_consent1": "N",
        "opt_consent2": "N",
        "disp_opt_consent3": "on",
        "opt_consent3": "Y",
        "opt_consent4": "N",
        "opt_consent5": "N",
        "parentMail": "",
    }

    submit = session.post(USER_REGISTER_EP,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": AUTH_BASE_URL,
            "Referer": REGISTER_FORM_URL,
        },
        data=urlencode(form),
        allow_redirects=True,
    )

    return {
        "result": "success",
        "validate": validate_json,
        "submit": submit,
    }

def post_otp_code(session, csrf, otp_code):
    payload = {
        "_csrf": csrf,
        "mode": "after",
        "code": str(otp_code),
    }
    res = session.post(USER_VERIFY_OTP_EP,
        headers={
            "content-type": "application/x-www-form-urlencoded",
            "origin": AUTH_BASE_URL,
            "referer": REGISTRATION_COMPLETE_URL,
        },
        data=urlencode(payload),
    )
    return res.text

def gen_account(account, mail):   

    session = create_session()

    res = session.get(REGISTER_FORM_URL,
        headers={
            "referer": AUTH_BASE_URL,
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "accept-language": "en-US,en;q=0.9",
        },
    )

    if res.status_code != 200:
        log(f"Account {account} | Blocked by antibot (code {res.status_code}) {res.text}", Colors.RED)
        return

    log(f"Account {account} | Getting tokens")
    soup = BeautifulSoup(res.text, "html.parser")
    register_key = soup.select_one("#registerKey") # Token 1
    csrf = soup.select_one('input[name="_csrf"]')  # Token 2

    try:
        if register_key:
            log(f"Account {account} | Got 1/2 tokens")
            pass
        else:
            log(f"Account {account} | Error getting 1/2 tokens", Colors.RED)

        if csrf:
            log(f"Account {account} | Got 2/2 tokens")
            session.headers.update({"x-csrf-token": csrf['value']})
        else:
            log(f"Account {account} | Error getting 2/2 tokens", Colors.RED)
    except Exception as e:
        log(f"Account {account} | Error getting tokens: {e}", Colors.RED)

    random_first_name = gen_random_string()
    random_last_name = gen_random_string()
    random_string = ''.join(random.sample(string.ascii_letters + string.digits, 8))
    random_email = f"{random_first_name}_{random_string}"

    log(f"Account {account} | Creating account")
    post_user_res = post_user_validate(
        session=session,
        csrf=csrf["value"],
        country_code=REGION_CODE,
        birthdate="20000101",
        email=f"{random_email}@{CATCHALL_DOMAIN}",
        password=ACCOUNT_PASSWORD,
        first_name=random_first_name,
        last_name=random_last_name,
        register_key=register_key["value"],
    )

    if post_user_res["result"] != "success":
        log(f"Account {account} | Error creating account: {post_user_res}", Colors.RED)
        return

    if post_user_res["result"] == "success":
        log(f"Account {account} | Waiting for OTP")
        otp_code = ""

        while not otp_code:
            mail.select("INBOX")
            status, messages = mail.search(None, "ALL")
            email_ids = messages[0].split()
            if not email_ids:
                time.sleep(0.1)
                continue

            latest_email_id = email_ids[-1]
            status, msg_data = mail.fetch(latest_email_id, "(RFC822)")

            for response in msg_data:
                if not isinstance(response, tuple):
                    continue

                msg = email.message_from_bytes(response[1])
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8", errors="ignore")
                if subject.strip() != "[CASIO ID]: Verification code information":
                    continue

                body = get_body(msg)
                match = re.search(r"\d{6}", body)

                if match:
                    otp_code = match.group()
                    log(f"Account {account} | Got OTP", Colors.GREEN)

                    # Delete the email
                    mail.store(latest_email_id, "+FLAGS", "\\Deleted")
                    mail.expunge()
                    break

            if not otp_code:
                time.sleep(0.1)

        log(f"Account {account} | Submitting OTP")
        post_otp_res = post_otp_code(session, csrf['value'], otp_code)

        delete_email_prompt = "Please delete your all latest email titled [CASIO ID]: Verification code information"
        
        if "verification code is incorrect." in post_otp_res:
            log(f"Account {account} | Error creating account: invalid OTP - {delete_email_prompt}", Colors.RED)
        elif "no longer be valid" in post_otp_res:
            log("Account {account} | Error creating account: acc gen blocked", Colors.RED)
        elif "CASIO ID User registered" in post_otp_res:
            log(f"Account {account} | User account created successfully!", Colors.GREEN)
            append_line("accounts.txt", f"{random_email}@{CATCHALL_DOMAIN}")
        else:
            log(f"Account {account} | Error creating account: unknown error", Colors.RED)

def main():
    print("Casio Account Generator\n")
    log("Enter number of accounts to generate")
    number_of_accounts = int(input(f"{get_timestamp()} | [/]: "))

    mail = login_imap()
    
    if mail is None:
        while True:
            pass
    
    if mail:
        for i in range(number_of_accounts):
            gen_account(i+1, mail)
    while True:
        pass

if __name__ == "__main__":
    main()
