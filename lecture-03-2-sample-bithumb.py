from bithumb import *

def bithumb_init_api():

    api_key = ""
    api_secret = ""
    api = XCoinAPI(api_key, api_secret);
    
    return api

def bithumb_balance(api, cur):
    
    rgParams = {'currency': cur}
    result = api.xcoinApiCall("/info/balance", rgParams)
    
    print (result)

    total_currency = total_krw = in_use_currency = -1.0
    if result['status'] != '0000':
        #print 'Error: bithumb_balance', result
        return -1, -1, -1
    
    data = result['data']
    
    total_currency = ((float) (data['available_%s' % cur.lower()])) * 10000.0
    in_use_currency = ((float) (data['in_use_%s' % cur.lower()])) * 10000.0
    total_currency = (float) (math.floor(total_currency)) / 10000.0
    in_use_currency = (float) (math.floor(in_use_currency)) / 10000.0

    #total_krw = ((float) (data['in_use_krw'])) + ((float) (data['available_krw']))
    total_krw = (float) (data['total_krw'])
    
    return total_currency, total_krw, in_use_currency

def bithumb_buy_order(api, price, units, cur):
    
    rgParams = {'order_currency': cur, 'price': price, 'units': units, 'type': 'bid', 'payment_currency':'KRW'}
    print rgParams
    result = api.xcoinApiCall("/trade/place", rgParams)
    
    try_again = False 
    #order_id = 0
    order_id = None 
    num_trade = 0
    if result['status'] == '0000':
        order_id = result['order_id']
        #num_trade = len (result['data'])
        num_trade = 1
    else:
        try_again = True
    
    return order_id, num_trade, try_again, result

def bithumb_sell_order (api, price, units, cur):
    
    rgParams = {'order_currency': cur, 'price': price, 'units': units, 'type': 'ask', 'payment_currency':'KRW'}
    result = api.xcoinApiCall("/trade/place", rgParams)

    try_again = False 
    order_id = None 
    num_trade = 0
    if result['status'] == '0000':
        order_id = result['order_id']
        #num_trade = len (result['data'])
        num_trade = 1
    else:
        try_again = True

    return order_id, num_trade, try_again, result

def bithumb_cancel_order(api, order_id, cur):
    
    rgParams = {'order_currency': cur, 'order_id': (order_id[0]).encode('ascii'), 'type': (order_id[1]).encode('ascii'), 'payment_currency':'KRW'}
    result = api.xcoinApiCall("/trade/cancel", rgParams)

    if result['status'] == '0000':
        #print '  order cancelled', order_id[2]
        return True, result
    #print '  Possible: bithumb_cancel_order may be empty', result['status']
    return False, result #fill or http error


def main():

    api = bithumb_init_api()
    cur = "BTC"

    #print (bithumb_balance(api, cur))
    #order_id, num_trade, try_again, _err = bithumb_buy_order (api, px, qty, cur)

    #px = 171.1; qty = 10 
    #order_id, num_trade, try_again, _err = bithumb_sell_order (api, px, qty, cur)
    
    #success, _err = bithumb_cancel_order(api, [order_id, 'ask'], cur)
    #print success, _err


if __name__ == "__main__":
    main()

#urllib3.disable_warnings()
