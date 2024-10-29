import json
import requests
import time
from datetime import datetime
import pandas as pd

def get_coin():
    quotation = requests.get("https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL,BTC-BRL")
    return quotation.json()
'''
    dolar = quotation['USDBRL']['bid']
    print(f"Dollar --> Real : {dolar}")

    euro = quotation["EURBRL"]["bid"]
    print (f"Euro --> Real : {euro}")
'''
def timer_coin():
    i=1
    rep = 6

    df_coin = pd.DataFrame(columns=['time','dollar','euro'])

    while i<=rep:

        quotation = get_coin()

        current_time = datetime.now().strftime('%H:%M:%S')

        if quotation is not None:

            new_row = {
                "time" : current_time,
                "dollar" : "$" + quotation['USDBRL']['bid'],
                "euro" : "$" +  quotation['EURBRL']['bid'],
            }

            df_coin = pd.concat([df_coin, pd.DataFrame([new_row])],ignore_index=True)

            print(df_coin.tail(1))
            print("\n_________________________________________\n")

        else:
            print("Não foi possível obter os preços.")

        if i != rep:
          time.sleep(10)
        i+=1

def get_cripto():
    coins = ['bitcoin', 'ethereum', 'litecoin']
    url = 'https://api.coingecko.com/api/v3/simple/price'

    params = {
        'ids': ','.join(coins),
        'vs_currencies': 'usd'
    }

    quotation = requests.get(url, params=params)

    if quotation.status_code == 200:
        return quotation.json()
    else:
        print("ERROR:", quotation.status_code)
        return None
    
def timer_cripto():
    i=1
    rep = 6

    df = pd.DataFrame(columns=['time','bitcoin','ethereum','litecoin'])

    while i<=rep:

        quotation = get_cripto()

        current_time = datetime.now().strftime('%H:%M:%S')

        if quotation is not None:

            new_row = {
                "time" : current_time,
                "bitcoin" : f"${quotation['bitcoin']['usd']:.2f}",
                "ethereum" : f"${quotation['ethereum']['usd']:.2f}",
                "litecoin" : f"${quotation['litecoin']['usd']:.2f}"
            }

            df = pd.concat([df, pd.DataFrame([new_row])],ignore_index=True)

            print(df.tail(1))
            print("\n_________________________________________\n")

        else:
            print("Não foi possível obter os preços.")

        if i != rep:
          time.sleep(10)
        i+=1

if __name__ == "__main__":
    timer_coin()