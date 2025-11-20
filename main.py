import os
import pickle
import re
from enum import Enum
from typing import Any

import requests
from requests.models import Response
from requests.sessions import Session


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

    def save_cookie(self):
        with open("py_cookie_jar", "wb") as f:
            pickle.dump(self._session.cookies, f)

    def send_request(self, url: str, method=REQMETHOD.GET, data_raw="", follow=True):
        print(data_raw)
        # _req = session.request(method.value, url, data=data_raw, allow_redirects=False)
        if not follow:
            self._session.headers.update(
                {"Content-type": "application/x-www-form-urlencoded"}
            )

        _req = self._session.request(
            method.value, url, data=data_raw, allow_redirects=follow
        )
        self.save_cookie()
        print(_req)

        _location = _req.headers.get("location", None)
        if _location:
            self._storage["location"] = _location

        return _req

    def get_state(self, _req: Response):
        to_storage: dict[str, str | None] = {}
        for g in grep(_req.text, 'name="state"'):
            ggg = re.sub("\\s+", " ", re.sub('[<>"]', "", g)).split(" ")
            for _gi in ggg:
                try:
                    k, v = _gi.split("=")
                except ValueError:
                    k, v = _gi, None
                to_storage.update({k: v})
        self._storage["state"] = to_storage

    def set_env(self):
        _user_name = os.getenv("CL_USER_NAME", None)
        _user_password = os.getenv("CL_USER_PASSWORD", None)
        _country = os.getenv("CL_COUNTRY", None)
        _lang = os.getenv("CL_LANGUAGE", None)
        if None in [_user_name, _user_password, _country, _lang]:
            print("Mandatory env vars are empty")
            os._exit(1)
        self._cl_vars = CLVars(_user_name, _user_password, _country, _lang)

    def main(self):
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

        _url = f"https://carelink.minimed.eu/patient/sso/login?country={self._cl_vars.country}&lang={self._cl_vars.language}"
        _req = self.send_request(_url)

        self.get_state(_req)

        _url_params = [f"state={self._storage['state']['value']}", "ui_locales=en"]
        _data_raw_params = [
            f"state={self._storage['state']['value']}",
            f"username={self._cl_vars.user_name}",
            f"password={self._cl_vars.user_password}",
            "action=default",
        ]

        _url = f"https://carelink-login.minimed.eu/u/login?{'&'.join(_url_params)}"
        self.send_request(_url, REQMETHOD.POST, "&".join(_data_raw_params), False)

        _url = f"https://carelink-login.minimed.eu/{self._storage['location']}"
        _req = self.send_request(_url)

        print(_req.headers)
        print(self._session.cookies)


if __name__ == "__main__":
    cl = CareLink()
    cl.main()

