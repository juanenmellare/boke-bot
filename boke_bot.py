import time
import re
import json
import urllib3
import requests
import signal
from datetime import datetime
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame


def handler(signum, frame):
    res = input('\n' + get_current_time_for_log() + 'Do you want to exit? y/n... ')
    if res == 'y':
        log_vamo_boke_and_close()


signal.signal(signal.SIGINT, handler)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_current_time_for_log():
    now = datetime.now()
    return now.strftime("\033[0;0m%H:%M:%S | ")


def __base_log(color, message):
    print(get_current_time_for_log() + color + message)


def log(message):
    __base_log('', message)


def log_warning(message):
    __base_log('\033[0;93m', message)


def log_success(message):
    __base_log('\033[0;92m', message)


def log_progress(message):
    __base_log('\033[0;36m', message)


def log_error(message):
    __base_log('\033[0;31m', message)


def log_boca(message):
    print('\033[1;93;44m' + message + '\033[0;0m')


def get_config():
    with open('config.json') as json_file:
        return json.load(json_file)


def build_session():
    session_candidate = requests.Session()
    session_candidate.verify = False
    session_candidate.trust_env = False
    cookies = {
        "firstSessionLogin": "true",
        "baas": token
    }
    session_candidate.cookies = cookies
    user_agent = requests_config['userAgent']
    headers = {
        "Cache-Control": "no-store, must-revalidate, max-age=0",
        "Connection": "Keep-Alive",
        "Content-Encoding": "gzip",
        "Content-Type": "text/html;charset=ISO-8859-1",
        "User-Agent": user_agent
    }
    session_candidate.headers = headers

    return session_candidate


def wait_grandstand_refresh_rate():
    time.sleep(grandstands_refresh_rate)


def find_es_nid(grandstands_response_text):
    es_nid = None
    available_grandstands = re.findall("(?<=enableSection\", ).*?(?=\))", grandstands_response_text)
    try:
        for available_grandstand in available_grandstands:
            raw_grandstand_data = available_grandstand.replace(' ', '').replace('"', '')
            grandstand_data = raw_grandstand_data.split(',')
            es_nid_candidate = grandstand_data[0]
            grandstand_code = grandstand_data[1]
            base_grandstand_available_message = 'Grandstand ' + grandstand_code + ' available'
            is_in_selected_grandstands = selected_grandstands and grandstand_code in selected_grandstands
            if is_in_selected_grandstands or not selected_grandstands:
                es_nid = es_nid_candidate
                log_progress(base_grandstand_available_message+'...')
                break
            else:
                log_warning(base_grandstand_available_message + ', but not in the selected list...')
    except Exception as error:
        log_error("Something happened while processing the grandstand...")
        log_error(str(available_grandstands))
        log_error(str(error))
        log_vamo_boke_and_close()

    return es_nid


def find_available_grandstand_id():
    es_nid = None
    timeout = seconds_timeout
    has_found_available_grandstand = False
    while not has_found_available_grandstand:
        log("Looking for grandstands with empty seats... ")
        try:
            grandstands_response = session.get(url=grandstand_url, timeout=timeout)
        except Exception as grandstands_response_error:
            log_error(str(grandstands_response_error))
            timeout = timeout * 2 if timeout < max_timeout_seconds_allowed else max_timeout_seconds_allowed
            log_warning(
                'Something happened while trying to get the grandstands, in {0} seconds will try again with a '
                'timeout of {1} seconds...'.format(str(grandstands_refresh_rate), str(timeout)))
            wait_grandstand_refresh_rate()
            continue

        grandstands_response_text = grandstands_response.text
        if 'FILA DE ESPERA' in grandstands_response_text:
            log('In the queue, after ' + str(queue_refresh_rate) + ' seconds will retry...')
            time.sleep(queue_refresh_rate)
            continue
        elif '<!-- plano bombonera -->' not in grandstands_response_text:
            log_error("Page stadium not found, update the token of config.js or check the response below to analyze "
                      "if the webpage has any update...")
            log_error(str(grandstands_response.content))
            log_vamo_boke_and_close()

        timeout = seconds_timeout

        es_nid = find_es_nid(grandstands_response_text)
        if es_nid is None:
            wait_grandstand_refresh_rate()
        else:
            has_found_available_grandstand = True

    return es_nid


