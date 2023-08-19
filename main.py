import time
import re
import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def log(message):
    print('\033[0;0m' + message)


def log_warning(message):
    print('\033[93m' + message)


def log_success(message):
    print('\033[0;32m' + message)


def log_progress(message):
    print('\033[1;36m' + message)


def log_error(message):
    print('\033[1;31m' + message)


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
        es_nid = grandstand_data[0]
        grandstand_name = grandstand_data[1]
        log_progress('Grandstand ' + grandstand_name + ' available!')
        break

    return es_nid


if __name__ == '__main__':
    config = get_config()

    match_config = config['match']
    e_nid = match_config['eNid']
    selected_grandstands = match_config['selectedGrandstands']

    requests_config = config['requests']
    base_url = requests_config['baseUrl']
    field_url = base_url + 'comprar_plano_general.php?eNid=' + e_nid
    seats_url = base_url + 'comprar_plano_asiento.php?eNid=' + e_nid + '&esNid='
    check_seat_availability_url = base_url + 'curl_client_request.php'

    refresh_frequency_seconds = requests_config['refreshFrequencySeconds']
    initial_request_timeout_seconds = requests_config['initialRequestTimeoutSeconds']

    cookies = requests_config['cookies']
    headers = requests_config['headers']

    session = build_session()

    seat_reserved = False

    while not seat_reserved:
        es_nid_query_param = None
        timeout = initial_request_timeout_seconds

        has_found_empty_seat_in_grandstand = False
        while not has_found_empty_seat_in_grandstand:
            log("Looking for grandstand with empty seats... ")
            try:
                grandstands_response = session.get(url=field_url, cookies=cookies, headers=headers, timeout=timeout)
            except Exception as error:
                log_error('Error: ' + str(error))
                if str(error) == 'Exceeded 30 redirects.':
                    log_warning('Must update queue cookie...')
                    exit()
                else:
                    log_warning('Something happened while trying to get the grandstands, in '
                                + str(timeout) + ' seconds will try again...')
                    timeout = timeout * initial_request_timeout_seconds
                    time.sleep(refresh_frequency_seconds)
                    continue

            timeout = initial_request_timeout_seconds
            es_nid_query_param = find_es_nid(grandstands_response.text)
            if es_nid_query_param is not None:
                has_found_empty_seat_in_grandstand = True
            else:
                time.sleep(refresh_frequency_seconds)

        full_seats_url = seats_url + es_nid_query_param
        log_progress("// Seat URL: " + full_seats_url)
        seats_response = session.get(url=full_seats_url, cookies=cookies, headers=headers)
        available_seats = re.findall("(?<=updateLocation\", ).*?(?=\))", seats_response.text)
        if not len(available_seats):
            log_warning("Seats already taken...")
            continue

        for availableSeat in available_seats:
            raw_available_seat = availableSeat.replace(' ', '').split(',')
            print(raw_available_seat[0])
            print(raw_available_seat[1])
            seatId = raw_available_seat[2]
            log_progress('Preparing Seat (ID: ' + seatId + ')...')
            check_seat_availability_response_data = {
                'jsonRequest': "{\"eventoUbicacionNid\": \"" + str(seatId) + "\"}",
                'api': 'ventas/consultar_disponibilidad_ubicacion'
            }
            check_seat_availability_response_headers = \
                headers | {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

            check_seat_availability_response = session.post(check_seat_availability_url,
                                                            headers=check_seat_availability_response_headers,
                                                            cookies=cookies,
                                                            data=check_seat_availability_response_data)
            log_success(check_seat_availability_response.content)
            seat_reserved = True
            log_success('Seat reserved successfully!... Vamo\' Boke')
