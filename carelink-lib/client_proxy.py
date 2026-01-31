###############################################################################
#
#  Carelink Client 2 Proxy
#
#  Description:
#
#    This program periodically downloads the available data from the
#    Medtronic Carelink API. Then this data is provided via a simple
#    REST API to local clients:
#
#    Send a GET request to the following URI:
#      http://<serveraddr>:8081/carelink/          # all Carelink data
#      http://<serveraddr>:8081/carelink/nohistory # no history data
#
#  Author:
#
#    Ondrej Wisniewski (ondrej.wisniewski *at* gmail.com)
#
#  Changelog:
#
#    08/06/2021 - Initial public release
#    27/07/2021 - Add logging, bug fixes
#    06/02/2022 - Download new data as soon as it is available
#    08/02/2022 - Fix HTTP API
#    24/05/2023 - Add patient parameter
#    12/10/2023 - Replace login parameters with initial token
#    27/10/2023 - Add Web GUI to insert auth token
#    03/01/2024 - Porting to Carelink Client 2
#    11/04/2024 - Handle reconnection in case of network error
#    17/01/2025 - Adapt get_essential_data() to new data format
#    31/01/2026 - Refactor and added own functions + container
#
#  Copyright 2021-2025, Ondrej Wisniewski, Zsolt Alfoldi
#
###############################################################################

import argparse
import copy
import json
import logging
import signal
import sys
import threading
import time
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import client

VERSION = "1.3"

# Logging config
FORMAT = "[%(asctime)s:%(levelname)s] %(message)s"
logging.basicConfig(format=FORMAT, datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO)
log = logging.getLogger(__name__)

# HTTP server settings
HOSTNAME = "0.0.0.0"
PORT = 8081
GUIURL = ""
APIURL = "carelink"
OPT_NOHISTORY = "nohistory"

UPDATE_INTERVAL = 300
RETRY_INTERVAL = 120

# Token handling
TOKENFILE = "logindata.json"
wait_for_params = True

# Status messages
STATUS_INIT = "Initialization"
STATUS_DO_LOGIN = "Performing login"
STATUS_LOGIN_OK = "Login successful"
STATUS_NEED_TKN = "Valid token required"
g_status = STATUS_INIT

recentData = None
TRACE_LEVEL = 2
verbose = False
verbose_level = 1


def trace(msg: str):
    if verbose_level >= TRACE_LEVEL:
        log.debug(f"TRACE: {str(msg)}")


#################################################
# The signal handler for the TERM signal
#################################################
def on_sigterm(signum, frame):
    # TODO: cleanup (if any)
    log.debug("Exiting in sigterm")
    sys.exit()


#################################################
# Get only essential data from json
#################################################


def carelink_get_last_n_blood_sugar_data(data, n=10, mmol=True):
    """
    Get last 'n' bloodsugar data
    -> fixing datetime to epoch
    -> convert sg value to mmol/L
    """
    try:
        log.debug("LOG: get last n")
        _data = copy.deepcopy(data)
        sgs = _data.get("sgs")[n * -1 :]
        for sg in sgs:
            _datetime: str | None = sg.get("datetime", None)
            if _datetime:
                trace(_datetime)
                sg["datetime"] = int(datetime.fromisoformat(_datetime).timestamp())
            if mmol:
                sg["sg"] = round(int(sg.get("sg", 0)) / 18, 1)
        return sgs
    except Exception as e:
        log.debug(e)
        return []


def carelink_get_current_blood_sugar_level(data):
    try:
        log.debug("LOG: get current bs")
        _data = copy.deepcopy(data)
        sg = _data.get("sgs")[-1].get("sg") or None
        if not sg:
            raise ValueError("sg cannot be None")
        return round(sg / 18, 1)
    except Exception as e:
        log.debug(e)
        return 0


def get_essential_data(data):
    mydata = ""
    if data != None:
        try:
            mydata = copy.deepcopy(data["patientData"])
        except (KeyError, TypeError):
            mydata = data.copy()
        try:
            del mydata["sgs"]
        except (KeyError, TypeError):
            pass
        try:
            del mydata["markers"]
        except (KeyError, TypeError):
            pass
        try:
            del mydata["limits"]
        except (KeyError, TypeError):
            pass
        try:
            del mydata["notificationHistory"]
        except (KeyError, TypeError):
            pass
    return mydata


