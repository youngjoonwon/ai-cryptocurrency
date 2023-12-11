#! /usr/bin/env python

import sys
import datetime
import json
import csv
import os
import requests
import time

import jwt
from urllib.parse import urlencode
import math
import uuid

def upbit_request(endpoint, method, query, params=None):

    url = "https://api.upbit.com" + endpoint
    body = ""
    auth_header = None
    if method == "POST" or method == 'DELETE':
        body = query
    
    payload = {
            "access_key": api_key,
            "nonce": str(uuid.uuid4()),
            }
    
    try:
        if method == "GET":

            #print (payload)
            
            token = jwt.encode(payload, api_secret).decode('utf-8')
            
            auth_header = {
                "Authorization": "Bearer " + token #"Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=auth_header)
            response = response.json()

            return response

        elif method == "POST":
            
            query_string = urlencode(query).encode()
            m = hashlib.sha512()
            m.update(query_string)
            query_hash = m.hexdigest()

            payload['query_hash'] = query_hash
            payload['query_hash_alg'] = 'SHA512'
            token = jwt.encode(payload, api_secret).decode('utf-8')
            
            auth_header = {
                "Authorization": "Bearer " + token #"Content-Type": "application/json"
            }

           
            response = requests.post(url, params=query, headers=auth_header)
            response = response.json()

            return response

        elif method == "DELETE":
            query_string = urlencode(query).encode()
            m = hashlib.sha512()
            m.update(query_string)
            query_hash = m.hexdigest()

            payload['query_hash'] = query_hash
            payload['query_hash_alg'] = 'SHA512'
            token = jwt.encode(payload, api_secret).decode('utf-8')
            
            auth_header = {
                "Authorization": "Bearer " + token #"Content-Type": "application/json"
            }

            response = requests.delete(url, params=query, headers=auth_header)
            response = response.json()

            return response
    except:
        return None

def upbit_balance(cur):
    
    result = upbit_request ('/v1/accounts', 'GET', None) 

    total_currency = total_krw = in_use_currency = -1.0
    
    if result is None:
        #print 'Error: upbit_balance', result
        return -1, -1, -1
    
    #print ('upbit balance', result); sys.stdout.flush()

    total_krw = (float)((result[0])['balance']) + (float)((result[0])['locked'])
    
    for account in result:
        if account['currency'] == cur:
            total_currency = ((float) (account['balance'])) * 10000.0
            total_currency = (float) (math.floor(total_currency)) / 10000.0
            in_use_currency = ((float) (account['locked'])) * 10000.0
            in_use_currency = (float) (math.floor(in_use_currency)) / 10000.0
        if account['currency'] == 'KRW':
            total_krw = (float)(account['balance'])

    return total_currency, total_krw, in_use_currency

def upbit_buy_order(price, units, market):
    
    query = { 'market': market,
            'side': 'bid',
            'volume': units,
            'price': price,
            'ord_type': 'limit'
            }
    
    try_again = False
    result = upbit_request ('/v1/orders', 'POST', query, None)
    order_id = result.get('uuid', None)
    num_trade = result.get('trade_count', 0)
    
    print ('buy order', result); sys.stdout.flush()
   
    if order_id is None:
        try_again = True

    return order_id, num_trade, try_again, result

def upbit_sell_order(price, units, market):
    
    query = { 'market': market,
            'side': 'ask',
            'volume': units,
            'price': price,
            'ord_type': 'limit'
            }
    
    try_again = False
    result = upbit_request ('/v1/orders', 'POST', query, None)
    order_id = result.get('uuid', None)
    num_trade = result.get('trade_count',0)
    
    print ('sell order', result); sys.stdout.flush()

    if order_id is None:
        try_again = True

    return order_id, num_trade, try_again, result

def upbit_cancel_order(order_id):

    query = { 'uuid': order_id.encode('ascii') }

    result = upbit_request ('/v1/order', 'DELETE', query, None)
    
    print ('upbit-cancel', result); sys.stdout.flush()
    
    if result is None:
        return False, result

    return True, result


api_key = ""
api_secret = ""


cur = 'BTC'
market = 'KRW-BTC'

#print (upbit_balance(cur))

exit()

