#! /usr/bin/env python

import sys
import math
import time
import logging
from telepot.loop import MessageLoop

import datetime
import json
import csv
import os
import requests
import time

import urllib
import math

import time
import telepot

import timeit
import pandas as pd
import random
import hashlib
import collections
import hmac

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import urllib3

import pycurl
from StringIO import StringIO

import decimal 

from xcoin_api_client import *

import multiprocessing
import threading

import base64
import httplib2

#from config_tele_trade_bot import *

import jwt
import base64
import uuid

from requests import Request, Response


def ftx_order_success(_err):
    if _err is None:
        return False
    
    if _err['success'] == True:
        return True
    else:
        return False

def ftx_live_book(data, req_timestamp):
    #timestamp,price,type,quantity

    data = data['result']

    bids = (pd.DataFrame(data['bids'])).apply(pd.to_numeric,errors='ignore')
    #print bids
    #bids = (bids.groupby('price').sum()).reset_index()
    bids.columns = ['price','quantity']
    bids.sort_values('price', ascending=False, inplace=True)
    bids = bids.reset_index(); del bids['index']
    bids['type'] = 0

    asks = (pd.DataFrame(data['asks'])).apply(pd.to_numeric,errors='ignore')
    #print asks
    asks.columns = ['price','quantity']
    asks.sort_values('price', ascending=True, inplace=True)
    asks['type'] = 1
    
    #print bids
    #print asks

    #return bids.head(5), asks.head(5)
    return bids, asks


def ftx_book(ex, currency, req_timestamp, session):
    
    market = ftx_market(currency, '')
 
    url = _dict_url[ex][0]
    try:
        #start_time = timeit.default_timer()
        book = (session.get(url % market, headers={ 'User-Agent': 'Mozilla/5.0' }, verify=False, timeout=1)).json()
    except:
        return None, None
    
    if book is None:
        return None, None

    #if type(book) is not list:
    #    return None, None

    if book['success'] is not True:
        return None, None

    bids, asks = ftx_live_book(book, req_timestamp)

    return bids, asks

def ftx_tick (px):
    
    return 0.5 #temporary

    '''
    if 0 < px and px < 10.0:
        return 0.01
    elif 10.0 <= px and px < 100.0:
        return 0.1
    elif 100.0 <= px and px < 1000.0:
        return 1
    elif 1000.0 <= px and px < 10000.0:
        return 5
    elif 10000.0 <= px and px < 100000.0:
        return 10
    elif 100000.0 <= px and px < 500000.0:
        return 50
    elif 500000.0 <= px and px < 1000000.0:
        return 100
    elif 1000000.0 <= px and px < 2000000.0:
        return 500
    elif px >= 2000000.0:
        return 1000
    '''

def ftx_digit (tick):
    
    str_tick = decimal.Decimal('%s' % tick)
    return abs(str_tick.as_tuple().exponent)

#def ftx_sign_request(api_key, api_secret, request: Request) -> None:
def ftx_sign_request(api_key, api_secret, request):
    
    ts = int(time.time() * 1000)
    prepared = request.prepare()
    #signature_payload = '{ts}{prepared.method}{prepared.path_url}'.encode()
    signature_payload = ('%s%s%s'% (ts,prepared.method,prepared.path_url)).encode()
    
    #print ts
    #print prepared.method
    #print prepared.path_url
    #print signature_payload

    if prepared.body:
        signature_payload += prepared.body

    #signature = hmac.new(api_secret.encode(), signature_payload, 'sha256').hexdigest()
    signature = hmac.new(api_secret.encode(), str.encode(signature_payload), hashlib.sha256).hexdigest()
    #print signature
    
    request.headers['FTX-KEY'] = api_key
    request.headers['FTX-SIGN'] = signature
    request.headers['FTX-TS'] = str(ts)
    request.headers['FTX-SUBACCOUNT'] = ''.encode('ascii')
    
    #if subaccount_name:
    #    request.headers['FTX-SUBACCOUNT'] = urllib.parse.quote(subaccount_name)

def ftx_self_request(api_key, api_secret, method, path, **kwargs):
    
    request = Request(method, path, **kwargs)

    ftx_sign_request(api_key, api_secret, request)
    response = session.send(request.prepare())
    
    print response.json()

    return response.json()