def webgui(status, action=None, country=""):
    head = '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd"> \n \
            <html><head><title>Carelink Client 2 Proxy</title> \n \
            <style></style> \n \
            </head> \n \
            <body><table style="text-align: left; width: 460px; background-color: #2196F3; font-family: Helvetica,Arial,sans-serif; font-weight: bold; color: white;" border="0" cellpadding="2" cellspacing="2"> \n \
            <tbody><tr><td> \n \
            <span style="vertical-align: top; font-size: 48px;">Carelink Client 2</span><br> \n \
            </td></tr></tbody></table><br> \n'

    body = (
        '<table style="text-align: left; width: 460px; background-color: white; font-family: Helvetica,Arial,sans-serif; font-size: 18px;" border="0" cellpadding="2" cellspacing="3"><tbody> \n \
            <tr style="font-size: 18px; font-weight: bold; background-color: lightgrey"> \n \
            <td style="width: 200px;">Status</td> \n \
            <td style="background-color: white;"></td><td style="background-color: white;"></td></tr> \n \
            <tr style="vertical-align: top; background-color: rgb(230, 230, 255);"> \n \
            <td style="width: 300px;">%s</td> \n \
            </tbody></table><br> \n'
        % (status)
    )

    tail = (
        '<span style="font-size: 16px; color: red; font-family: Helvetica,Arial,sans-serif;"></span><br> \n \
            <table style="text-align: left; width: 460px; background-color: #2196F3;" border="0" cellpadding="2" cellspacing="2"><tbody> \n \
            <tr><td style="vertical-align: top; text-align: center;"> \n \
            <span style="font-family: Helvetica,Arial,sans-serif; color: white;"><a style="text-decoration:none; color: white;" href=https://github.com/ondrej1024/carelink-python-client>carelink_client2_proxy</a> | version %s | 2024</span></td></tr> \n \
            </tbody></table></body></html>'
        % VERSION
    )

    html = head + body + tail
    return html


