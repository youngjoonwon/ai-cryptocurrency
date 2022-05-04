import time
import requests

while(1):
    response = requests.get ('https://api.bithumb.com/public/orderbook/BTC_KRW/?count=10')
    print (response.text)
    time.sleep(5)



#print (response.status_code)