def ftx_request(api_key, api_secret, endpoint, method, query, params=None):
    
    time.sleep(0.01)
    
    url = "https://ftx.com/api/" + endpoint
    body = ""
    auth_header = None
    payload = {}
    
    try:
        if method == 'GET':
            return ftx_self_request(api_key, api_secret, method, url, params=query) 
        else: #POST and DELETE
            return ftx_self_request(api_key, api_secret, method, url, json=query)
    except:
        return None

def ftx_market(currency, base_cur):
    
    ##market = currency + '/' + 'USD' #SPOT
    market = currency + '-' + 'PERP' #Futures
    market = market.upper()
    
    return market


def ftx_buy_order(api_key, api_secret, price, units, cur, digits):
    
    market = ftx_market(cur, '')
    
    query = { 'market': market,
            'side': 'buy',
            'price': price,
            'type': 'limit',
            'size': units
            }

    try_again = False
    orig_result = ftx_request (api_key, api_secret, 'orders', 'POST', query, None)
    result = orig_result.get('result', None)
    if result is None:
        return None, 0, True, result

    order_id = result.get('id', None)
    num_trade = result.get('filledSize', 0)
    
    #print 'buy order', result; sys.stdout.flush()
   
    if order_id is None:
        try_again = True

    return order_id, num_trade, try_again, orig_result


def ftx_sell_order(api_key, api_secret, price, units, cur, digits):
    
    market = ftx_market(cur, '')
    
    query = { 'market': market,
            'side': 'sell',
            'price': price,
            'type': 'limit',
            'size': units
            }
    
    try_again = False
    orig_result = ftx_request (api_key, api_secret, 'orders', 'POST', query, None)
    result = orig_result.get('result', None)
    if result is None:
        return None, 0, True, result

    order_id = result.get('id', None)
    num_trade = result.get('filledSize', 0)
    
    #print 'buy order', result; sys.stdout.flush()
   
    if order_id is None:
        try_again = True

    return order_id, num_trade, try_again, orig_result


def ftx_order_info(side, orderid, api_key, api_secret, exchange, currency, base_cur):
 
    cur = currency
   
    if side == 'sell':
        side = 1
    elif side == 'buy':
        side = 0
    else:
        print 'ftx_order_info fail'
        return
  
    orig_result = ftx_request (api_key, api_secret, '/orders/{%s}' % orderid.encode('ascii'), 'GET', {}, None)
    result = orig_result.get('result', None)

    order_info = True
    try_again = False
    
    #print payload
    #print result
    
    if result is None:
        print 'failed: server problem'
        return order_info, 0, try_again, result
    
    #remaining_volume = round((float)(result['remaining_volume']), 4)
    #volume = round((float)(result['volume']), 4)
    executed_volume = round((float)(result['filledSize']), 4)

    #if remaining_volume >= 0.0 and remaining_volume < volume:
    if executed_volume > 0.0: #filled or partially filled
        success, _err = ftx_cancel_order(api_key, api_secret, [orderid, side], int(side), cur)
        print 'order_info cancel', ftx_order_success(_err)
        order_info = False

    return order_info, 0, try_again, orig_result


def ftx_balance(api_key, api_secret, cur):
    
    orig_result = ftx_request (api_key, api_secret, 'wallet/balances', 'GET', None) 
    result = orig_result.get('result', None)
    
    total_currency = total_krw = in_use_currency = -1.0
    if result is None:
        #print 'Error: ftx_balance', result
        return -1, -1, -1
   
    if type(result) is not list:
        #if result.get('error') is None:
        return -1, -1, -1
    
    #print 'ftx balance', result; sys.stdout.flush()
    
    for account in result:
        if account['coin'] == cur:
            total_currency = ((float) (account['total'])) * 10000.0
            total_currency = (float) (math.floor(total_currency)) / 10000.0
            in_use_currency = ((float) (account['free'])) * 10000.0
            in_use_currency = (float) (math.floor(in_use_currency)) / 10000.0
            in_use_currency = total_currency - in_use_currency
        if account['coin'] == 'USD':
            total_krw = (float)(account['total'])

    if total_currency == -1:
        total_currency = 0.0
        in_use_currency = 0.0
        #print 'Wrong: ftx_balance', result; sys.stdout.flush()
        #exit(-1)
    
    return total_currency, total_krw, in_use_currency