#################################################
# HTTP server methods
#################################################
class MyServer(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Disable logging
        pass

    def do_GET(self):
        # Security checks (if any)
        # TODO
        log.debug(f"received client GET request from {self.address_string()}")
        query_params = parse_qs(urlparse(self.path).query)
        log.debug(query_params)

        # _path = self.path.split("?")[0].strip("/")
        _path = self.path.split("?")[0]
        log.debug(f"with path {_path}")

        # Check request path
        if _path.strip("/") == APIURL:
            response = json.dumps(recentData)
            status_code = HTTPStatus.OK
            content_type = "application/json"
        elif _path.strip("/") == f"{APIURL}/nohistory":
            response = json.dumps(get_essential_data(recentData))
            status_code = HTTPStatus.OK
            content_type = "application/json"
        elif _path.strip("/") == f"{APIURL}/get-last-bsd":
            _last_n = int(query_params.get("last-n", ["0"])[0])
            _last_n = (_last_n and _last_n > 0) and _last_n or 10
            response = json.dumps(
                carelink_get_last_n_blood_sugar_data(recentData, _last_n)
            )
            status_code = HTTPStatus.OK
            content_type = "application/json"
        elif _path.strip("/") == f"{APIURL}/get-current-bsd":
            response = json.dumps(carelink_get_current_blood_sugar_level(recentData))
            status_code = HTTPStatus.OK
            content_type = "application/json"
        elif _path == "/":
            # Show web GUI
            if g_status == STATUS_NEED_TKN:
                response = webgui(status=g_status, action=GUIURL)
            else:
                response = webgui(status=g_status)
            status_code = HTTPStatus.OK
            content_type = "text/html"
            # print("Setup web page requested")
        else:
            response = ""
            status_code = HTTPStatus.NOT_FOUND
            content_type = "text/html"
            # print("page not found")

        # Send response
        self.send_response(status_code)
        self.send_header("Content-type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        try:
            self.wfile.write(bytes(response, "utf-8"))
        except BrokenPipeError:
            pass


#################################################
# Web server thread
#################################################
def webserver_thread():
    # Init web server
    webserver = ThreadingHTTPServer((HOSTNAME, PORT), MyServer)
    log.debug("HTTP server started at http://%s:%s" % (HOSTNAME, PORT))

    # Start server loop
    webserver.serve_forever()


#################################################
# Start web server as asynchronous thread
#################################################
def start_webserver():
    t = threading.Thread(target=webserver_thread, args=())
    t.daemon = True
    t.start()


# Parse command line
parser = argparse.ArgumentParser()
parser.add_argument(
    "--tokenfile",
    "-t",
    type=str,
    help="File containing auth tokens (default: %s)" % TOKENFILE,
    required=False,
)
parser.add_argument(
    "--wait",
    "-w",
    type=int,
    help="Wait seconds between repeated calls (default 300)",
    required=False,
)
parser.add_argument("--verbose", "-v", help="Verbose mode", action="store_true")
parser.add_argument(
    "--verbose-level", "-l", help="Verbose level", type=int, required=False
)
args = parser.parse_args()

# Get parameters from CLI
tokenfile = TOKENFILE if args.tokenfile == None else args.tokenfile
wait = UPDATE_INTERVAL if args.wait == None else args.wait
verbose = args.verbose

print(args.verbose_level)

if args.verbose_level:
    verbose_level = args.verbose_level

# Logging config (verbose)
if verbose:
    log.setLevel(logging.DEBUG)

# log.addHandler(logging.StreamHandler())

log.info("Starting Carelink Client Proxy (version %s)" % VERSION)

# Init signal handler
signal.signal(signal.SIGTERM, on_sigterm)
signal.signal(signal.SIGINT, on_sigterm)

# Start web server
start_webserver()

# Main process loop
while True:
    # Init Carelink client
    _client = client.CareLinkClient(tokenFile=tokenfile)
    g_status = STATUS_DO_LOGIN

    # Login to Carelink server
    if _client.init():
        g_status = STATUS_LOGIN_OK

        # Infinite loop requesting Carelink data periodically
        i = 0
        while True:
            i += 1
            log.debug("Starting download %d" % i)

            try:
                recentData = _client.getRecentData()
                if (
                    recentData != None
                    and _client.getLastResponseCode() == HTTPStatus.OK
                ):
                    log.debug("New data received")
                elif (
                    _client.getLastResponseCode() == HTTPStatus.FORBIDDEN
                    or _client.getLastResponseCode() == HTTPStatus.UNAUTHORIZED
                ):
                    # Authorization error occured
                    log.error(
                        "ERROR: failed to get data (Authotization error, response code %d)"
                        % _client.getLastResponseCode()
                    )
                    break
                else:
                    # Connection error occured
                    log.error(
                        "ERROR: failed to get data (Connection error, response code %d)"
                        % _client.getLastResponseCode()
                    )
                    time.sleep(60)
                    continue
            except Exception as e:
                log.error(e)
                recentData = None
                time.sleep(60)
                continue

            # Calculate time until next reading
            try:
                nextReading = (
                    int(recentData["lastConduitUpdateServerTime"] / 1000) + wait
                )
                tmoSeconds = int(nextReading - time.time())
                log.debug(
                    "Next reading at {0}, {1} seconds from now\n".format(
                        nextReading, tmoSeconds
                    )
                )
                if tmoSeconds < 0:
                    tmoSeconds = RETRY_INTERVAL
            except KeyError:
                tmoSeconds = RETRY_INTERVAL
                # print("Retry reading {0} seconds from now\n".format(tmoSeconds))

            log.debug("Waiting " + str(tmoSeconds) + " seconds before next download")
            time.sleep(tmoSeconds + 10)

    # Wait for new token
    # FIXME
    log.info(STATUS_NEED_TKN)
    g_status = STATUS_NEED_TKN
    wait_for_params = True
    while wait_for_params:
        time.sleep(0.1)

# Exit
log.info("Exit")
