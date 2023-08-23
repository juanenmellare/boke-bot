# Boke Bot 

## Requirements

- Python 3.11 or higher (https://www.python.org/downloads/)

## Setup (only once)

- Open terminal and check python version with `python3 –version`.
- Change directory to the 'boke_bot' folder, e.g.: `cd .../boke_bot`.
- Execute `python3 -m venv .venv`
- Execute `source .venv/bin/activate`
- Execute `pip3 install -r requirements.txt`.

## Each time before use

- Log in into https://soysocio.bocajuniors.com.ar/.
- Control + click on the page, then click in "inspect".
- Go to the "Application" tab, then "cookies" and click on Boca URL.
- Copy the value of the `bass` cookie into the requests `token` config.json file.
- On the browser select the match, copy the `eNid` of the URL into the match `eNid` config.json file.

## Run

- Open terminal and change directory to the 'boke_bot' folder.
- Execute `source .venv/bin/activate` if you are not already in the env `.venv`.
- Execute the following command:
```bash
python3 boke_bot.py 
```
Note: Close the terminal or press `Control + C` to stop execution.

---

---

### config.json
```json
{
  "match": {
    "eNid": "",                       // The "eNid" displayed in the URL after selecting the match in the browser.
    "selectedGrandstands": []         // The grandstands (view HTML of the stadium) selected separated by coma, if empty includes all. e.g.: ["F", "G", "H", "I", "J", "SCD", "SCI", "SAD", "SAC", "SAI", "SBD", "SBC", "SBI", "SDD", "SDI"].
  },
  "requests": {
    "grandstandsRefreshRate": 2,      // The refresh frequency per seconds to call the grandstands URL.
    "secondsTimeout": 4,              // The maximun time of response, ack.
    "queueRefreshRate": 60,           // The refresh frequency per seconds to call the queue URL.
    "userAgent": "",                  // The 'User-Agent' request header used in the browser.
    "token": ""                       // The "baas" cookie, obtained from the cookies after log in.
  },
  "successSongFile": "dale_boca.mp3"  // Once the seat is reserved the boke bot will play beeps per second to alert the user.
}
```
---
#### v1.0.0