def ftx_buymm(qtymult, widthpct, new_tick, trade_size, tick, frequency, chat_id, api_key, api_secret, exchange, currency, base_cur):
    
    cur = currency
    market = ftx_market(cur, '')
   
    telegram_send_all('wait! ftx start buyMM')
    
    self_seq = 0
    seq = 0
    
    timestamp = last_update_time = datetime.datetime.now()
    session = init_session()
    
    out_orders = {}
    openorder_dict = {} #orders in ask789
    last_bid = 0.0
    total_currency = total_krw = in_use_currency = 0.0

    while 1:
        
        if stop_threads:

            od_list = out_orders.values()
            for od in od_list:
                ftx_cancel_order(api_key, api_secret, [od[1],'bid'], 0, cur)
                print 'cancel', cur, od[0]
            return

        timestamp = datetime.datetime.now()
        if ((timestamp - last_update_time).total_seconds() < frequency) and (seq > 0):
            seq += 1
            continue
        __timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        total_currency, total_krw, in_use_currency = ftx_balance(api_key, api_secret, cur)
        gr_bid_level, gr_ask_level = ftx_book(exchange, currency, None, session)
        
        
        if gr_bid_level is None or gr_ask_level is None:
            print 'ftx book is none'; sys.stdout.flush()
            continue
        last_update_time = datetime.datetime.now()
        
        seq += 1

        mid_price, bid, ask, bid_qty, ask_qty = short_cal_mid_price(gr_bid_level, gr_ask_level, None)
        
        tick = ftx_tick(bid)
        digits = ftx_digit(tick)

        bid = round(bid, digits)
        px = bid
        
        #print 'buymm ', px, trade_size; sys.stdout.flush()

        if ((float)(px) <= 0):
            print 'ftx px negative'; sys.stdout.flush()
            continue

        if trade_size > 0:

            order_id = None
            order_history = out_orders.get(px, None)
            if order_history is None:
                order_id, num_trade, try_again, _err = ftx_buy_order (api_key, api_secret, px, trade_size, cur, digits)
                if order_id is None:
                    continue
                out_orders[px] = (px, order_id)
                print 'buymm ', exchange, px, trade_size, __timestamp; sys.stdout.flush()
            else:
                #
                order_info, tmp, try_again, _err = ftx_order_info('buy', order_history[1], api_key, api_secret, exchange, currency, base_cur)
                if order_info is False:
                    order_id, num_trade, try_again, _err = ftx_buy_order (api_key, api_secret, px, trade_size, cur, digits)
                    if order_id is None:
                        continue
                    del out_orders[px]
                    out_orders[px] = (px, order_id)
                    print 'check buymm ', exchange, px, trade_size, __timestamp; sys.stdout.flush()
       
            if stop_threads:
                od_list = out_orders.values()
                for od in od_list:
                    ftx_cancel_order(api_key, api_secret, [od[1],'bid'], 0, cur)
                    print 'cancel', cur, od[0]
                return

            od_list = out_orders.values()
            for od in od_list:
                if (float)(od[0]) != bid:
                    ftx_cancel_order(api_key, api_secret, [od[1],'bid'], 0, cur)
                    del out_orders[od[0]]
                    print 'cancel', cur, od[0]
                    
        #print total_currency, total_krw; print gr_bid_level; print gr_ask_level
        ###
        
        last_bid = bid


