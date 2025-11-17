# set -e
set -euo pipefail

function _curl() {
    # curl_resp=$(curl -v -c cookie_jar.txt "$@")
    # curl -v -b cookies.txt -c cookies.txt -b "application_country=hu;application_language=en;m2m_enabled=true" "$@" >/tmp/curl_resp 2>&1
    curl -v -b cookie_jar.txt -c cookie_jar.txt "$@" 2>&1 | tr -d '\r' > /tmp/curl_resp
    cat /tmp/curl_resp | tee -a /tmp/all_curl_resp
    # echo skip
}

echo '' >cookie_jar.txt
echo '' >/tmp/all_curl_resp

: ${CL_USER_NAME:?Needed...}
: ${CL_USER_PASSWORD:?Needed...}

exit 0

# curl -v -c oda -L 'https://carelink.minimed.eu/patient/sso/login?country=hu&lang=en' \
_curl -L 'https://carelink.minimed.eu/patient/sso/login?country=hu&lang=en' \
    -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) FxQuantum/144.0 AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15' \
    -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' \
    -H 'Accept-Language: en-US' \
    -H 'Accept-Encoding: gzip, deflate, br, zstd' \
    -H 'DNT: 1' \
    -H 'Alt-Used: carelink.minimed.eu' \
    -H 'Connection: keep-alive' \
    -H 'Referer: https://carelink.minimed.eu/app/login' \
    -H 'Cookie: m2m_enabled=true' \
    -H 'Upgrade-Insecure-Requests: 1' \
    -H 'Sec-Fetch-Dest: document' \
    -H 'Sec-Fetch-Mode: navigate' \
    -H 'Sec-Fetch-Site: same-origin' \
    -H 'Sec-Fetch-User: ?1' \
    -H 'Priority: u=0, i' \
    -H 'TE: trailers'

# state=$(cat /tmp/curl_resp | grep 'name="state"' )

state=$(cat /tmp/curl_resp | grep 'name="state"' | tr -d '>"' | cut -d= -f4)

echo $state

# _curl 'https://carelink-login.minimed.eu/u/login?state='$state'&ui_locales=en' \
#   -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) FxQuantum/144.0 AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15' \
#   -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' \
#   -H 'Accept-Language: en-US' \
#   -H 'Accept-Encoding: gzip, deflate, br, zstd' \
#   -H 'Referer: https://carelink.minimed.eu/' \
#   -H 'DNT: 1' \
#   -H 'Connection: keep-alive' \
#   -H 'Upgrade-Insecure-Requests: 1' \
#   -H 'Sec-Fetch-Dest: document' \
#   -H 'Sec-Fetch-Mode: navigate' \
#   -H 'Sec-Fetch-Site: same-site' \
#   -H 'Sec-Fetch-User: ?1' \
#   -H 'Priority: u=0, i' \
#   -H 'TE: trailers'

# exit 0

# curl 'https://carelink.minimed.eu/patient/configuration/system/personal.crm.settings' \
#   -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) FxQuantum/144.0 AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15' \
#   -H 'Accept: */*' \
#   -H 'Accept-Language: en-US' \
#   -H 'Accept-Encoding: gzip, deflate, br, zstd' \
#   -H 'Origin: https://carelink-login.minimed.eu' \
#   -H 'DNT: 1' \
#   -H 'Connection: keep-alive' \
#   -H 'Sec-Fetch-Dest: empty' \
#   -H 'Sec-Fetch-Mode: cors' \
#   -H 'Sec-Fetch-Site: same-site' \
#   -H 'Priority: u=4' \
#   -H 'TE: trailers'
#
# _curl 'https://carelink.minimed.eu/crm/ocl/15.2/i18n/ui/sso/en.json' \
#   --compressed \
#   -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) FxQuantum/144.0 AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15' \
#   -H 'Accept: */*' \
#   -H 'Accept-Language: en-US' \
#   -H 'Accept-Encoding: gzip, deflate, br, zstd' \
#   -H 'Origin: https://carelink-login.minimed.eu' \
#   -H 'DNT: 1' \
#   -H 'Connection: keep-alive' \
#   -H 'Sec-Fetch-Dest: empty' \
#   -H 'Sec-Fetch-Mode: cors' \
#   -H 'Sec-Fetch-Site: same-site' \
#   -H 'Priority: u=4' \
#   -H 'TE: trailers'
#
# curl -v -c oda
# _curl -L --compressed 'https://carelink-login.minimed.eu/u/login?state='$state'&ui_locales=en' \
_curl 'https://carelink-login.minimed.eu/u/login?state='$state'&ui_locales=en' \
    -X POST \
    -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0' \
    -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' \
    -H 'Accept-Language: en-US' \
    -H 'Accept-Encoding: gzip, deflate, br, zstd' \
    -H 'Referer: https://carelink-login.minimed.eu/u/login?state='$state'&ui_locales=en' \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    -H 'Origin: https://carelink-login.minimed.eu' \
    -H 'DNT: 1' \
    -H 'Connection: keep-alive' \
    -H 'Upgrade-Insecure-Requests: 1' \
    -H 'Sec-Fetch-Dest: document' \
    -H 'Sec-Fetch-Mode: navigate' \
    -H 'Sec-Fetch-Site: same-origin' \
    -H 'Sec-Fetch-User: ?1' \
    -H 'Priority: u=0, i' \
    --data-raw 'state='$state'&username='$CL_USER_NAME'&password='$CL_USER_PASSWORD'&action=default'

# location=$(cat /tmp/curl_resp | awk -F': ' '/^Location:/ {print $2}' | tr -d '\r')
# location=$(cat /tmp/curl_resp | grep -oP 'location: \K.*$')
location=$(cat /tmp/curl_resp | grep resume | grep -oP 'location: /\K.*$')

echo "############################"
echo $location
echo "############################"

# https://carelink-login.minimed.eu/

_curl -L --compressed "https://carelink-login.minimed.eu/$location" \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0' \
  -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' \
  -H 'Accept-Language: en-US' \
  -H 'Accept-Encoding: gzip, deflate, br, zstd' \
  -H 'Referer: https://carelink-login.minimed.eu/u/login?state='$state'&ui_locales=en' \
  -H 'DNT: 1' \
  -H 'Connection: keep-alive' \
  -H 'Upgrade-Insecure-Requests: 1' \
  -H 'Sec-Fetch-Dest: document' \
  -H 'Sec-Fetch-Mode: navigate' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'Sec-Fetch-User: ?1' \
  -H 'Priority: u=0, i' \
  -H 'TE: trailers'

