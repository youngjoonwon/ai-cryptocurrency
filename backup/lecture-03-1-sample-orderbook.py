import time
import requests
import pandas as pd

while(1):
    #response = requests.get ('https://api.bithumb.com/public/orderbook/BTC_KRW/?count=10')
    #print (response.text)

    book = {}
    response = requests.get ('https://api.bithumb.com/public/orderbook/BTC_KRW/?count=10')
    book = response.json()

    data = book['data']

    #print (data)
    
    bids = (pd.DataFrame(data['bids'])).apply(pd.to_numeric,errors='ignore')
    bids.sort_values('price', ascending=False, inplace=True)
    bids = bids.reset_index(); del bids['index']
    bids['type'] = 0
    
    asks = (pd.DataFrame(data['asks'])).apply(pd.to_numeric,errors='ignore')
    asks.sort_values('price', ascending=True, inplace=True)
    asks['type'] = 1 

    df = bids.append(asks)
    print (df)

    #df.to_csv("2022-05-11-bithumb-BTC-orderbook.csv")

    time.sleep(5)



#print (response.status_code)