def ftx_sellmm(qtymult, widthpct, new_tick, trade_size, tick, frequency, chat_id, api_key, api_secret, exchange, currency, base_cur):
    
    cur = currency
    market = ftx_market(cur, '')
    
    telegram_send_all('wait! ftx start sellMM')
    
    self_seq = 0
    seq = 0
    
    timestamp = last_update_time = datetime.datetime.now()
    session = init_session()
    
    out_orders = {}
    openorder_dict = {} #orders
    last_bid = 0.0
    total_currency = total_krw = in_use_currency = 0.0

    while 1:
        
        if stop_threads:

            od_list = out_orders.values()
            for od in od_list:
                ftx_cancel_order(api_key, api_secret, [od[1],'ask'], 1, cur)
                print 'cancel', cur, od[0]
            return

        timestamp = datetime.datetime.now()
        if ((timestamp - last_update_time).total_seconds() < frequency) and (seq > 0):
            seq += 1
            continue
        __timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        total_currency, total_krw, in_use_currency = ftx_balance(api_key, api_secret, cur)
        gr_bid_level, gr_ask_level = ftx_book(exchange, currency, None, session)
        
        if gr_bid_level is None or gr_ask_level is None:
            print 'ftx book is none'; sys.stdout.flush()
            continue
        last_update_time = datetime.datetime.now()
        
        seq += 1

        mid_price, bid, ask, bid_qty, ask_qty = short_cal_mid_price(gr_bid_level, gr_ask_level, None)
        
        tick = ftx_tick(ask)
        digits = ftx_digit(tick)

        ask = round(ask, digits)
        px = ask
        
        #print 'sellmm ', px, trade_size; sys.stdout.flush()

        if ((float)(px) <= 0):
            print 'ftx px negative'; sys.stdout.flush()
            continue

        if trade_size > 0:

            order_id = None
            order_history = out_orders.get(px, None)
            if order_history is None:
                order_id, num_trade, try_again, _err = ftx_sell_order (api_key, api_secret, px, trade_size, cur, digits)
                if order_id is None:
                    continue
                out_orders[px] = (px, order_id)
                print 'sellmm ', exchange, px, trade_size, __timestamp; sys.stdout.flush()
            else:
                order_info, tmp, try_again, _err = ftx_order_info('sell', order_history[1], api_key, api_secret, exchange, currency, base_cur)
                if order_info is False:
                    order_id, num_trade, try_again, _err = ftx_sell_order (api_key, api_secret, px, trade_size, cur, digits)
                    if order_id is None:
                        continue
                    del out_orders[px]
                    out_orders[px] = (px, order_id)
                    print 'check sellmm ', exchange, px, trade_size, __timestamp; sys.stdout.flush()
       
            if stop_threads:
                od_list = out_orders.values()
                for od in od_list:
                    ftx_cancel_order(api_key, api_secret, [od[1],'ask'], 1, cur)
                    print 'cancel', cur, od[0]
                return

            od_list = out_orders.values()
            for od in od_list:
                if (float)(od[0]) != ask:
                    ftx_cancel_order(api_key, api_secret, [od[1],'ask'], 1, cur)
                    del out_orders[od[0]]
                    print 'cancel', cur, od[0]
        
        last_bid = bid


def ftx_fill_range (side, start_qty, end_qty, start_px, end_px, tick, buy_first, level_treshold, chat_id, api_key, api_secret, exchange, currency, base_cur):
    
    cur = currency
    market = ftx_market(cur, '')

    price = bid_price = ask_price = start_px

    print side,
    
    price = 0.0
    if side == 'sell':
        side = 1
        price = ask_price
    elif side == 'buy':
        side = 0
        price = bid_price
    else:
        print 'Error: fill_range side wrong'; exit(-1)

    telegram_send_all('wait! do not touch! ftx start order')
    
    _flag = buy_first
    
    tick = ftx_tick(price)
    tick = tick*1 #ftx
    
    cur_level = 0
    max_level = int((round(abs(end_px - start_px), 3))/tick)
    level_789 = 6 
    level_789_threshold = level_treshold
    
    out_msg = ''
    while(1):
        
        if stop_threads:
            return
   
        digits = ftx_digit(tick)
        #print 'digits', digits

        if side == 1: #ask
            px = round(price, digits)
            
            trade_size = round(random.uniform (start_qty, end_qty), 4)
            if cur_level >= level_789 and cur_level <= level_789+2 and max_level >= 10:
                print cur_level
                trade_size = round(trade_size*level_789_threshold, 4)

            print 'order: ', px, trade_size, side
            order_id, num_trade, try_again, _err = ftx_sell_order (api_key, api_secret, px, trade_size, cur, digits)
            print _err
            out_msg += ('%s: sell %s %s %s\n' % (market, px, trade_size, ftx_order_success(_err)))
            price += tick
            cur_level += 1
            
            if price > end_px:
                telegram_send_all(out_msg)

                print 'price >= end_px, so break loop'
                break


        elif side == 0: #bid
            px = round(price, digits)
            
            trade_size = round(random.uniform (start_qty, end_qty), 4)
            if cur_level >= level_789 and cur_level <= level_789+2 and max_level >= 10:
                print cur_level
                trade_size = round(trade_size*level_789_threshold, 4)
            
            print 'order: ', price, px, trade_size, side
            order_id, num_trade, try_again, _err = ftx_buy_order (api_key, api_secret, px, trade_size, cur, digits)
            print _err
            out_msg += ('%s: buy %s %s %s\n' % (market, px, trade_size, ftx_order_success(_err)))
            price -= tick
            cur_level += 1
            
            if price < end_px:
                telegram_send_all(out_msg)
                
                print 'price >= end_px, so break loop'
                break

        else:
            print "Error: ftx_config_fill_level"; exit(-1)

    telegram_send_all('done order')