def find_available_seat_id(es_nid):
    seats_url_with_es_nid = seats_url + es_nid
    seats_response = session.get(url=seats_url_with_es_nid)

    available_seats = re.findall("(?<=updateLocation\", ).*?(?=\))", seats_response.text)
    if not available_seats:
        log_warning("Seat already taken...")
        wait_grandstand_refresh_rate()
        return None

    seat_id = None
    try:
        for availableSeat in available_seats:
            raw_available_seat = availableSeat.replace(' ', '').split(',')
            seat_id = raw_available_seat[2]
            break
    except Exception as error:
        log_error("Something happened while processing the seat...")
        log_error(str(available_seats))
        log_error(str(error))
        log_vamo_boke_and_close()

    log_progress('Seat available...')

    return seat_id


def post_sells_api(api_endpoint, json_request):
    request_data = {
        'jsonRequest': json_request,
        'api': 'ventas/' + api_endpoint
    }
    request_headers = session.headers | {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

    try:
        response = session.post(check_seat_availability_url, headers=request_headers, data=request_data)
        return response.json()
    except Exception as error:
        log_error(error)
        return None


def post_reserve_seat(seat_id):
    json_request = "{\"eventoUbicacionNid\": \"" + str(seat_id) + "\"}"
    return post_sells_api('reservar_ubicacion', json_request)


def reserve_seat(seat_id):
    reserve_seat_json_response = post_reserve_seat(seat_id)
    if reserve_seat_json_response is None:
        return False

    result = reserve_seat_json_response['resultado']
    if result == 'OK':
        log_success('Seat reserved successfully!')
        log_success('Checkout at ' + grandstand_url)
        return True

    if result == 'ERROR':
        description_error = reserve_seat_json_response['descripcionError']
        log_warning('Something happened while trying to reserve. Boca Message: "' + description_error + '"')
        wait_grandstand_refresh_rate()
        return False

    log_error('Unexpected post_reserve_seat response: ' + str(reserve_seat_json_response))
    log_vamo_boke_and_close()


def log_vamo_boke():
    log_boca('======================= Vamo\' Boke! =======================')


def log_vamo_boke_and_close():
    log_vamo_boke()
    exit(1)


def start_bot():
    is_seat_reserved = False
    while not is_seat_reserved:
        available_grandstand_id = find_available_grandstand_id()
        available_seat_id = find_available_seat_id(available_grandstand_id)
        if available_seat_id is not None:
            is_seat_reserved = reserve_seat(available_seat_id)


def play_song():
    success_song_file = config['successSongFile']
    if not success_song_file:
        return

    pygame.init()
    mp3_file = success_song_file
    pygame.mixer.music.load(mp3_file)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pass
    pygame.quit()


if __name__ == '__main__':
    log_boca('======================== BOKE BOT =========================')
    config = get_config()

    match_config = config['match']
    e_nid = match_config['eNid']
    if not e_nid:
        log_error('Missing "eNid" value in the match config.json')
        log_vamo_boke_and_close()

    selected_grandstands = match_config['selectedGrandstands']

    max_timeout_seconds_allowed = 60
    requests_config = config['requests']
    base_url = 'https://soysocio.bocajuniors.com.ar/'
    grandstand_url = base_url + 'comprar_plano_general.php?eNid=' + e_nid
    seats_url = base_url + 'comprar_plano_asiento.php?eNid=' + e_nid + '&esNid='
    check_seat_availability_url = base_url + 'curl_client_request.php'

    grandstands_refresh_rate = requests_config['grandstandsRefreshRate']
    seconds_timeout = requests_config['secondsTimeout']
    queue_refresh_rate = requests_config['queueRefreshRate']

    token = requests_config['token']
    if not token:
        log_error('Missing "token" value in the request config.json')
        log_vamo_boke_and_close()

    session = build_session()

    start_bot()

    play_song()
    log_vamo_boke()
