Make the repository public, as Boca has deprecated their website and introduced a new app for ticketing.

---
# Boke Bot 

Nowadays, the club adherents (people who cannot access the club membership due to the limit available) can only get tickets when the members release their seats but these are immediately taken by other bots. To compete against these bots they asked me to create one, so I had to come up with a bot maybe even faster than the ones that already exist.

After a short investigation I discovered that some bots work directly on the browser (like Chrome), they execute the same actions that a normal user would do but extremely quickly either using selectors like ids and classes or moving the mouse. 

After doing this, I began to analyze the problem, so I started to replicate the actions of a normal user to understand how the flow to reserve a match seat from the club website works, how it represents the views, what is stored in the browser and how the interface interacts with the user, all this to reverse engineer its operation.


<img width="847" alt="Screenshot 2023-08-30 at 16 11 37" src="https://github.com/juanenmellare/boke-bot/assets/18221356/2b17a050-d14c-426c-b18f-70dc48f92f3f">

<img width="1048" alt="Screenshot 2023-08-30 at 16 14 59" src="https://github.com/juanenmellare/boke-bot/assets/18221356/3b26db13-54cd-4f81-82af-d67a5277f94f">

## Requirements

- Python 3.11 or higher (https://www.python.org/downloads/)

## Setup (only once)

- Open terminal and check python version with `python3 –-version`.
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
```console
python3 boke_bot.py 
```
_Note: Close the terminal or press `Control + C` to stop execution._

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
  "successSongFile": "dale_boca.mp3"  // Once the seat is reserved the boke bot will play a song that should be on root level and mp3 extension.
}
```