def ftx_open_orders(api_key, api_secret, cur):
    
    cur = currency
    market = ftx_market(cur, '')
    
    query = { 'market': market }
    orig_result = ftx_request (api_key, api_secret, 'orders', 'GET', query, None)
    result = orig_result.get('result', None)

    if result is None:
        return None

    return orig_result


def ftx_cancel_all(side, start_px, end_px, chat_id, api_key, api_secret, exchange, currency, base_cur):
    
    cur = currency
    market = ftx_market(cur, '')
    
    if side == 'sell':
        pass
    elif side == 'buy':
        pass
    else:
        print 'ftx_cancel_all fail'
        return

    telegram_send_all('ftx wait! do not touch! get open orders')
    
    orig_result = ftx_open_orders(api_key, api_secret, cur)
    result = orig_result.get('result', None)

    if result is None:
        telegram_send_all ('failed: no orders or server problem, Check, try again')
        return

    orderData = []
    out_msg = ''
    
    for order in result:

        if stop_threads:
            return

        #print order['type'], order['price'], order['qty'], order['orderId']
        print order['side'], order['price'], order['remainingSize'], order['id']
        if order['side'] == side:
            orderData.append([order['id'], order['side'], order['price']])
    
    for od_id in orderData:
        ordPrc = (float)(od_id[2])

        if stop_threads:
            return

        if start_px <= ordPrc and ordPrc <= end_px:
            success, _err = ftx_cancel_order (api_key, api_secret, [od_id[0], None], 1 if side=='ask' else 0, cur)
            out_msg += ('%s: cancel %s %s\n' %(market, ordPrc, ftx_order_success(_err)))
            #pass

    telegram_send_all (out_msg)
    telegram_send_all ('done cancel')


def ftx_openorders(chat_id, api_key, api_secret, exchange, currency, base_cur):
    
    cur = currency
    market = ftx_market(cur, '')
    
    telegram_send_all('wait! ftx open-orders')
    
    orig_result = ftx_open_orders(api_key, api_secret, cur)
    result = orig_result.get('result', None)
    
    orderData = []
    if result is None:
        telegram_send_all ('failed: no orders perhaps, Check, try again')
        return

    out_msg = ''

    fp = open('./openorders_%s.txt' % (cur), 'w')
    seq = 1
    for row in result:

        if stop_threads:
            return

        #print row['orderId'], row['type'], row['price'], row['qty']
        print row['id'], row['side'], row['price'], row['remainingSize']
        _line = str(seq)+' '+cur+' '+row['side']+' '+row['price']+' '+row['remainingSize']
        fp.write (_line+'\n')
        seq += 1
    
    fp.close()
    telegram_send_doc('./openorders_%s.txt' % (cur))


###############
urllib3.disable_warnings()
pd.set_option('precision', 8)
pd.set_option('display.precision', 8)

def telegram_send_young(msg):
    return

def telegram_send_all(msg):
    return

def init_session():
    session = requests.Session()
    retry = Retry (connect=1, backoff_factor=0.1)
    adapter = HTTPAdapter (max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    return session

_dict_url = { 'ftx': ['https://ftx.com/api/markets/%s/orderbook?depth=10', ''] }

api_key = ""; api_secret = ""

stop_threads = False
session = init_session()

print ftx_book('ftx', 'BTC', None, session)
print ftx_balance(api_key, api_secret, 'BTC')


exit()

