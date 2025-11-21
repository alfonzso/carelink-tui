import base64
import json
import os
import pickle
import re
from datetime import datetime
from enum import Enum
from typing import Any, Self

import requests
from requests.models import Response
from requests.sessions import Session


def get_epoch() -> int:
    return int(datetime.now().timestamp())


def grep(source: str, search: str):
    for s in source.split("\n"):
        if search in s:
            yield s
    return None


class REQMETHOD(Enum):
    GET = "GET"
    POST = "POST"


class CLVars:
    """
    user_name: str
    user_password: str
    country: str
    language: str
    """

    user_name: str
    user_password: str
    country: str
    language: str

    def __init__(self, un: str, up: str, c: str, lang: str):
        self.user_name = un
        self.user_password = up
        self.country = c
        self.language = lang


class CareLink:

    _storage: dict[str, Any] = {}
    _session: Session
    _cl_vars: CLVars

    class RequestObj:
        method: REQMETHOD
        headers: dict
        url: str
        data_raw: str
        allow_redirect: bool

        def __init__(self, _u: str, _dw: str = "", _ar: bool = True):
            self.method = REQMETHOD.GET
            self.headers = {}
            self.url = _u
            self.data_raw = _dw
            self.allow_redirect = _ar

        def Get(self):
            self.method = REQMETHOD.GET
            return self

        def Post(self):
            self.method = REQMETHOD.POST
            return self

        def Headers(self, headers: dict):
            self.headers = headers
            return self

        def do(self) -> Self:
            return self

    def __init__(self):
        self.set_env()

        self._session = requests.session()
        self._session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) FxQuantum/144.0 AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15"
            }
        )
        if os.path.exists("py_cookie_jar"):
            with open("py_cookie_jar", "rb") as f:
                self._session.cookies.update(pickle.load(f))

    def create_params(self, _params_dict: dict):
        return "&".join([f"{k}={v}" for k, v in _params_dict.items()])

    def carelink_patient_login(self):
        _url_params = self.create_params(
            {
                "country": self._cl_vars.country,
                "lang": self._cl_vars.language,
            }
        )
        _req_obj = (
            self.RequestObj(
                f"https://carelink.minimed.eu/patient/sso/login?{_url_params}"
            )
            .Get()
            .do()
        )
        return self.send_request(_req_obj)

    def carelink_u_login(self):
        _url_params = self.create_params(
            {"state": self._storage["state"], "ui_locales": "en"}
        )
        _data_raw = self.create_params(
            {
                "state": self._storage["state"],
                "username": self._cl_vars.user_name,
                "password": self._cl_vars.user_password,
                "action": "default",
            }
        )
        _req_obj = (
            self.RequestObj(
                f"https://carelink-login.minimed.eu/u/login?{_url_params}",
                _data_raw,
                False,
            )
            .Post()
            .Headers({"Content-type": "application/x-www-form-urlencoded"})
            .do()
        )
        return self.send_request(_req_obj)

    def carelink_resume(self, _resp: Response):
        _req_obj = (
            self.RequestObj(
                f"https://carelink-login.minimed.eu/{_resp.headers.get("location")}"
            )
            .Get()
            .do()
        )

        return self.send_request(_req_obj)

    def carelink_patient_data(self):

        if self.auth_token is None:
            raise ValueError("Auth token was None...")

        _req_obj = (
            self.RequestObj(
                "https://clcloud.minimed.eu/patient/connect/data",
            )
            .Get()
            .Headers(
                {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.auth_token}",
                }
            )
            .do()
        )
        return self.send_request(_req_obj)

    def carelink_get_last_n__blood_sugar_data(self, n=10):
        print(datetime.now(), "LOG: get last n")
        sgs = self.patient_data.json().get("sgs")[n * -1 :]
        for sg in sgs:
            sg["datetime"] = int(
                datetime.fromisoformat(sg.get("datetime", "")).timestamp()
            )
            sg["sg"] = round(int(sg.get("sg", 0)) / 18, 1)
        return sgs

    def carelink_get_current_blood_sugar_level(self):
        print(datetime.now(), "LOG: get current bs")
        return round((self.patient_data.json().get("sgs")[-1]).get("sg") / 18, 1)

    def save_cookie(self):
        with open("py_cookie_jar", "wb") as f:
            pickle.dump(self._session.cookies, f)

    def send_request(self, obj: RequestObj):
        _response = self._session.request(
            method=obj.method.value,
            url=obj.url,
            data=obj.data_raw,
            allow_redirects=obj.allow_redirect,
            headers=obj.headers,
        )
        self.save_cookie()
        return _response

    def get_state(self, _resp: Response):
        for _grep_res in grep(_resp.text, 'name="state"'):
            search_res = re.search('value="(\\w+)"', _grep_res)
            if search_res:
                self._storage["state"] = search_res.group(1)
                return True
        return False

    def set_env(self):
        _user_name = os.getenv("CL_USER_NAME", None)
        _user_password = os.getenv("CL_USER_PASSWORD", None)
        _country = os.getenv("CL_COUNTRY", None)
        _lang = os.getenv("CL_LANGUAGE", None)
        if None in [_user_name, _user_password, _country, _lang]:
            print("Mandatory env vars are empty")
            os._exit(1)
        self._cl_vars = CLVars(_user_name, _user_password, _country, _lang)

    def get_auth_token(self):
        _cookies = self._session.cookies
        for cookie in _cookies:
            if cookie.name == "auth_tmp_token":
                return cookie.value
        return None

    def is_token_expired(self, token: str):
        if token is None:
            return True
        token_in_3 = token.split(".")
        if not len(token_in_3) == 3:
            return True

        exp = json.loads(base64.b64decode(token_in_3[1] + "==")).get("exp", None)
        if exp is None:
            return True

        return (int(exp) - get_epoch()) // 60 < 0

    def main(self):
        is_expired = self.is_token_expired(self.get_auth_token())

        if is_expired:
            # full monad here
            self.get_state(self.carelink_patient_login())
            self.carelink_resume(self.carelink_u_login())

        self.auth_token = self.get_auth_token()
        self.patient_data = self.carelink_patient_data()


if __name__ == "__main__":
    cl = CareLink()
    cl.main()
    last_n = cl.carelink_get_last_n__blood_sugar_data()
    current_bs = cl.carelink_get_current_blood_sugar_level()
    print(last_n, current_bs)
