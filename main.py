import os
import pickle
import re
from enum import Enum
from typing import Any

import requests
from requests.models import Response


class REQMETHOD(Enum):
    GET = "GET"
    POST = "POST"


session = requests.session()
session.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) FxQuantum/144.0 AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15"
    }
)


def save_cookie():
    with open("py_cookie_jar", "wb") as f:
        pickle.dump(session.cookies, f)


def grep(source: str, search: str):
    for s in source.split("\n"):
        if search in s:
            yield s
    return None


if os.path.exists("py_cookie_jar"):
    with open("py_cookie_jar", "rb") as f:
        session.cookies.update(pickle.load(f))


_storage: dict[str, Any] = {}
# __follow = False


def send_request(url: str, method=REQMETHOD.GET, data_raw="", follow=True):
    print(data_raw)
    # _req = session.request(method.value, url, data=data_raw, allow_redirects=False)
    if not follow:
        session.headers.update({"Content-type": "application/x-www-form-urlencoded"})

    _req = session.request(method.value, url, data=data_raw, allow_redirects=follow)
    save_cookie()
    print(_req)

    _location = _req.headers.get("location", None)
    if _location:
        _storage["location"] = _location

    return _req


def get_state(_req: Response):
    to_storage: dict[str, str | None] = {}
    for g in grep(_req.text, 'name="state"'):
        ggg = re.sub("\\s+", " ", re.sub('[<>"]', "", g)).split(" ")
        for _gi in ggg:
            try:
                k, v = _gi.split("=")
            except ValueError:
                k, v = _gi, None
            to_storage.update({k: v})
    _storage["state"] = to_storage


_user_name = os.getenv("CL_USER_NAME", None)
_user_password = os.getenv("CL_USER_PASSWORD", None)
_country = os.getenv("CL_COUNTRY", None)
_lang = os.getenv("CL_LANGUAGE", None)
if None in [_user_name, _user_password, _country, _lang]:
    print("Mandatory env vars are empty")
    os._exit(1)

# __follow = True
_url = f"https://carelink.minimed.eu/patient/sso/login?country={_country}&lang={_lang}"
_req = send_request(_url)

get_state(_req)

_url_params = [f"state={_storage['state']['value']}", "ui_locales=en"]
_data_raw_params = [
    f"state={_storage['state']['value']}",
    f"username={_user_name}",
    f"password={_user_password}",
    "action=default",
]

_url = f"https://carelink-login.minimed.eu/u/login?{'&'.join(_url_params)}"
print(_url)
send_request(_url, REQMETHOD.POST, "&".join(_data_raw_params), False)

_url = f"https://carelink-login.minimed.eu/{_storage['location']}"
_req = send_request(_url)

print(_req.headers)

print(session.cookies)

