set -euo pipefail

export expired=0

function _curl() {
    curl -v -b cookie_jar.txt -c cookie_jar.txt "$@" \
        -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) FxQuantum/144.0 AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15' >/tmp/_curl_resp 2>&1

    cat /tmp/_curl_resp | tr -d '\r' >/tmp/curl_resp
    # cat /tmp/curl_resp | tee -a /tmp/all_curl_resp
}

function get_exp_date() {
    jwt_middle=$(cat cookie_jar.txt | grep -oP "auth_tmp_token\t\K.*$" | cut -d. -f2)
    exp_date=$(echo "$jwt_middle"==== | fold -w 4 | sed '$ d' | tr -d '\n' | base64 -d | jq .exp)
    cur_date=$(date +%s)
    echo $(((exp_date - cur_date) / 60))
}

[[ $(get_exp_date) -lt 0 ]] && export expired=1

[[ expired -eq 1 ]] && echo '' >cookie_jar.txt

echo '' >/tmp/all_curl_resp

: ${CL_USER_NAME:?Needed...}
: ${CL_USER_PASSWORD:?Needed...}

function get_token() {

    _curl -L 'https://carelink.minimed.eu/patient/sso/login?country=hu&lang=en'

    state=$(cat /tmp/curl_resp | grep 'name="state"' | tr -d '>"' | cut -d= -f4)
    # echo $state

    _curl 'https://carelink-login.minimed.eu/u/login?state='$state'&ui_locales=en' \
        --data-raw 'state='$state'&username='$CL_USER_NAME'&password='$CL_USER_PASSWORD'&action=default'

    location=$(cat /tmp/curl_resp | grep resume | grep -oP 'location: /\K.*$')
    # echo $location

    _curl -L --compressed "https://carelink-login.minimed.eu/$location"
}

[[ expired -eq 1 ]] && get_token

auth_token=$(cat cookie_jar.txt | grep -oP "auth_tmp_token\t\K.*$")

last_sg=$(
    curl -sq 'https://clcloud.minimed.eu/patient/connect/data' \
        -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) FxQuantum/144.0 AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15' \
        -H 'Content-Type: application/json' \
        -H "Authorization: Bearer $auth_token" |
        jq -r '(.sgs | last).sg'
)

echo "scale=2; $last_sg/18" | bc

# last_sg=$(cat /tmp/curl_resp | )
