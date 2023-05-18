import requests
import time
from random import randint

URL = 'http://127.0.0.1:8000/traffic_record'

while True:
    PARAMS = {
        'carril_izq': randint(1,14),
        'carril_der': randint(5,37)
    }
    response = requests.post(
        url = URL,
        params = PARAMS
    )
    print(response.json())
    time.sleep(2)
