import time
import re
import json
import urllib3
import requests
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_current_time_for_log():
    now = datetime.now()
    return now.strftime("\033[0;0m%H:%M:%S | ")


def __base_log(color, message):
    print(get_current_time_for_log() + color + message)


def log(message):
    __base_log('', message)


def log_warning(message):
    __base_log('\033[93m', message)


def log_success(message):
    __base_log('\033[92m', message)


def log_progress(message):
    __base_log('\033[1;36m', message)


def log_error(message):
    __base_log('\033[1;31m', message)


def get_config():
    with open('config.json') as json_file:
        return json.load(json_file)


def build_session():
    session_candidate = requests.Session()
    session_candidate.verify = False
    session_candidate.trust_env = False

    return session_candidate


def find_es_nid(grandstands_response_text):
    es_nid = None
    available_grandstands = re.findall("(?<=enableSection\", ).*?(?=\))", grandstands_response_text)
    for available_grandstand in available_grandstands:
        raw_grandstand_data = available_grandstand.replace(' ', '').replace('"', '')
        grandstand_data = raw_grandstand_data.split(',')
        es_nid_candidate = grandstand_data[0]
        grandstand_name = grandstand_data[1]
        if selected_grandstands:
            if grandstand_name in selected_grandstands:
                es_nid = es_nid_candidate
                log_progress('Grandstand ' + grandstand_name + ' available!')
                break
            else:
                log_warning('Grandstand ' + grandstand_name + ' available, but not in the selected list...')
        else:
            es_nid = es_nid_candidate
            log_progress('Grandstand ' + grandstand_name + ' available!')
            break

    return es_nid


def find_grandstand_es_nid():
    es_nid = None
    timeout = seconds_timeout
    has_found_empty_seat_in_grandstand = False
    while not has_found_empty_seat_in_grandstand:
        log("Looking for grandstand with empty seats... ")
        try:
            grandstands_response = session.get(url=field_url, cookies=cookies, headers=headers, timeout=timeout)
        except Exception as grandstands_response_error:
            log_error(str(grandstands_response_error))
            if timeout < max_timeout_seconds_allowed:
                timeout = timeout * 2
            log_warning(
                'Something happened while trying to get the grandstands, in {0} seconds will try again with a '
                'timeout of {1} seconds...'.format(str(refresh_rate), str(timeout)))
            time.sleep(refresh_rate)
            continue

        timeout = seconds_timeout
        es_nid = find_es_nid(grandstands_response.text)
        if es_nid is None:
            time.sleep(refresh_rate)
        else:
            has_found_empty_seat_in_grandstand = True

    return es_nid


def find_available_seat_id(seats_response_text):
    available_seats = re.findall("(?<=updateLocation\", ).*?(?=\))", seats_response_text)
    if not len(available_seats):
        log_warning("Seat already taken...")
        return None

    seat_id = None
    for availableSeat in available_seats:
        raw_available_seat = availableSeat.replace(' ', '').split(',')
        seat_id = raw_available_seat[2]
        break

    return seat_id


def post_sells_api(api_endpoint, seat_id):
    request_data = {
        'jsonRequest': "{\"eventoUbicacionNid\": \"" + str(seat_id) + "\"}",
        'api': 'ventas/' + api_endpoint
    }
    request_headers = headers | {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

    try:
        response = session.post(check_seat_availability_url, headers=request_headers, cookies=cookies,
                                data=request_data)
        return response.json()
    except Exception as error:
        log_error(error)
        return None


def post_reserve_seat(seat_id):
    return post_sells_api('reservar_ubicacion', seat_id)


def run_bot():
    print('==================== BOKE BOT - ' + version + ' ====================')
    seat_reserved = False
    while not seat_reserved:
        grandstand_es_nid = find_grandstand_es_nid()
        full_seats_url = seats_url + grandstand_es_nid
        seats_response = session.get(url=full_seats_url, cookies=cookies, headers=headers)
        available_seat_id = find_available_seat_id(seats_response.text)
        if available_seat_id is None:
            continue

        reserved_seat_json = post_reserve_seat(available_seat_id)
        if reserved_seat_json is None:
            continue

        print(str(reserved_seat_json.json()))
        seat_reserved = True

    log_success('Seat reserved successfully!')
    print('======================= Vamo\' Boke! ======================')


if __name__ == '__main__':
    version = 'v1.0.0'
    config = get_config()

    match_config = config['match']
    e_nid = match_config['eNid']
    selected_grandstands = match_config['selectedGrandstands']

    max_timeout_seconds_allowed = 64
    requests_config = config['requests']
    base_url = 'https://soysocio.bocajuniors.com.ar/'
    field_url = base_url + 'comprar_plano_general.php?eNid=' + e_nid
    seats_url = base_url + 'comprar_plano_asiento.php?eNid=' + e_nid + '&esNid='
    check_seat_availability_url = base_url + 'curl_client_request.php'

    refresh_rate = requests_config['refreshRate']
    seconds_timeout = requests_config['secondsTimeout']

    bass = requests_config['baas']
    cookies = {
        "firstSessionLogin": "true",
        "baas": bass
    }

    headers = {
        "Cache-Control": "no-store, must-revalidate, max-age=0",
        "Connection": "Keep-Alive",
        "Content-Encoding": "gzip",
        "Content-Type": "text/html;charset=ISO-8859-1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/115.0.0.0 Safari/537.36"
    }

    session = build_session()

    run_bot()
    input()
