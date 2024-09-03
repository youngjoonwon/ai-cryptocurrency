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

from config_tele_trade_bot import *

def roundup(f, n):
    return math.ceil(f * 10 ** n) / 10 ** n

########################################
def init_session():
    session = requests.Session()
    retry = Retry (connect=1, backoff_factor=0.1)
    adapter = HTTPAdapter (max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    return session
    

#################################
def short_cal_mid_price (gr_bid_level, gr_ask_level, group_t):
    
    #level = 5 
    
    if len(gr_bid_level) > 0 and len(gr_ask_level) > 0:
        bid_top_price = gr_bid_level.iloc[0].price
        bid_top_level_qty = gr_bid_level.iloc[0].quantity
        ask_top_price = gr_ask_level.iloc[0].price
        ask_top_level_qty = gr_ask_level.iloc[0].quantity
        mid_price = (bid_top_price + ask_top_price) * 0.5 #what is mid price?
    
        return (mid_price, bid_top_price, ask_top_price, bid_top_level_qty, ask_top_level_qty)

    else:
        print 'Error: serious short_cal_mid_price'
        return (-1, -1, -2, -1, -1)

def get_self_size_list (max_size, sector):
    
    gap = (float)(max_size / sector)
    _list = []
    for i in range(0,sector):
        _list.append([i*gap, (i+1)*gap])
    return _list

from dateutil.relativedelta import relativedelta

########## BITHUMB ###########
def bithumb_cancel_order(api, order_id, cur):
    
    #rgParams = {'currency': cur, 'order_id': order_id[0], 'type': order_id[1]}
    rgParams = {'order_currency': cur, 'order_id': (order_id[0]).encode('ascii'), 'type': (order_id[1]).encode('ascii'), 'payment_currency':'KRW'}
    result = api.xcoinApiCall("/trade/cancel", rgParams)
    
    #print result

    if result['status'] == '0000':
        #print '  order cancelled', order_id[2]
        return True, result
    #print '  Possible: bithumb_cancel_order may be empty', result['status']
    return False, result #fill or http error

def bithumb_buy_order(api, price, units, cur, digits):
    
    #tick = bithumb_tick(price)
    #digits = bithumb_digit(tick)
    if digits == 0: 
        price = int(price)

    rgParams = {'order_currency': cur, 'price': price, 'units': units, 'type': 'bid', 'payment_currency':'KRW'}
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

def bithumb_sell_order (api, price, units, cur, digits):
    
    #tick = bithumb_tick(price)
    #digits = bithumb_digit(tick)
    if digits == 0: 
        price = int(price)
    
    rgParams = {'order_currency': cur, 'price': price, 'units': units, 'type': 'ask', 'payment_currency':'KRW'}
    result = api.xcoinApiCall("/trade/place", rgParams)

    try_again = False 
    #order_id = 0
    order_id = None 
    num_trade = 0
    if result['status'] == '0000':
        order_id = result['order_id']
        #print result
        #num_trade = len (result['data'])
        num_trade = 1
    else:
        try_again = True

    #elif result['status'] == '5600':
    #    try_again = True
    #    print result
    #else:
    #    print result

    #    print '  ', result
    #else:
    #    print '  Error: bithumb_sell_order', result

    return order_id, num_trade, try_again, result

def bithumb_init_api():
    api = XCoinAPI(api_key, api_secret);
    return api

def bithumb_balance(api, cur):
    
    rgParams = {'currency': cur}
    result = api.xcoinApiCall("/info/balance", rgParams)

    #print result
    
    total_currency = total_krw = in_use_currency = -1.0
    if result['status'] != '0000':
        #print 'Error: bithumb_balance', result
        return -1, -1, -1
    
    data = result['data']
    
    #total_currency = ((float) (data['total_%s' % cur.lower()])) * 10000.0
    total_currency = ((float) (data['available_%s' % cur.lower()])) * 10000.0
    in_use_currency = ((float) (data['in_use_%s' % cur.lower()])) * 10000.0
    total_currency = (float) (math.floor(total_currency)) / 10000.0
    in_use_currency = (float) (math.floor(in_use_currency)) / 10000.0

    #total_krw = ((float) (data['in_use_krw'])) + ((float) (data['available_krw']))
    total_krw = (float) (data['total_krw'])
    
    #if in_use_currency > 0:
    #    msg = 'in_use >0 or -1:%s' % (_hostname)
    #    telegram_send_young (msg)
    #    telegram_send_ki (msg)

    #return total_currency, total_krw
    return total_currency, total_krw, in_use_currency


def bithumb_live_book(data, req_timestamp):
    #timestamp,price,type,quantity

    data = data['data']
    
    bids = (pd.DataFrame(data['bids'])).apply(pd.to_numeric,errors='ignore')
    #print bids
    bids = (bids.groupby('price').sum()).reset_index()
    bids.sort_values('price', ascending=False, inplace=True)
    bids = bids.reset_index(); del bids['index']
    bids['type'] = 0

    asks = (pd.DataFrame(data['asks'])).apply(pd.to_numeric,errors='ignore')
    #print asks
    asks = (asks.groupby('price').sum()).reset_index()
    asks.sort_values('price', ascending=True, inplace=True)
    asks['type'] = 1 
    
    #print bids
    #print asks

    #return bids.head(5), asks.head(5)
    return bids, asks

def bithumb_book(ex, currency, req_timestamp, session):

    #session = init_session()
    
    url = _dict_url[ex][0]
    try:
        book = (session.get(url % currency, verify=False, timeout=1)).json()
    except:
        return None, None
    
    if not book:
        return None, None

    bids, asks = bithumb_live_book(book, req_timestamp)
    
    return bids, asks

def bithumb_tick (px):
    
    if 0 < px and px < 1.0:
        return 0.0001
    elif 1 <= px and px < 10.0:
        return 0.001
    elif 10.0 <= px and px < 100.0:
        return 0.01
    elif 100.0 <= px and px < 1000.0:
        return 0.1
    elif 1000.0 <= px and px < 5000.0:
        return 1
    elif 5000.0 <= px and px < 10000.0:
        return 5
    elif 10000.0 <= px and px < 50000.0:
        return 10
    elif 50000.0 <= px and px < 100000.0:
        return 50
    elif 100000.0 <= px and px < 500000.0:
        return 100
    elif 500000.0 <= px and px < 1000000.0:
        return 500
    elif px >= 1000000.0:
        return 1000

def bithumb_digit (tick):
    str_tick = decimal.Decimal('%s' % tick)
    return abs(str_tick.as_tuple().exponent)

def bithumb_market(currency, base_cur):

    market = base_cur + '-' + currency
    market = market.upper()
    
    return market

def bithumb_fill_range (side, start_qty, end_qty, start_px, end_px, tick, buy_first, level_treshold, chat_id, api, exchange, currency, base_cur):
    
    cur = currency
    market = bithumb_market(currency, base_cur)

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

    telegram_send_all('wait! do not touch! start order')
    
    _flag = buy_first
    
    tick = bithumb_tick(price)
    #tick = tick*10 #bithumb soc, BASIC
    tick = tick*2 #bithumb soc, BASIC
    
    cur_level = 0
    max_level = int((round(abs(end_px - start_px), 3))/tick)
    level_789 = 6 
    level_789_threshold = level_treshold
    
    out_msg = ''
    while(1):
        
        if stop_threads:
            return
   
        #tick = bithumb_tick(price)
        digits = bithumb_digit(tick)
        print 'digits', digits

        if side == 1: #ask
            px = round(price, digits)
            #if digits == 0: 
            #    px = int(px)
            trade_size = round(random.uniform (start_qty, end_qty), 4)
            if cur_level >= level_789 and cur_level <= level_789+2 and max_level >= 10:
                print cur_level
                trade_size = round(trade_size*level_789_threshold, 4)

            print 'order: ', px, trade_size, side
            order_id, num_trade, try_again, _err = bithumb_sell_order (api, px, trade_size, cur, digits)
            print _err
            out_msg += ('%s: sell %s %s %s\n' % (market, px, trade_size, bithumb_order_success(_err)))
            price += tick
            cur_level += 1
            
            #time.sleep(0.01)
            if price > end_px:
                telegram_send_all(out_msg)

                print 'price >= end_px, so break loop'
                break


        elif side == 0: #bid
            px = round(price, digits)
            #if digits == 0:
            #    px = int(px)
            trade_size = round(random.uniform (start_qty, end_qty), 4)
            if cur_level >= level_789 and cur_level <= level_789+2 and max_level >= 10:
                print cur_level
                trade_size = round(trade_size*level_789_threshold, 4)
            
            print 'order: ', price, px, trade_size, side
            order_id, num_trade, try_again, _err = bithumb_buy_order (api, px, trade_size, cur, digits)
            print _err
            out_msg += ('%s: buy %s %s %s\n' % (market, px, trade_size, bithumb_order_success(_err)))
            price -= tick
            cur_level += 1
            
            #time.sleep(0.01)
            if price < end_px:
                telegram_send_all(out_msg)
                
                print 'price >= end_px, so break loop'
                break

        else:
            print "Error: coinzest_config_fill_level"; exit(-1)

    telegram_send_all('done order')

def bithumb_cancel_all(side, start_px, end_px, chat_id, api, exchange, currency, base_cur):
    
    cur = currency
    market = bithumb_market(currency, base_cur)
    
    if side == 'sell':
        side = 'ask'
    elif side == 'buy':
        side = 'bid'
    else:
        print 'bithumb_cancel_all fail'
        return

    telegram_send_all('wait! do not touch! get open orders')
    
    todayDate = datetime.datetime.today()
    startDate = (todayDate - relativedelta(days=91)).strftime('%s')
    
    rgParams = {'count': 1000, 'order_currency': cur, 'after': startDate}
    result = api.xcoinApiCall("/info/orders", rgParams)
   
    orderData = []
    if result['status'] != '0000':
        result = None
        
    if result is None:
        telegram_send_all ('failed: no orders or server problem, Check, try again')
        return

    if 'data' not in result:
        telegram_send_all ('failed: no orders or server problem, Check, try again')
        return

    out_msg = ''
    for row in result['data']:
        if stop_threads:
            return

        print row['order_id'], row['type'], row['price'], row['units']
        if row['type'] == side:
            orderData.append([row['order_id'], row['type'], row['price']])

    for od_id in orderData:
        ordPrc = (float)(od_id[2])
        
        if stop_threads:
            return

        if start_px <= ordPrc and ordPrc <= end_px:
            success, _err = bithumb_cancel_order(api, od_id, cur)
            out_msg += ('%s: cancel %s %s\n' %(market, ordPrc, bithumb_order_success(_err)))
            pass
    
    telegram_send_all (out_msg)
    telegram_send_all ('done cancel')

def bithumb_openorders(chat_id, api, exchange, currency, base_cur):
    
    cur = currency
    market = bithumb_market(currency, base_cur)
    
    #print market; sys.stdout.flush(); return

    telegram_send_all('wait! open-orders')
    
    todayDate = datetime.datetime.today()
    startDate = (todayDate - relativedelta(days=90)).strftime('%s')
    
    rgParams = {'count': 1000, 'order_currency': cur, 'after': startDate}
    result = api.xcoinApiCall("/info/orders", rgParams)
   
    orderData = []
    if result['status'] != '0000':
        result = None
        
    #print result
    if result is None:
        telegram_send_all ('failed: no orders perhaps, Check, try again')
        return

    if 'data' not in result:
        telegram_send_all ('failed: no orders or server problem, Check, try again')
        return

    out_msg = ''

    fp = open('./openorders_%s.txt' % (cur), 'w')
    seq = 1
    for row in result['data']:

        if stop_threads:
            return

        print row['order_id'], row['type'], row['price'], row['units']
        _line = str(seq)+' '+cur+' '+row['type']+' '+row['price']+' '+row['units']
        fp.write (_line+'\n')
        seq += 1
        #if row['type'] == side:
        #    orderData.append([row['order_id'], row['type'], row['price']])
    
    fp.close()
    telegram_send_doc('./openorders_%s.txt' % (cur))
    #telegram_send_all (out_msg)
    #telegram_send_all ('done cancel')


def bithumb_order_info(side, orderid, api, exchange, currency, base_cur):
     
    cur = currency
 
  
    if side == 'sell':
        side = 'ask'
    elif side == 'buy':
        side = 'bid'
    else:
        print 'bithumb_order_info fail'
        return
   
    todayDate = datetime.datetime.today()
    startDate = (todayDate - relativedelta(days=60)).strftime('%s')
    
    rgParams = {'count': 100, 'order_id': orderid, 'type': side, 'order_currency': cur, 'after': startDate}
    result = api.xcoinApiCall("/info/orders", rgParams)
    
    order_info = True
    try_again = False
    
    #print result

    if result['status'] != '0000':
        result = None
        
    if result is None:
        print 'failed: server problem'
        return False, 0, try_again, result

    if 'data' not in result:
        print 'failed: no orders'
        return order_info, 0, try_again, result

    for row in result['data']:
        #print row['order_id'], row['type'], row['price'], row['units']
        #if row['total'] is not None:
        if row['units'] != row['units_remaining']:
            success, _err = bithumb_cancel_order(api, [orderid, side], cur) 
            print 'order_info cancel', bithumb_order_success(_err)
            order_info = False

    return order_info, 0, try_again, result


def bithumb_nospread(side, trade_size, tick, frequency, chat_id, api, exchange, currency, base_cur):
    
    #global currency, cur, market
    
    cur = currency
    market = bithumb_market(currency, base_cur)
    session = init_session()
    
    telegram_send_all('wait! start nospread %s' % side)
    
    self_seq = 0
    seq = 0
    
    timestamp = last_update_time = datetime.datetime.now()
    
    #self_size_list = get_self_size_list (trade_size, 4)
    #self_size_list = self_size_list[-1:]
    
    od_list = []
    while 1:
        
        if stop_threads:
            for od in od_list:
                bithumb_cancel_order(api, [od,side], cur)
                print 'nospread cancel', cur, od
           
            od_list = []
            telegram_send_all('done! nospread %s' % side)
            return

        timestamp = datetime.datetime.now()
        if ((timestamp - last_update_time).total_seconds() < frequency) and (seq > 0):
            seq += 1
            continue
        __timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
       
        
        gr_bid_level, gr_ask_level = bithumb_book(exchange, currency, None, session)
        if gr_bid_level is None or gr_ask_level is None:
            print 'bithumb book is none'; sys.stdout.flush()
            continue

        mid_price, bid, ask, bid_qty, ask_qty = short_cal_mid_price(gr_bid_level, gr_ask_level, None)
        
        #gap = 0.1; trade_size = round(random.uniform (trade_size*(1-gap), trade_size*(1+gap)), 4)
        #gap = random.choice(self_size_list); trade_size = round(random.uniform(gap[0], gap[1]), 4)
        trade_size = round(trade_size, 4)

        last_update_time = datetime.datetime.now()
        seq += 1

        tick = bithumb_tick(mid_price)
        digits = bithumb_digit(tick)

        ask_bid_spread = round(ask - bid, digits)
        if ask_bid_spread <= 0:
            seq +=1
            print 'nospread <= 0'; sys.stdout.flush()
            continue
        
        if int(ask_bid_spread/tick) <= 1:
            seq +=1
            #print 'nospread <= 1'; sys.stdout.flush()
            continue
  
        for od in od_list:
            bithumb_cancel_order(api, [od, side], cur)
            print 'nospread cancel', cur, od
        od_list = []
        
        if side == 'bid':
            px = ask + (-1*tick)
        elif side == 'ask':
            px = bid + tick
        
        px = round(px, digits)
        
        order_id = None

        #print market, __timestamp, bid, ask; sys.stdout.flush()
        #sell_order_id, num_trade, try_again, _err = bithumb_sell_order (api, px, trade_size, cur)
            
        ##time.sleep(0.01)
            
        if side == 'bid':
            order_id, num_trade, try_again, _err = bithumb_buy_order (api, px, trade_size, cur, digits)
        elif side == 'ask':
            order_id, num_trade, try_again, _err = bithumb_sell_order (api, px, trade_size, cur, digits)

        print 'nospread order', __timestamp, side, order_id, px, trade_size; sys.stdout.flush()
        
        time.sleep(0.01)

        if order_id is not None:
            od_list.append(order_id)


def bithumb_order_success(_err):
    if _err is None:
        return False
    
    if _err['status'] == '0000':
        return True
    else:
        return False

def bithumb_self(trade_size, tick, frequency, final_seq, chat_id, api, exchange, currency, base_cur):
    
    #global currency, cur, market
    
    cur = currency
    market = bithumb_market(currency, base_cur)
    session = init_session()
    
    telegram_send_all('wait! do not touch! start self')
    
    self_seq = 0
    seq = 0
    
    timestamp = last_update_time = datetime.datetime.now()
    
    self_size_list = get_self_size_list (trade_size, 4)
    self_size_list = self_size_list[-1:]
    
    while 1:
        
        if stop_threads:
            return

        timestamp = datetime.datetime.now()
        if ((timestamp - last_update_time).total_seconds() < frequency) and (seq > 0):
            seq += 1
            continue
        __timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        
        if self_seq >= final_seq:
            print 'self heavy, exit after self_seq', self_seq; sys.stdout.flush()
            telegram_send_all ('done self')
            return

        self_seq += 1
       
        print market,
        
        gr_bid_level, gr_ask_level = bithumb_book(exchange, currency, None, session)
        if gr_bid_level is None or gr_ask_level is None:
            print 'bithumb book is none'; sys.stdout.flush()
            continue

        mid_price, bid, ask, bid_qty, ask_qty = short_cal_mid_price(gr_bid_level, gr_ask_level, None)
        
        
        #gap = 0.1; trade_size = round(random.uniform (trade_size*(1-gap), trade_size*(1+gap)), 4)
        gap = random.choice(self_size_list); trade_size = round(random.uniform(gap[0], gap[1]), 4)

        last_update_time = datetime.datetime.now()
        seq += 1

        tick = bithumb_tick(mid_price)
        digits = bithumb_digit(tick)

        ask_bid_spread = round(ask - bid, digits)
        if ask_bid_spread <= 0:
            seq +=1
            print 'bithumb spread <= 0'; sys.stdout.flush()
            continue
            
        if int(ask_bid_spread/tick) <= 1:
            seq +=1
            print 'int <= 1'; sys.stdout.flush()
            continue

        mid_price = round(mid_price, digits)

        #random_tick = random.randint(1,int(ask_bid_spread/tick)-1)
        #print market, -1*random_tick,int(ask_bid_spread/tick)-1; sys.stdout.flush()
        #px = ask + (-1*random_tick*tick)
        random_tick = 1
        px = bid + tick
 
        px = round(px, digits)
        
        if ((float)(px) <= 0):
            seq += 1
            print 'bithumb px negative'; sys.stdout.flush()
            continue
        
        if (ask-bid) <= (random_tick*tick):
            seq += 1
            print 'bithumb spread no good'
            continue
        
        if ask == (float)(px) or bid == (float)(px):
            seq += 1
            print 'ask or bid equal to px'; sys.stdout.flush()
            continue
            
        round_px = round ((float)(px), digits)
        if round (ask, digits) == round_px or round (bid, digits) == round_px:
            seq += 1
            print 'rounded ask or bid equal to px'; sys.stdout.flush()
            continue
            
        sell_order_id = buy_order_id = None

        print market, __timestamp, bid, ask; sys.stdout.flush()
        sell_order_id, num_trade, try_again, _err = bithumb_sell_order (api, px, trade_size, cur, digits)
            
        #time.sleep(0.01)
            
        buy_order_id, num_trade, try_again, _err = bithumb_buy_order (api, px, trade_size, cur, digits)
        
        print px, trade_size, sell_order_id, buy_order_id; sys.stdout.flush()

        time.sleep(0.01)

        if buy_order_id is not None:
            bithumb_cancel_order(api, [buy_order_id,'bid'], cur)
            print 'buy cancel'
        if sell_order_id is not None:
            bithumb_cancel_order(api, [sell_order_id,'ask'], cur)
            print 'sell cancel'
 
        telegram_send_all('%s: self %s %s %s' %(market, px, trade_size, __timestamp))
        #sys.stdout.flush()


def bithumb_clear_ask_orders(openorder_dict, api, exchange, currency, base_cur):

    ask_orders = openorder_dict.values()
    for od in ask_orders:
        success, _err = bithumb_cancel_order(api, [od[1], 'ask'], currency)
        print 'ask789 cancel', currency, od[0], bithumb_order_success(_err)
    return {}


def bithumb_fill_level_ask789 (widthpct, new_tick, openorder_dict, book, trade_size, api, exchange, currency, base_cur):
    
    cur = currency
    #market = bithumb_market(currency, base_cur)

    #max_level = 10 
    #ask_start_level = 8 

    #book = book.head(max_level)
    
    #missing_level = 0
    #print len(book.index), max_level
    #print book.to_string()
    
    #df = book[ask_start_level:ask_start_level+1]
    #print '\n' + df.to_string()
    
    side = int(book.iloc[0].type) #bid:0, ask:1
    
    if side == 0:
        print 'ask789 ask only, gr_ask_level'
        exit()

    #cancel everything, add new 789, 2019-03-13
    openorder_dict = bithumb_clear_ask_orders(openorder_dict, api, exchange, currency, base_cur)

    price = 0
    order_id = None
    #price = df.iloc[0].price
    price = px = book.iloc[0].price

    tick = bithumb_tick(price)
    digits = bithumb_digit(tick)

    #for x in range (0, max_level-ask_start_level):
    for x in range (3):
        if x == 0:
            px = round(px*(1+widthpct), digits)
        elif x == 1:
            px = round(px+new_tick, digits)
        elif x == 2:
            px = round(px+(new_tick*2), digits)
        else:
            print "error: fill_level_ask789 x"
            exit()
        
        if openorder_dict.get(px, None) is None:
            ask_trade_size = round(trade_size, 4)
            print 'bt, ask789, order: ', px, ask_trade_size
            order_id, num_trade, try_again, _err = bithumb_sell_order (api, px, ask_trade_size, cur, digits)
            if order_id is not None:
                openorder_dict.update( {px: (px,order_id)} )
                order_id = None
        
        #price -= tick # is it -?
    
    print '_ask789', sorted(openorder_dict.keys()); sys.stdout.flush()
    
    return openorder_dict


def bithumb_clear_bid_orders(openorder_dict, api, exchange, currency, base_cur):

    bid_orders = openorder_dict.values()
    for od in bid_orders:
        success, _err = bithumb_cancel_order(api, [od[1], 'bid'], currency)
        print 'bid789 cancel', currency, od[0], bithumb_order_success(_err)
    return {}

def bithumb_fill_level_bid789 (widthpct, new_tick, openorder_dict, book, trade_size, api, exchange, currency, base_cur):
    
    cur = currency

    #missing_level = 0
    #print len(book.index), max_level
    #print book.to_string()
    
    #df = book[bid_start_level:bid_start_level+1]
    #print '\n' + df.to_string()
    
    side = int(book.iloc[0].type) #bid:0, ask:1
    
    if side == 1:
        print 'bid789 bid only, gr_bid_level'
        exit()

    #cancel everything, add new 789, 2019-03-13
    openorder_dict = bithumb_clear_bid_orders(openorder_dict, api, exchange, currency, base_cur)

    price = 0
    order_id = None
    #price = df.iloc[0].price
    price = px = book.iloc[0].price

    tick = bithumb_tick(price)
    digits = bithumb_digit(tick)

    #for x in range (0, max_level-bid_start_level):
    for x in range (3):
        if x == 0:
            px = round(px*(1-widthpct), digits)
        elif x == 1:
            px = round(px-new_tick, digits)
        elif x == 2:
            px = round(px-(new_tick*2), digits)
        else:
            print "error: fill_level_ask789 x"
            exit()
 
        if openorder_dict.get(px, None) is None:
            bid_trade_size = round(trade_size, 4)
            print 'bt, bid789, order: ', px, bid_trade_size
            order_id, num_trade, try_again, _err = bithumb_buy_order (api, px, bid_trade_size, cur, digits)
            if order_id is not None:
                openorder_dict.update( {px: (px,order_id)} )
                order_id = None

        #price -= tick
    
    #if stop_threads:
    #    openorder_dict = bithumb_clear_bid_orders(openorder_dict, api, exchange, currency, base_cur)

    print '_bid789', sorted(openorder_dict.keys()); sys.stdout.flush()
    
    return openorder_dict


def bithumb_sellmm(qtymult, widthpct, new_tick, trade_size, tick, frequency, chat_id, api, exchange, currency, base_cur):
    
    cur = currency
    market = bithumb_market(currency, base_cur)
   
    telegram_send_all('wait! start sellMM')
    
    self_seq = 0
    seq = 0
    
    timestamp = last_update_time = datetime.datetime.now()
    session = init_session()
    
    out_orders = {}
    openorder_dict = {} #orders in bid789
    last_bid = 0.0
    total_currency = total_krw = in_use_currency = 0.0

    while 1:
        
        if stop_threads:

            od_list = out_orders.values()
            for od in od_list:
                bithumb_cancel_order(api, [od[1],'ask'], cur)
                print 'cancel', cur, od[0]
            
            bithumb_clear_bid_orders(openorder_dict, api, exchange, currency, base_cur)
            return

        timestamp = datetime.datetime.now()
        if ((timestamp - last_update_time).total_seconds() < frequency) and (seq > 0):
            seq += 1
            continue
        __timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        total_currency, total_krw, in_use_currency = bithumb_balance(api, cur)
        gr_bid_level, gr_ask_level = bithumb_book(exchange, currency, None, session)
        
        if gr_bid_level is None or gr_ask_level is None:
            print 'bithumb book is none'; sys.stdout.flush()
            continue
        last_update_time = datetime.datetime.now()
        
        seq += 1

        mid_price, bid, ask, bid_qty, ask_qty = short_cal_mid_price(gr_bid_level, gr_ask_level, None)
        
        tick = bithumb_tick(ask)
        digits = bithumb_digit(tick)

        ask = round(ask, digits)
        px = ask
        
        ### TEST
        #if qtymult != 0:
        #    bid_trade_size = trade_size * qtymult
        #    openorder_dict = bithumb_fill_level_bid789 (widthpct, new_tick, openorder_dict, gr_bid_level, bid_trade_size, api, exchange, currency, base_cur)
        #print total_currency, total_krw; print gr_bid_level; print gr_ask_level
        #print tick, digits, px; continue
        ###

        #print 'sellmm ', px, trade_size; sys.stdout.flush()

        if ((float)(px) <= 0):
            print 'bithumb px negative'; sys.stdout.flush()
            continue
        
        temp_qty = trade_size
        if ((float)(px) >= 200):
            trade_size = round(temp_qty * 1.5, 4)
        elif ((float)(px) >= 300):
            trade_size = round(temp_qty * 3.0, 4)
        elif ((float)(px) >= 400):
            trade_size = round(temp_qty * 6.0, 4)
        elif ((float)(px) >= 500):
            trade_size = round(temp_qty * 10.0, 4)


        if trade_size > 0:

            order_id = None
            order_history = out_orders.get(px, None)
            if order_history is None:
                order_id, num_trade, try_again, _err = bithumb_sell_order (api, px, trade_size, cur, digits)
                if order_id is None:
                    continue
                out_orders[px] = (px, order_id)
                print 'sellmm ', px, trade_size, __timestamp; sys.stdout.flush()
            else:
                order_info, tmp, try_again, _err = bithumb_order_info('sell', order_history[1], api, exchange, currency, base_cur)
                if order_info is False:
                    order_id, num_trade, try_again, _err = bithumb_sell_order (api, px, trade_size, cur, digits)
                    if order_id is None:
                        continue
                    del out_orders[px]
                    out_orders[px] = (px, order_id)
                    print 'check sellmm ', px, trade_size, __timestamp; sys.stdout.flush()
       
            if stop_threads:
                od_list = out_orders.values()
                for od in od_list:
                    bithumb_cancel_order(api, [od[1],'ask'], cur)
                    print 'cancel', cur, od[0]

                bithumb_clear_bid_orders(openorder_dict, api, exchange, currency, base_cur)
                return

            od_list = out_orders.values()
            for od in od_list:
                if (float)(od[0]) != ask:
                    bithumb_cancel_order(api, [od[1],'ask'], cur)
                    del out_orders[od[0]]
                    print 'cancel', cur, od[0]
        
        
        if qtymult != 0:
            if last_bid != bid:
                bid_trade_size = trade_size * qtymult
                openorder_dict = bithumb_fill_level_bid789 (widthpct, new_tick, openorder_dict, gr_bid_level, bid_trade_size, api, exchange, currency, base_cur)
 
        
        ''' 
        if last_bid != bid:
            #total_currency, total_krw, in_use_currency = bithumb_balance(api, cur)
            if currency == 'BASIC': #BASIC
                if total_krw > 698800000: #698943377
                    print 'bid789 total_krw: ', total_krw
                    bid_trade_size = 25000  #CONFIG SIZE
                    openorder_dict = bithumb_fill_level_bid789 (openorder_dict, gr_bid_level, bid_trade_size, api, exchange, currency, base_cur)
                else:
                    print 'NObid789 total_krw: ', total_krw
                    openorder_dict = bithumb_clear_bid_orders(openorder_dict, api, exchange, currency, base_cur)
        '''
        last_bid = bid


def bithumb_sellmmimp(qtymult, widthpct, new_tick, trade_size, tick, frequency, chat_id, api, exchange, currency, base_cur):
    
    cur = currency
    market = bithumb_market(currency, base_cur)
   
    telegram_send_all('wait! start sellMMIMP')
    
    self_seq = 0
    seq = 0
    
    timestamp = last_update_time = datetime.datetime.now()
    session = init_session()
    
    out_orders = {}
    openorder_dict = {} #orders in bid789
    last_bid = 0.0
    total_currency = total_krw = in_use_currency = 0.0

    while 1:
        
        if stop_threads:

            od_list = out_orders.values()
            for od in od_list:
                bithumb_cancel_order(api, [od[1],'ask'], cur)
                print 'cancel', cur, od[0]
            
            bithumb_clear_bid_orders(openorder_dict, api, exchange, currency, base_cur)
            return

        timestamp = datetime.datetime.now()
        if ((timestamp - last_update_time).total_seconds() < frequency) and (seq > 0):
            seq += 1
            continue
        __timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        total_currency, total_krw, in_use_currency = bithumb_balance(api, cur)
        gr_bid_level, gr_ask_level = bithumb_book(exchange, currency, None, session)
        
        if gr_bid_level is None or gr_ask_level is None:
            print 'bithumb book is none'; sys.stdout.flush()
            continue
        last_update_time = datetime.datetime.now()
        
        seq += 1

        mid_price, bid, ask, bid_qty, ask_qty = short_cal_mid_price(gr_bid_level, gr_ask_level, None)
        
        tick = bithumb_tick(ask)
        digits = bithumb_digit(tick)

        ask = round(ask, digits)
        px = ask
        
        ask_bid_spread = round(ask - bid, digits)
        if ask_bid_spread > tick:
            px = round (ask-tick, digits)
        

        if ((float)(px) <= 0):
            print 'bithumb px negative'; sys.stdout.flush()
            continue

        if trade_size > 0:
            
            od_list = out_orders.values()
            for od in od_list:
                #if (float)(od[0]) != ask:
                if (float)(od[0]) < ask or (float)(od[0]) > ask:
                    bithumb_cancel_order(api, [od[1],'ask'], cur)
                    del out_orders[od[0]]
                    print 'cancel', cur, od[0]
                else:
                    #print 'sellmmimp: px == ask', cur, od[0]
                    px = round ((float)(od[0]), digits)


            order_id = None
            order_history = out_orders.get(px, None)
            if order_history is None:
                order_id, num_trade, try_again, _err = bithumb_sell_order (api, px, trade_size, cur, digits)
                if order_id is None:
                    continue
                out_orders[px] = (px, order_id)
                print 'sellmmimp ', px, trade_size, __timestamp; sys.stdout.flush()
            else:
                order_info, tmp, try_again, _err = bithumb_order_info('sell', order_history[1], api, exchange, currency, base_cur)
                if order_info is False:
                    order_id, num_trade, try_again, _err = bithumb_sell_order (api, px, trade_size, cur, digits)
                    if order_id is None:
                        continue
                    del out_orders[px]
                    out_orders[px] = (px, order_id)
                    print 'check sellmmimp ', px, trade_size, __timestamp; sys.stdout.flush()
       
            if stop_threads:
                od_list = out_orders.values()
                for od in od_list:
                    bithumb_cancel_order(api, [od[1],'ask'], cur)
                    print 'cancel', cur, od[0]

                bithumb_clear_bid_orders(openorder_dict, api, exchange, currency, base_cur)
                return
            
            '''
            od_list = out_orders.values()
            for od in od_list:
                if (float)(od[0]) != ask:
                    bithumb_cancel_order(api, [od[1],'ask'], cur)
                    del out_orders[od[0]]
                    print 'cancel', cur, od[0]
            '''
        
        #if qtymult != 0:
        #    if last_bid != bid:
        #        bid_trade_size = trade_size * qtymult
        #        openorder_dict = bithumb_fill_level_bid789 (widthpct, new_tick, openorder_dict, gr_bid_level, bid_trade_size, api, exchange, currency, base_cur)
 
        
        last_bid = bid



def bithumb_twap(side, tick, frequency, chat_id, api, exchange, currency, base_cur):
    
    cur = currency
    market = bithumb_market(currency, base_cur)
    
    telegram_send_all('wait! start %s twap' % (side))
    
    price = 0.0
    if side == 'sell':
        side = 1
    elif side == 'buy':
        side = 0
    else:
        print 'Error: twap side wrong'; exit(-1)

    seq = 0
    out_msg = ''

    timestamp = last_update_time = datetime.datetime.now()
    session = init_session()
    
    
    while 1:
        
        if stop_threads:
            return

        timestamp = datetime.datetime.now()
        if ((timestamp - last_update_time).total_seconds() < frequency) and (seq > 0):
            seq += 1
            continue
        __timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        gr_bid_level, gr_ask_level = bithumb_book(exchange, currency, None, session)
        
        if gr_bid_level is None or gr_ask_level is None:
            print 'bithumb book is none'; sys.stdout.flush()
            continue
        last_update_time = datetime.datetime.now()
        
        seq += 1
        
        ### TEST
        #print gr_bid_level
        #print gr_ask_level; exit()
        ###

        mid_price, bid, ask, bid_qty, ask_qty = short_cal_mid_price(gr_bid_level, gr_ask_level, None)
        
        tick = bithumb_tick(mid_price)
        digits = bithumb_digit(tick)

        order_id = None
        qty_ratio = 0.5 

        if side == 1: #ask
            px = round(bid, digits)
            trade_size = round(bid_qty*qty_ratio, 1)
            if trade_size < 10000:
                trade_size = round(bid_qty, 4)
                #trade_size = bid_qty
            if bid_qty <= 1000:
                trade_size = round(1000.0, 4)

            print 'twap order: ', px, trade_size, side
            order_id, num_trade, try_again, _err = bithumb_sell_order (api, px, trade_size, cur, digits)
            out_msg = '%s: sell TWAP %s %s %s\n' % (market, px, trade_size, bithumb_order_success(_err))
            telegram_send_all(out_msg)
            
            #time.sleep(0.01)
            if order_id is not None:
                success, _err = bithumb_cancel_order(api, [order_id, 'ask'], cur)

        elif side == 0: #bid
            px = round(ask, digits)
            trade_size = round(ask_qty*qty_ratio, 1)
            if trade_size < 10000:
                trade_size = round(ask_qty, 4)
                #trade_size = ask_qty
            if ask_qty <= 1000:
                trade_size = round(1000.0, 4)

            print 'twap order: ', px, trade_size, side
            order_id, num_trade, try_again, _err = bithumb_buy_order (api, px, trade_size, cur, digits)
            out_msg = '%s: buy TWAP %s %s %s\n' % (market, px, trade_size, bithumb_order_success(_err))
            telegram_send_all(out_msg)
            
            #time.sleep(0.01)
            if order_id is not None:
                success, _err = bithumb_cancel_order(api, [order_id, 'bid'], cur)

        else:
            print "Error: twap ", side; exit(-1)

        #continue from here

def bithumb_buymm(qtymult, widthpct, new_tick, trade_size, tick, frequency, chat_id, api, exchange, currency, base_cur):
    
    cur = currency
    market = bithumb_market(currency, base_cur)
   
    telegram_send_all('wait! start buyMM')
    
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
                bithumb_cancel_order(api, [od[1],'bid'], cur)
                print 'cancel', cur, od[0]
            #
            bithumb_clear_ask_orders(openorder_dict, api, exchange, currency, base_cur)
            return

        timestamp = datetime.datetime.now()
        if ((timestamp - last_update_time).total_seconds() < frequency) and (seq > 0):
            seq += 1
            continue
        __timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        total_currency, total_krw, in_use_currency = bithumb_balance(api, cur)
        gr_bid_level, gr_ask_level = bithumb_book(exchange, currency, None, session)
        
        ### TEST
        if qtymult != 0:
            ask_trade_size = trade_size * qtymult
            openorder_dict = bithumb_fill_level_ask789 (widthpct, new_tick, openorder_dict, gr_ask_level, ask_trade_size, api, exchange, currency, base_cur)
        #print total_currency, total_krw; print gr_bid_level; print gr_ask_level
        ###

        if gr_bid_level is None or gr_ask_level is None:
            print 'bithumb book is none'; sys.stdout.flush()
            continue
        last_update_time = datetime.datetime.now()
        
        seq += 1
        #continue

        mid_price, bid, ask, bid_qty, ask_qty = short_cal_mid_price(gr_bid_level, gr_ask_level, None)
        
        tick = bithumb_tick(bid)
        digits = bithumb_digit(tick)

        bid = round(bid, digits)
        px = bid 
        
        print 'buymm ', px, trade_size; sys.stdout.flush()

        if ((float)(px) <= 0):
            print 'bithumb px negative'; sys.stdout.flush()
            continue

        if trade_size > 0:

            order_id = None
            order_history = out_orders.get(px, None)
            if order_history is None:
                order_id, num_trade, try_again, _err = bithumb_buy_order (api, px, trade_size, cur, digits)
                if order_id is None:
                    continue
                out_orders[px] = (px, order_id)
                print 'buymm ', px, trade_size, __timestamp; sys.stdout.flush()
            else:
                #
                order_info, tmp, try_again, _err = bithumb_order_info('buy', order_history[1], api, exchange, currency, base_cur)
                if order_info is False:
                    order_id, num_trade, try_again, _err = bithumb_buy_order (api, px, trade_size, cur, digits)
                    if order_id is None:
                        continue
                    del out_orders[px]
                    out_orders[px] = (px, order_id)
                    print 'check buymm ', px, trade_size, __timestamp; sys.stdout.flush()
       
            if stop_threads:
                od_list = out_orders.values()
                for od in od_list:
                    bithumb_cancel_order(api, [od[1],'bid'], cur)
                    print 'cancel', cur, od[0]
                #
                bithumb_clear_ask_orders(openorder_dict, api, exchange, currency, base_cur)
                return

            od_list = out_orders.values()
            for od in od_list:
                if (float)(od[0]) != bid:
                    bithumb_cancel_order(api, [od[1],'bid'], cur)
                    del out_orders[od[0]]
                    print 'cancel', cur, od[0]
        
        #if total_krw < 450690051:
        if total_krw < 0:
            od_list = out_orders.values()
            for od in od_list:
                bithumb_cancel_order(api, [od[1],'bid'], cur)
                print 'cancel', cur, od[0]
            bithumb_clear_ask_orders(openorder_dict, api, exchange, currency, base_cur)
            return
        
        ##should be ask??
        #if last_bid != bid:
        #    if currency == 'BASIC': #BASIC
        #        if total_krw > 500690051:
        #            print 'ask789 total_krw: ', total_krw
        #            ask_trade_size = 10000  #CONFIG SIZE
        #            openorder_dict = bithumb_fill_level_ask789 (openorder_dict, gr_ask_level, ask_trade_size, api, exchange, currency, base_cur)
        #        else:
        #            print 'NOask789total_krw: ', total_krw
        #            openorder_dict = bithumb_clear_ask_orders(openorder_dict, api, exchange, currency, base_cur)
      
        #NOT THIS ONE
        ##changed to bid789
        #if last_bid != bid:
        #    total_currency, total_krw, in_use_currency = bithumb_balance(api, cur)
        #    if currency == 'BASIC': #BASIC
        #        if total_krw > 189037003:
        #            print 'bid789 total_krw: ', total_krw
        #            bid_trade_size = 20000  #CONFIG SIZE
        #            openorder_dict = bithumb_fill_level_bid789 (openorder_dict, gr_bid_level, bid_trade_size, api, exchange, currency, base_cur)
        #        else:
        #            print 'NObid789 total_krw: ', total_krw
        #            openorder_dict = bithumb_clear_bid_orders(openorder_dict, api, exchange, currency, base_cur)
        
        
        last_bid = bid


def bithumb_buymmimp(qtymult, widthpct, new_tick, trade_size, tick, frequency, chat_id, api, exchange, currency, base_cur):
    
    cur = currency
    market = bithumb_market(currency, base_cur)
   
    telegram_send_all('wait! start buyMMIMP')
    
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
                bithumb_cancel_order(api, [od[1],'bid'], cur)
                print 'cancel', cur, od[0]
            #
            bithumb_clear_ask_orders(openorder_dict, api, exchange, currency, base_cur)
            return

        timestamp = datetime.datetime.now()
        if ((timestamp - last_update_time).total_seconds() < frequency) and (seq > 0):
            seq += 1
            continue
        __timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        total_currency, total_krw, in_use_currency = bithumb_balance(api, cur)
        gr_bid_level, gr_ask_level = bithumb_book(exchange, currency, None, session)
        
        ### TEST
        #if qtymult != 0:
        #    ask_trade_size = trade_size * qtymult
        #    openorder_dict = bithumb_fill_level_ask789 (widthpct, new_tick, openorder_dict, gr_ask_level, ask_trade_size, api, exchange, currency, base_cur)
        #print total_currency, total_krw; print gr_bid_level; print gr_ask_level
        ###

        if gr_bid_level is None or gr_ask_level is None:
            print 'bithumb book is none'; sys.stdout.flush()
            continue
        last_update_time = datetime.datetime.now()
        
        seq += 1
        #continue

        mid_price, bid, ask, bid_qty, ask_qty = short_cal_mid_price(gr_bid_level, gr_ask_level, None)
        
        tick = bithumb_tick(bid)
        digits = bithumb_digit(tick)

        bid = round(bid, digits)
        px = bid 
        
        ask_bid_spread = round(ask - bid, digits)
        if ask_bid_spread > tick:
            px = round(bid+tick, digits)

        #print 'buymmimp ', px, trade_size; sys.stdout.flush()

        if ((float)(px) <= 0):
            print 'bithumb px negative'; sys.stdout.flush()
            continue

        if trade_size > 0:
            
            od_list = out_orders.values()
            for od in od_list:
                #if (float)(od[0]) != bid:
                if (float)(od[0]) < bid or (float)(od[0]) > bid:
                    bithumb_cancel_order(api, [od[1],'bid'], cur)
                    del out_orders[od[0]]
                    print 'cancel', cur, od[0]
                else:
                    #print 'buymmimp: px == bid', cur, od[0]
                    px = round ((float)(od[0]), digits)

            order_id = None
            order_history = out_orders.get(px, None)
            if order_history is None:
                order_id, num_trade, try_again, _err = bithumb_buy_order (api, px, trade_size, cur, digits)
                if order_id is None:
                    continue
                out_orders[px] = (px, order_id)
                print 'buymmimp ', px, trade_size, __timestamp; sys.stdout.flush()
            else:
                #
                order_info, tmp, try_again, _err = bithumb_order_info('buy', order_history[1], api, exchange, currency, base_cur)
                if order_info is False:
                    order_id, num_trade, try_again, _err = bithumb_buy_order (api, px, trade_size, cur, digits)
                    if order_id is None:
                        continue
                    del out_orders[px]
                    out_orders[px] = (px, order_id)
                    print 'check buymmimp ', px, trade_size, __timestamp; sys.stdout.flush()
       
            if stop_threads:
                od_list = out_orders.values()
                for od in od_list:
                    bithumb_cancel_order(api, [od[1],'bid'], cur)
                    print 'cancel', cur, od[0]
                #
                bithumb_clear_ask_orders(openorder_dict, api, exchange, currency, base_cur)
                return
            '''
            od_list = out_orders.values()
            for od in od_list:
                #if (float)(od[0]) != bid:
                if (float)(od[0]) < bid:
                    bithumb_cancel_order(api, [od[1],'bid'], cur)
                    del out_orders[od[0]]
                    print 'cancel', cur, od[0]
                else:
                    print 'buymmimp: px >= bid, no cancel', cur, od[0]
            '''
        
        if total_krw < 0:
            od_list = out_orders.values()
            for od in od_list:
                bithumb_cancel_order(api, [od[1],'bid'], cur)
                print 'cancel', cur, od[0]
            bithumb_clear_ask_orders(openorder_dict, api, exchange, currency, base_cur)
            return
        
        last_bid = bid



def bithumb_show(op, chat_id, api, exchange, currency, base_cur):
    
    cur = currency
    market = bithumb_market(currency, base_cur)
   
    telegram_send_all('wait! getting trade')
    
    if op == 'trade':

        seq = 1 
        result = None
        fp = open('./trade_%s_%s.txt' % (cur, exchange), 'w')

        #for offset in range(0,2000,40):
        for offset in range(0,40000,40):
            rgParams = {'offset': offset, 'count': 40, 'searchGb': 0, 'order_currency': cur}
            result = api.xcoinApiCall("/info/user_transactions", rgParams)

            if result['status'] != '0000':
                print 'error: failed to get trans'
                continue
            for row in result['data']:
                result_ms = pd.to_datetime((int)(row['transfer_date'])+(9*60*60*1000*1000),unit='us')
                
                if row['search'] == '1' or row['search'] == '2':
                    _line = str(seq)+' '+cur+' '+str(result_ms)+' '+row['search']+' '+row['price']+' '+row['units']+' '+row['fee']+' '+row['order_balance']+' '+row['payment_balance']
                    fp.write (_line+'\n')
                    seq += 1
            
            time.sleep(2)

    telegram_send_doc('./trade_%s_%s.txt' % (cur, exchange))
    #bot.sendDocument(chat_id, 'order.txt')

def bithumb_flash(tick, duration, chat_id, api, exchange, currency, base_cur):
    
    cur = currency
    market = bithumb_market(currency, base_cur)
    
    side = 1
    print duration
    telegram_send_all('wait! start flash for %d sec' % (duration))
    
    price = 0.0

    seq = 0
    out_msg = ''
    
    timestamp = last_update_time = datetime.datetime.now()
    session = init_session()
    
    while 1:
        
        if stop_threads:
            return

        if (last_update_time-timestamp).total_seconds() > duration:
            break
        __timestamp = last_update_time.strftime('%Y-%m-%d %H:%M:%S')
        
        gr_bid_level, gr_ask_level = bithumb_book(exchange, currency, None, session)
        
        if gr_bid_level is None or gr_ask_level is None:
            print 'bithumb book is none'; sys.stdout.flush()
            continue
        last_update_time = datetime.datetime.now()
        
        ### TEST
        #print gr_bid_level
        #print gr_ask_level; exit()
        ###

        mid_price, bid, ask, bid_qty, ask_qty = short_cal_mid_price(gr_bid_level, gr_ask_level, None)
        
        tick = bithumb_tick(bid)
        digits = bithumb_digit(tick)
       
        ask_bid_spread = round(ask - bid, digits)
        if ask_bid_spread <= 0:
            seq +=1
            print 'bithumb spread <= 0'; sys.stdout.flush()
            continue
        
        order_id = None
        qty_ratio = 0.1  # 10% of top bid_qty

        #start from here
        if side == 1: #ask
            px = round(bid+tick, digits)
            trade_size = round(bid_qty*qty_ratio, 1)

            #print 'flash order: ', px, trade_size, side, __timestamp
            order_id, num_trade, try_again, _err = bithumb_sell_order (api, px, trade_size, cur, digits)
            print 'flash order: ', px, trade_size, side, __timestamp, bithumb_order_success(_err)
            #out_msg = '%s: sell Flash %s %s %s\n' % (market, px, trade_size, bithumb_order_success(_err))
            
            time.sleep(0.2)
            
            if order_id is not None:
                success, _err = bithumb_cancel_order(api, [order_id, 'ask'], cur)
                print 'flash cancel order', _err 

            time.sleep(0.2)

        else:
            print "Error: flash ", side; exit(-1)

    telegram_send_all('wait! end flash for %d sec' % (duration))


#################################

############ UPBIT ##############
import jwt
import base64
import uuid

def upbit_order_success(_err):
    if _err is None:
        return False
    
    if _err['state'] == 'done' or _err['state'] == 'wait':
        return True
    else:
        return False

def upbit_live_book(data, req_timestamp):
    #timestamp,price,type,quantity

    data = data[0]
    df = (pd.DataFrame(data['orderbook_units'])).apply(pd.to_numeric,errors='ignore')
    
    bids = df.filter(['bid_price','bid_size'])
    bids.rename(columns = {'bid_price':'price', 'bid_size':'quantity'}, inplace=True)
    bids['type'] = 0
    #print bids

    asks = df.filter(['ask_price','ask_size'])
    asks.rename(columns = {'ask_price':'price', 'ask_size':'quantity'}, inplace=True)
    asks['type'] = 1 
    #print asks

    return bids, asks


def upbit_book(ex, currency, req_timestamp, session):
    
    base_cur = 'KRW'
    market = upbit_market(currency, base_cur)
 
    url = _dict_url[ex][0]
    try:
        #start_time = timeit.default_timer()
        book = (session.get(url % market, headers={ 'User-Agent': 'Mozilla/5.0' }, verify=False, timeout=1)).json()
    except:
        return None, None
    
    if book is None:
        return None, None

    if type(book) is not list:
        return None, None

    bids, asks = upbit_live_book(book, req_timestamp)

    return bids, asks

def upbit_tick (px):
    
    return 0.00000001

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

def upbit_digit (tick):
    str_tick = decimal.Decimal('%s' % tick)
    return abs(str_tick.as_tuple().exponent)

def upbit_request(api_key, api_secret, endpoint, method, query, params=None):
    
    url = "https://api.upbit.com" + endpoint
    body = ""
    auth_header = None
    payload = {}

    #if method == "POST" or method == 'DELETE':
    if method != "GET":
        
        query_string = urllib.urlencode(query).encode()
        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()
        
        payload = {
            "access_key": api_key,
            "nonce": str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512'
            }
    else: #'GET'

        payload = {
            "access_key": api_key,
            "nonce": str(uuid.uuid4())
            }

        if params:
            body = "?" + urllib.urlencode(params)
    
    #print payload
    jwt_token = jwt.encode(payload, api_secret, algorithm='HS256').decode('utf-8')
    authorize_token = 'Bearer {}'.format(jwt_token)
    auth_header = {"Authorization": authorize_token} 

    try:
        if method == "GET":
            
            
            response = requests.get(url, headers=auth_header)
            response = response.json()
            #print response
            
            return response

        elif method == "POST":
            response = requests.post(url, data=query, headers=auth_header)
            
            #print response.status_code
            #if response.status_code != 200:
            #    print 'within request', response; sys.stdout.flush()
            #    return None

            response = response.json()

            return response
        
        elif method == "DELETE":
            response = requests.delete(url, params = query, headers=auth_header)
            response = response.json()
            return response
        
        elif method == "GET-P": #order_info
            
            response = requests.get(url, params = query, headers=auth_header)
            response = response.json()
            return response
            
    except:
        return None


def upbit_market(currency, base_cur):
    
    if currency in ['BTC', 'ETH']:
        base_cur = 'KRW'
    else:
        base_cur = 'BTC'
    
    market = base_cur + '-' + currency
    market = market.upper()
    
    return market


def upbit_buy_order(api_key, api_secret, price, units, cur, digits):
    
    base_cur = ''
    market = upbit_market(cur, base_cur)
    
    query = { 'market': market,
            'side': 'bid',
            'volume': units,
            'price': price,
            'ord_type': 'limit'
            }
    
    try_again = False
    result = upbit_request (api_key, api_secret, '/v1/orders', 'POST', query, None)
    if result is None:
        return None, 0, True, result

    order_id = result.get('uuid', None)
    num_trade = result.get('trade_count', 0)
    
    #print 'buy order', result; sys.stdout.flush()
   
    if order_id is None:
        try_again = True

    return order_id, num_trade, try_again, result


def upbit_sell_order(api_key, api_secret, price, units, cur, digits):
    
    base_cur = ''
    market = upbit_market(cur, base_cur)
       
    query = { 'market': market,
            'side': 'ask',
            'volume': units,
            'price': price,
            'ord_type': 'limit'
            }
    
    #print query

    try_again = False
    result = upbit_request (api_key, api_secret, '/v1/orders', 'POST', query, None)
    if result is None:
        return None, 0, True, result

    order_id = result.get('uuid', None)
    num_trade = result.get('trade_count',0)
    
    #print 'sell order', result; sys.stdout.flush()

    if order_id is None:
        try_again = True

    return order_id, num_trade, try_again, result


def upbit_cancel_order(api_key, api_secret, order_id, is_ask, cur):
    
    query = { 'uuid': (order_id[0]).encode('ascii') }

    result = upbit_request (api_key, api_secret, '/v1/order', 'DELETE', query, None)
    
    #print 'upbit-cancel', result; sys.stdout.flush()
    
    if result is None:
        return False, result

    return True, result


def upbit_order_info(side, orderid, api_key, api_secret, exchange, currency, base_cur):
 
    cur = currency
   
    if side == 'sell':
        side = 1
    elif side == 'buy':
        side = 0
    else:
        print 'upbit_order_info fail'
        return
  
    query = { 'uuid': orderid.encode('ascii') }
    result = upbit_request (api_key, api_secret, '/v1/order', 'GET-P', query, None)

    order_info = True
    try_again = False
    
    #print payload
    #print result
    
    if result is None:
        print 'failed: server problem'
        return order_info, 0, try_again, result
    
    #remaining_volume = round((float)(result['remaining_volume']), 4)
    #volume = round((float)(result['volume']), 4)
    executed_volume = round((float)(result['executed_volume']), 4)

    #if remaining_volume >= 0.0 and remaining_volume < volume:
    if executed_volume > 0.0: #filled or partially filled
        success, _err = upbit_cancel_order(api_key, api_secret, [orderid, side], int(side), cur)
        print 'order_info cancel', upbit_order_success(_err)
        order_info = False

    return order_info, 0, try_again, result


def upbit_balance(api_key, api_secret, cur):
    
    result = upbit_request (api_key, api_secret, '/v1/accounts', 'GET', None) 
    
    total_currency = total_krw = in_use_currency = -1.0
    if result is None:
        #print 'Error: upbit_balance', result
        return -1, -1, -1
   
    if type(result) is not list:
        #if result.get('error') is None:
        return -1, -1, -1
    
    #print 'upbit balance', result; sys.stdout.flush()
    
    for account in result:
        if account['currency'] == cur:
            total_currency = ((float) (account['balance'])) * 10000.0
            total_currency = (float) (math.floor(total_currency)) / 10000.0
            in_use_currency = ((float) (account['locked'])) * 10000.0
            in_use_currency = (float) (math.floor(in_use_currency)) / 10000.0
        if account['currency'] == 'KRW':
            total_krw = (float)(account['balance']) + (float)(account['locked'])

    if total_currency == -1:
        total_currency = 0.0
        in_use_currency = 0.0
        #print 'Wrong: upbit_balance', result; sys.stdout.flush()
        #exit(-1)
    
    return total_currency, total_krw, in_use_currency


def upbit_twap(side, tick, frequency, twapMode, threshQty, chat_id, api_key, api_secret, exchange, currency, base_cur):
    
    cur = currency
    market = upbit_market(cur, base_cur)
    
    telegram_send_all('wait! start %s %s twap' % (exchange, side))
    
    price = 0.0
    if side == 'sell':
        side = 1
    elif side == 'buy':
        side = 0
    else:
        print 'Error: twap side wrong'; exit(-1)

    seq = 0
    out_msg = ''

    timestamp = last_update_time = datetime.datetime.now()
    session = init_session()
    
    while 1:
        
        if stop_threads:
            return

        timestamp = datetime.datetime.now()
        if ((timestamp - last_update_time).total_seconds() < frequency) and (seq > 0):
            seq += 1
            continue
        __timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        gr_bid_level, gr_ask_level = upbit_book(exchange, currency, None, session)
        
        if gr_bid_level is None or gr_ask_level is None:
            print 'upbit book is none'; sys.stdout.flush()
            continue
        last_update_time = datetime.datetime.now()
        
        seq += 1
        
        ### TEST
        #print gr_bid_level
        #print gr_ask_level; exit()
        ###

        mid_price, bid, ask, bid_qty, ask_qty = short_cal_mid_price(gr_bid_level, gr_ask_level, None)
        bid5Qty = gr_bid_level.iloc[0].quantity + gr_bid_level.iloc[1].quantity + gr_bid_level.iloc[2].quantity + gr_bid_level.iloc[3].quantity + gr_bid_level.iloc[4].quantity
        ask5Qty = gr_ask_level.iloc[0].quantity + gr_ask_level.iloc[1].quantity + gr_ask_level.iloc[2].quantity + gr_ask_level.iloc[3].quantity + gr_ask_level.iloc[4].quantity
        
        tick = upbit_tick(mid_price)
        digits = upbit_digit(tick)

        order_id = None
        qty_ratio = 0.5 

        if side == 1: #ask
            px = round(bid, digits)
            if twapMode == 0:
                trade_size = round(bid_qty*qty_ratio, 4)
                if trade_size < 10000:
                    trade_size = round(bid_qty, 4)
            elif twapMode == 1:
                trade_size = round(bid_qty, 4)
            elif twapMode == 2:
                if bid5Qty > threshQty:
                    trade_size = round(threshQty, 4)
                else:
                    continue

            if bid_qty <= 1000:
                trade_size = round(1000.0, 4)

            print 'twap order: ', px, trade_size, side
            order_id, num_trade, try_again, _err = upbit_sell_order (api_key, api_secret, px, trade_size, cur, digits)
            out_msg = '%s: sell TWAP %s %s %s\n' % (market, px, trade_size, upbit_order_success(_err))
            telegram_send_all(out_msg)
            
            #time.sleep(0.01)
            if order_id is not None:
                success, _err = upbit_cancel_order(api_key, api_secret, [order_id, 'ask'], 1, cur)


        elif side == 0: #bid
            px = round(ask, digits)
            if twapMode == 0:
                trade_size = round(ask_qty*qty_ratio, 4)
                if trade_size < 10000:
                    trade_size = round(ask_qty, 4)
            elif twapMode == 1:
                trade_size = round(ask_qty, 4)
            elif twapMode == 2:
                if ask5Qty > threshQty:
                    trade_size = round(ask_qty, 4)
                else:
                    continue

            if ask_qty <= 1000:
                trade_size = round(1000.0, 4)
            
            print 'twap order: ', px, trade_size, side
            order_id, num_trade, try_again, _err = upbit_buy_order (api_key, api_secret, px, trade_size, cur, digits)
            out_msg = '%s: buy TWAP %s %s %s\n' % (market, px, trade_size, upbit_order_success(_err))
            telegram_send_all(out_msg)
            
            #time.sleep(0.01)
            if order_id is not None:
                success, _err = upbit_cancel_order(api_key, api_secret, [order_id, 'bid'], 0, cur)

        else:
            print "Error: twap ", side; exit(-1)

        #continue from here


def upbit_clear_bid_orders(openorder_dict, api_key, api_secret, exchange, currency, base_cur):

    bid_orders = openorder_dict.values()
    for od in bid_orders:
        success, _err = upbit_cancel_order(api_key, api_secret, [od[1], 'bid'], 0, currency)
        print 'upbit cancel bid order', currency, od[0], upbit_order_success(_err)
    return {}

def upbit_clear_ask_orders(openorder_dict, api_key, api_secret, exchange, currency, base_cur):

    ask_orders = openorder_dict.values()
    for od in ask_orders:
        success, _err = upbit_cancel_order(api_key, api_secret, [od[1], 'ask'], 1, currency)
        print 'upbit cancel ask order', currency, od[0], upbit_order_success(_err)
    return {}


def upbit_buymm(qtymult, widthpct, new_tick, trade_size, tick, frequency, chat_id, api_key, api_secret, exchange, currency, base_cur):
    
    cur = currency
    market = upbit_market(cur, base_cur)
   
    telegram_send_all('wait! upbit start buyMM')
    
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
                upbit_cancel_order(api_key, api_secret, [od[1],'bid'], 0, cur)
                print 'cancel', cur, od[0]
            #
            upbit_clear_ask_orders(openorder_dict, api_key, api_secret, exchange, currency, base_cur)
            return

        timestamp = datetime.datetime.now()
        if ((timestamp - last_update_time).total_seconds() < frequency) and (seq > 0):
            seq += 1
            continue
        __timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        total_currency, total_krw, in_use_currency = upbit_balance(api_key, api_secret, cur)
        gr_bid_level, gr_ask_level = upbit_book(exchange, currency, None, session)
        
        
        if gr_bid_level is None or gr_ask_level is None:
            print 'upbit book is none'; sys.stdout.flush()
            continue
        last_update_time = datetime.datetime.now()
        
        seq += 1
        #continue

        mid_price, bid, ask, bid_qty, ask_qty = short_cal_mid_price(gr_bid_level, gr_ask_level, None)
        
        tick = upbit_tick(bid)
        digits = upbit_digit(tick)

        bid = round(bid, digits)
        px = bid
        
        #print 'buymm ', px, trade_size; sys.stdout.flush()

        if ((float)(px) <= 0):
            print 'upbit px negative'; sys.stdout.flush()
            continue

        if trade_size > 0:

            order_id = None
            order_history = out_orders.get(px, None)
            if order_history is None:
                order_id, num_trade, try_again, _err = upbit_buy_order (api_key, api_secret, px, trade_size, cur, digits)
                if order_id is None:
                    continue
                out_orders[px] = (px, order_id)
                print 'buymm ', exchange, px, trade_size, __timestamp; sys.stdout.flush()
            else:
                #
                order_info, tmp, try_again, _err = upbit_order_info('buy', order_history[1], api_key, api_secret, exchange, currency, base_cur)
                if order_info is False:
                    order_id, num_trade, try_again, _err = upbit_buy_order (api_key, api_secret, px, trade_size, cur, digits)
                    if order_id is None:
                        continue
                    del out_orders[px]
                    out_orders[px] = (px, order_id)
                    print 'check buymm ', exchange, px, trade_size, __timestamp; sys.stdout.flush()
       
            if stop_threads:
                od_list = out_orders.values()
                for od in od_list:
                    upbit_cancel_order(api_key, api_secret, [od[1],'bid'], 0, cur)
                    print 'cancel', cur, od[0]
                #
                upbit_clear_ask_orders(openorder_dict, api_key, api_secret, exchange, currency, base_cur)
                return

            od_list = out_orders.values()
            for od in od_list:
                if (float)(od[0]) != bid:
                    upbit_cancel_order(api_key, api_secret, [od[1],'bid'], 0, cur)
                    del out_orders[od[0]]
                    print 'cancel', cur, od[0]
                    
        ### TEST
        if qtymult != 0:
            if last_bid != bid:
                ask_trade_size = trade_size * qtymult
                openorder_dict = upbit_fill_level_ask789 (widthpct, new_tick, openorder_dict, gr_ask_level, ask_trade_size, api_key, api_secret, exchange, currency, base_cur)
        #print total_currency, total_krw; print gr_bid_level; print gr_ask_level
        ###
        
        last_bid = bid


def upbit_buymmimp(qtymult, widthpct, new_tick, trade_size, limitpx, pctrestart, tick, frequency, chat_id, api, exchange, currency, base_cur):
    
    cur = currency
    market = upbit_market(cur, base_cur)
   
    telegram_send_all('wait! upbit start buyMMIMP')
    
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
                upbit_cancel_order(api_key, api_secret, [od[1],'bid'], 0, cur)
                print 'cancel', cur, od[0]
            #
            upbit_clear_bid_orders(openorder_dict, api_key, api_secret, exchange, currency, base_cur)
            return

        timestamp = datetime.datetime.now()
        if ((timestamp - last_update_time).total_seconds() < frequency) and (seq > 0):
            seq += 1
            continue
        __timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        total_currency, total_krw, in_use_currency = upbit_balance(api_key, api_secret, cur)
        gr_bid_level, gr_ask_level = upbit_book(exchange, currency, None, session)
        
        ### TEST
        #if qtymult != 0:
        #    ask_trade_size = trade_size * qtymult
        #    openorder_dict = upbit_fill_level_ask789 (widthpct, new_tick, openorder_dict, gr_ask_level, ask_trade_size, api, exchange, currency, base_cur)
        #print total_currency, total_krw; print gr_bid_level; print gr_ask_level
        ###

        if gr_bid_level is None or gr_ask_level is None:
            print 'upbit book is none'; sys.stdout.flush()
            continue
        last_update_time = datetime.datetime.now()
        
        seq += 1
        #continue

        mid_price, bid, ask, bid_qty, ask_qty = short_cal_mid_price(gr_bid_level, gr_ask_level, None)
        bid_level2 = gr_bid_level.iloc[1].price
        
        tick = upbit_tick(bid)
        digits = upbit_digit(tick)

        bid = round(bid, digits)
        px = bid
        
        ask_bid_spread = round(ask - bid, digits)
        if ask_bid_spread > tick:
            px = round(bid+tick, digits)

        #print 'buymm ', px, trade_size; sys.stdout.flush()

        if ((float)(px) <= 0):
            print 'upbit px negative'; sys.stdout.flush()
            continue

        if (px > limitpx):
            limitpxreached = 1
            continue

        if limitpxreached == 1:
            if (px < (limitpx - (limitpx * pctrestart))):
                limitpxreached = 0
            else:
                continue

        if trade_size > 0:

            od_list = out_orders.values()
            for od in od_list:
                #if (float)(od[0]) != bid:
                if (float)(od[0]) < bid or (float)(od[0]) > bid:
                    upbit_cancel_order(api_key, api_secret, [od[1],'bid'], 0, cur)
                    del out_orders[od[0]]
                    print 'cancel', cur, od[0], bid_level2
                elif bid_level2 < (float)(od[0] - 1.0*tick):
                    upbit_cancel_order(api_key, api_secret, [od[1],'bid'], 0, cur)
                    del out_orders[od[0]]
                    print 'cancel', cur, od[0], bid_level2
                    px = round(bid_level2+tick, digits)
                else:
                    #print 'buymmimp: px == bid', cur, od[0]
                    px = round ((float)(od[0]), digits)
                    print 'buymmimp: px == bid', cur, od[0]

            order_id = None
            order_history = out_orders.get(px, None)
            if order_history is None:
                order_id, num_trade, try_again, _err = upbit_buy_order (api_key, api_secret, px, trade_size, cur, digits)
                if order_id is None:
                    continue
                out_orders[px] = (px, order_id)
                print 'buymmimp ', exchange, px, trade_size, __timestamp; sys.stdout.flush()
            else:
                #
                order_info, tmp, try_again, _err = upbit_order_info('buy', order_history[1], api_key, api_secret, exchange, currency, base_cur)
                if order_info is False:
                    order_id, num_trade, try_again, _err = upbit_buy_order (api_key, api_secret, px, trade_size, cur, digits)
                    if order_id is None:
                        continue
                    del out_orders[px]
                    out_orders[px] = (px, order_id)
                    print 'check buymmimp ', exchange, px, trade_size, __timestamp; sys.stdout.flush()
       
            if stop_threads:
                od_list = out_orders.values()
                for od in od_list:
                    upbit_cancel_order(api_key, api_secret, [od[1],'bid'], 0, cur)
                    print 'cancel', cur, od[0]
                #
                upbit_clear_bid_orders(openorder_dict, api_key, api_secret, exchange, currency, base_cur)
                return

        last_bid = bid


def upbit_sellmm(qtymult, widthpct, new_tick, trade_size, tick, frequency, chat_id, api_key, api_secret, exchange, currency, base_cur):
    
    cur = currency
    market = upbit_market(cur, base_cur)
    
    telegram_send_all('wait! upbit start sellMM')
    
    self_seq = 0
    seq = 0
    
    timestamp = last_update_time = datetime.datetime.now()
    session = init_session()
    
    out_orders = {}
    openorder_dict = {} #orders in bid789
    last_bid = 0.0
    total_currency = total_krw = in_use_currency = 0.0

    while 1:
        
        if stop_threads:

            od_list = out_orders.values()
            for od in od_list:
                upbit_cancel_order(api_key, api_secret, [od[1],'ask'], 1, cur)
                print 'cancel', cur, od[0]
            
            upbit_clear_bid_orders(openorder_dict, api_key, api_secret, exchange, currency, base_cur)
            return

        timestamp = datetime.datetime.now()
        if ((timestamp - last_update_time).total_seconds() < frequency) and (seq > 0):
            seq += 1
            continue
        __timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        total_currency, total_krw, in_use_currency = upbit_balance(api_key, api_secret, cur)
        gr_bid_level, gr_ask_level = upbit_book(exchange, currency, None, session)
        
        if gr_bid_level is None or gr_ask_level is None:
            print 'upbit book is none'; sys.stdout.flush()
            continue
        last_update_time = datetime.datetime.now()
        
        seq += 1

        mid_price, bid, ask, bid_qty, ask_qty = short_cal_mid_price(gr_bid_level, gr_ask_level, None)
        
        tick = upbit_tick(ask)
        digits = upbit_digit(tick)

        ask = round(ask, digits)
        px = ask
        
        #print 'sellmm ', px, trade_size; sys.stdout.flush()

        if ((float)(px) <= 0):
            print 'upbit px negative'; sys.stdout.flush()
            continue

        if trade_size > 0:

            order_id = None
            order_history = out_orders.get(px, None)
            if order_history is None:
                order_id, num_trade, try_again, _err = upbit_sell_order (api_key, api_secret, px, trade_size, cur, digits)
                if order_id is None:
                    continue
                out_orders[px] = (px, order_id)
                print 'sellmm ', exchange, px, trade_size, __timestamp; sys.stdout.flush()
            else:
                order_info, tmp, try_again, _err = upbit_order_info('sell', order_history[1], api_key, api_secret, exchange, currency, base_cur)
                if order_info is False:
                    order_id, num_trade, try_again, _err = upbit_sell_order (api_key, api_secret, px, trade_size, cur, digits)
                    if order_id is None:
                        continue
                    del out_orders[px]
                    out_orders[px] = (px, order_id)
                    print 'check sellmm ', exchange, px, trade_size, __timestamp; sys.stdout.flush()
       
            if stop_threads:
                od_list = out_orders.values()
                for od in od_list:
                    upbit_cancel_order(api_key, api_secret, [od[1],'ask'], 1, cur)
                    print 'cancel', cur, od[0]

                upbit_clear_bid_orders(openorder_dict, api_key, api_secret, exchange, currency, base_cur)
                return

            od_list = out_orders.values()
            for od in od_list:
                if (float)(od[0]) != ask:
                    upbit_cancel_order(api_key, api_secret, [od[1],'ask'], 1, cur)
                    del out_orders[od[0]]
                    print 'cancel', cur, od[0]
        
        
        if qtymult != 0:
            if last_bid != bid:
                bid_trade_size = trade_size * qtymult
                openorder_dict = upbit_fill_level_bid789 (widthpct, new_tick, openorder_dict, gr_bid_level, bid_trade_size, api_key, api_secret, exchange, currency, base_cur)
 
        
        last_bid = bid


def upbit_sellmmimp(qtymult, widthpct, new_tick, limitpx, pctrestart, trade_size, tick, frequency, chat_id, api, exchange, currency, base_cur):
    
    cur = currency
    market = upbit_market(cur, base_cur)
    
    telegram_send_all('wait! upbit start sellMM')
    
    self_seq = 0
    seq = 0
    
    timestamp = last_update_time = datetime.datetime.now()
    session = init_session()
    
    out_orders = {}
    openorder_dict = {} #orders in bid789
    last_bid = 0.0
    total_currency = total_krw = in_use_currency = 0.0

    while 1:
        
        if stop_threads:

            od_list = out_orders.values()
            for od in od_list:
                upbit_cancel_order(api_key, api_secret, [od[1],'ask'], 1, cur)
                print 'cancel', cur, od[0]
            
            upbit_clear_bid_orders(openorder_dict, api_key, api_secret, exchange, currency, base_cur)
            return

        timestamp = datetime.datetime.now()
        if ((timestamp - last_update_time).total_seconds() < frequency) and (seq > 0):
            seq += 1
            continue
        __timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        total_currency, total_krw, in_use_currency = upbit_balance(api_key, api_secret, cur)
        gr_bid_level, gr_ask_level = upbit_book(exchange, currency, None, session)
        
        if gr_bid_level is None or gr_ask_level is None:
            print 'upbit book is none'; sys.stdout.flush()
            continue
        last_update_time = datetime.datetime.now()
        
        seq += 1

        mid_price, bid, ask, bid_qty, ask_qty = short_cal_mid_price(gr_bid_level, gr_ask_level, None)
        ask_level2 = gr_ask_level.iloc[1].price
        
        tick = upbit_tick(ask)
        digits = upbit_digit(tick)

        ask = round(ask, digits)
        px = ask
        
        ask_bid_spread = round(ask - bid, digits)
        if ask_bid_spread > tick:
            px = round (ask-tick, digits)
 
        #print 'sellmm upbit', px, trade_size; sys.stdout.flush()

        if ((float)(px) <= 0):
            print 'upbit px negative'; sys.stdout.flush()
            continue

        if (px < limitpx):
            limitpxreached = 1
            continue

        if limitpxreached == 1:
            if (px > (limitpx + (limitpx * pctrestart))):
                limitpxreached = 0
            else:
                continue

        if trade_size > 0:
            
            od_list = out_orders.values()
            for od in od_list:
                if (float)(od[0]) < ask or (float)(od[0]) > ask:
                    upbit_cancel_order(api_key, api_secret, [od[1],'ask'], 1, cur)
                    del out_orders[od[0]]
                    print 'cancel', cur, od[0]
                elif ask_level2 > (float)(od[0] + 1.0*tick):
                    upbit_cancel_order(api_key, api_secret, [od[1],'ask'], 1, cur)
                    del out_orders[od[0]]
                    print 'cancel', cur, od[0]
                    px = round(ask_level2-tick, digits)
                else:
                    #print 'sellmmimp: px == ask', cur, od[0]
                    px = round ((float)(od[0]), digits)


            order_id = None
            order_history = out_orders.get(px, None)
            if order_history is None:
                order_id, num_trade, try_again, _err = upbit_sell_order (api_key, api_secret, px, trade_size, cur, digits)
                if order_id is None:
                    continue
                out_orders[px] = (px, order_id)
                print 'sellmmimp ', exchange, px, trade_size, __timestamp; sys.stdout.flush()
            else:
                order_info, tmp, try_again, _err = upbit_order_info('sell', order_history[1], api_key, api_secret, exchange, currency, base_cur)
                if order_info is False:
                    order_id, num_trade, try_again, _err = upbit_sell_order (api_key, api_secret, px, trade_size, cur, digits)
                    if order_id is None:
                        continue
                    del out_orders[px]
                    out_orders[px] = (px, order_id)
                    print 'check sellmmimp ', exchange, px, trade_size, __timestamp; sys.stdout.flush()
       
            if stop_threads:
                od_list = out_orders.values()
                for od in od_list:
                    upbit_cancel_order(api_key, api_secret, [od[1],'ask'], 1, cur)
                    print 'cancel', cur, od[0]

                upbit_clear_bid_orders(openorder_dict, api_key, api_secret, exchange, currency, base_cur)
                return

        last_bid = bid


def upbit_nospread(side, trade_size, tick, frequency, chat_id, api_key, api_secret, exchange, currency, base_cur):
    
    #global currency, cur, market
    
    cur = currency
    market = upbit_market(cur, base_cur)
    session = init_session()
    
    telegram_send_all('wait! coioone start nospread %s' % side)
    
    self_seq = 0
    seq = 0
    
    timestamp = last_update_time = datetime.datetime.now()
    
    
    od_list = []
    while 1:
        
        if stop_threads:
            for od in od_list:
                upbit_cancel_order(api_key, api_secret, [od,side], 1 if side=='ask' else 0, cur)
                print 'nospread cancel', cur, od
           
            od_list = []
            telegram_send_all('done! nospread %s' % side)
            return

        timestamp = datetime.datetime.now()
        if ((timestamp - last_update_time).total_seconds() < frequency) and (seq > 0):
            seq += 1
            continue
        __timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
       
        
        gr_bid_level, gr_ask_level = upbit_book(exchange, currency, None, session)
        if gr_bid_level is None or gr_ask_level is None:
            print 'upbit book is none'; sys.stdout.flush()
            continue

        mid_price, bid, ask, bid_qty, ask_qty = short_cal_mid_price(gr_bid_level, gr_ask_level, None)
        
        trade_size = round(trade_size, 4)

        last_update_time = datetime.datetime.now()
        seq += 1

        tick = upbit_tick(mid_price)
        digits = upbit_digit(tick)

        ask_bid_spread = round(ask - bid, digits)
        if ask_bid_spread <= 0:
            seq +=1
            print 'nospread <= 0'; sys.stdout.flush()
            continue
        
        if int(ask_bid_spread/tick) <= 1:
            seq +=1
            #print 'nospread <= 1'; sys.stdout.flush()
            continue
  
        for od in od_list:
            upbit_cancel_order(api_key, api_secret, [od, side], 1 if side=='ask' else 0, cur)
            print 'nospread cancel', cur, od
        od_list = []
        
        if side == 'bid':
            px = ask + (-1*tick)
        elif side == 'ask':
            px = bid + tick
        
        px = round(px, digits)
        
        order_id = None

        if side == 'bid':
            order_id, num_trade, try_again, _err = upbit_buy_order (api_key, api_secret, px, trade_size, cur, digits)
        elif side == 'ask':
            order_id, num_trade, try_again, _err = upbit_sell_order (api_key, api_secret, px, trade_size, cur, digits)

        print 'nospread order ', exchange, __timestamp, side, order_id, px, trade_size; sys.stdout.flush()
        
        #time.sleep(0.01)

        if order_id is not None:
            od_list.append(order_id)


def upbit_fill_range (side, start_qty, end_qty, start_px, end_px, tick, buy_first, level_treshold, chat_id, api_key, api_secret, exchange, currency, base_cur):
    
    cur = currency
    market = upbit_market(cur, base_cur)

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

    telegram_send_all('wait! do not touch! upbit start order')
    
    _flag = buy_first
    
    tick = upbit_tick(price)
    tick = tick*level_treshold #upbit
    
    cur_level = 0
    max_level = int((round(abs(end_px - start_px), 3))/tick)
    level_789 = 100
    level_789_threshold = 1.0
    
    out_msg = ''
    while(1):
        
        if stop_threads:
            return
   
        digits = upbit_digit(tick)
        #print 'digits', digits

        if side == 1: #ask
            px = round(price, digits)
            
            trade_size = round(random.uniform (start_qty, end_qty), 4)
            if cur_level >= level_789 and cur_level <= level_789+2 and max_level >= 10:
                print cur_level
                trade_size = round(trade_size*level_789_threshold, 4)

            print 'order: ', px, trade_size, side
            order_id, num_trade, try_again, _err = upbit_sell_order (api_key, api_secret, px, trade_size, cur, digits)
            print _err
            out_msg += ('%s: sell %s %s %s\n' % (market, px, trade_size, upbit_order_success(_err)))
            price += tick
            cur_level += 1
            
            #time.sleep(0.01)
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
            order_id, num_trade, try_again, _err = upbit_buy_order (api_key, api_secret, px, trade_size, cur, digits)
            print _err
            out_msg += ('%s: buy %s %s %s\n' % (market, px, trade_size, upbit_order_success(_err)))
            price -= tick
            cur_level += 1
            
            #time.sleep(0.01)
            if price < end_px:
                telegram_send_all(out_msg)
                
                print 'price >= end_px, so break loop'
                break

        else:
            print "Error: upbit_config_fill_level"; exit(-1)

    telegram_send_all('done order')


def upbit_fill_level_ask789 (widthpct, new_tick, openorder_dict, book, trade_size, api_key, api_secret, exchange, currency, base_cur):
    
    cur = currency
    market = upbit_market(cur, base_cur)

    
    side = int(book.iloc[0].type) #bid:0, ask:1
    
    if side == 0:
        print 'ask789 ask only, gr_ask_level'
        exit()

    #cancel everything, add new 789, 2019-03-13
    openorder_dict = upbit_clear_ask_orders(openorder_dict, api_key, api_secret, exchange, currency, base_cur)

    price = 0
    order_id = None
    #price = df.iloc[0].price
    price = px = book.iloc[0].price

    tick = upbit_tick(price)
    digits = upbit_digit(tick)

    #for x in range (0, max_level-ask_start_level):
    for x in range (3):
        if x == 0:
            px = round(px*(1+widthpct), digits)
        elif x == 1:
            px = round(px+new_tick, digits)
        elif x == 2:
            px = round(px+new_tick, digits)
        else:
            print "error: fill_level_ask789 x"
            exit()
        
        if openorder_dict.get(px, None) is None:
            ask_trade_size = round(trade_size, 4)
            order_id, num_trade, try_again, _err = upbit_sell_order (api_key, api_secret, px, ask_trade_size, cur, digits)
            if order_id is not None:
                print 'upbit, ask789, order: ', px, ask_trade_size
                openorder_dict.update( {px: (px,order_id)} )
                order_id = None
        
        #price -= tick # is it -?
    
    print '_ask789', sorted(openorder_dict.keys()); sys.stdout.flush()
    
    return openorder_dict


def upbit_fill_level_bid789 (widthpct, new_tick, openorder_dict, book, trade_size, api_key, api_secret, exchange, currency, base_cur):
    
    cur = currency

    side = int(book.iloc[0].type) #bid:0, ask:1
    
    if side == 1:
        print 'bid789 bid only, gr_bid_level'
        exit()

    #cancel everything, add new 789, 2019-03-13
    openorder_dict = upbit_clear_bid_orders(openorder_dict, api_key, api_secret, exchange, currency, base_cur)

    price = 0
    order_id = None
    #price = df.iloc[0].price
    price = px = book.iloc[0].price

    tick = upbit_tick(price)
    digits = upbit_digit(tick)

    #for x in range (0, max_level-bid_start_level):
    for x in range (3):
        if x == 0:
            px = round(px*(1-widthpct), digits)
        elif x == 1:
            px = round(px-new_tick, digits)
        elif x == 2:
            px = round(px-new_tick, digits)
        else:
            print "error: fill_level_bid89 x"
            exit()
 
        if openorder_dict.get(px, None) is None:
            bid_trade_size = round(trade_size, 4)
            print 'upbit, bid789, order: ', px, bid_trade_size
            order_id, num_trade, try_again, _err = upbit_buy_order (api_key, api_secret, px, bid_trade_size, cur, digits)
            if order_id is not None:
                openorder_dict.update( {px: (px,order_id)} )
                order_id = None


    print '_bid789', sorted(openorder_dict.keys()); sys.stdout.flush()
    
    return openorder_dict


def upbit_open_orders(api_key, api_secret, cur):

    query = { 'state': 'wait', 'limit': 100 }
    result = upbit_request (api_key, api_secret, '/v1/orders', 'GET-P', query, None)

    if result is None:
        return None

    return result


def upbit_cancel_all(side, start_px, end_px, chat_id, api_key, api_secret, exchange, currency, base_cur):
    
    cur = currency
    market = upbit_market(cur, base_cur)
    
    if side == 'sell':
        side = 'ask'
    elif side == 'buy':
        side = 'bid'
    else:
        print 'upbit_cancel_all fail'
        return

    telegram_send_all('upbit wait! do not touch! get open orders')
    
    result = upbit_open_orders(api_key, api_secret, cur)
    if result is None:
        telegram_send_all ('failed: no orders or server problem, Check, try again')
        return

    orderData = []
    out_msg = ''
    
    for order in result:

        if stop_threads:
            return

        #print order['type'], order['price'], order['qty'], order['orderId']
        print order['side'], order['price'], order['remaining_volume'], order['uuid']
        if order['side'] == side:
            orderData.append([order['uuid'], order['side'], order['price']])
    
    for od_id in orderData:
        ordPrc = (float)(od_id[2])

        if stop_threads:
            return

        if start_px <= ordPrc and ordPrc <= end_px:
            success, _err = upbit_cancel_order (api_key, api_secret, [od_id[0], None], 1 if side=='ask' else 0, cur)
            out_msg += ('%s: cancel %s %s\n' %(market, ordPrc, upbit_order_success(_err)))
            #pass

    telegram_send_all (out_msg)
    telegram_send_all ('done cancel')


def upbit_openorders(chat_id, api_key, api_secret, exchange, currency, base_cur):
    
    cur = currency
    market = cur
    
    telegram_send_all('wait! upbit open-orders')
    
    result = upbit_open_orders(api_key, api_secret, cur)
    
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
        print row['uuid'], row['side'], row['price'], row['remaining_volume']
        _line = str(seq)+' '+cur+' '+row['side']+' '+row['price']+' '+row['remaining_volume']
        fp.write (_line+'\n')
        seq += 1
    
    fp.close()
    telegram_send_doc('./openorders_%s.txt' % (cur))

def upbit_self(trade_size, tick, frequency, final_seq, chat_id, api_key, api_secret, exchange, currency, base_cur):
    
    #global currency, cur, market
    
    cur = currency
    market = upbit_market(cur, base_cur)
    session = init_session()
    
    telegram_send_all('wait! do not touch! start self')
    
    self_seq = 0
    seq = 0
    
    timestamp = last_update_time = datetime.datetime.now()
    
    self_size_list = get_self_size_list (trade_size, 4)
    self_size_list = self_size_list[-1:]
    
    while 1:
        
        if stop_threads:
            return

        timestamp = datetime.datetime.now()
        if ((timestamp - last_update_time).total_seconds() < frequency) and (seq > 0):
            seq += 1
            continue
        __timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        
        if self_seq >= final_seq:
            print 'self heavy, exit after self_seq', self_seq; sys.stdout.flush()
            telegram_send_all ('done self')
            return

        #self_seq += 1
       
        print market,
        
        gr_bid_level, gr_ask_level = upbit_book(exchange, currency, None, session)
        if gr_bid_level is None or gr_ask_level is None:
            print 'upbit book is none'; sys.stdout.flush()
            continue

        mid_price, bid, ask, bid_qty, ask_qty = short_cal_mid_price(gr_bid_level, gr_ask_level, None)
        
        
        #gap = 0.1; trade_size = round(random.uniform (trade_size*(1-gap), trade_size*(1+gap)), 4)
        gap = random.choice(self_size_list); trade_size = round(random.uniform(gap[0], gap[1]), 4)

        last_update_time = datetime.datetime.now()
        seq += 1

        tick = upbit_tick(mid_price)
        digits = upbit_digit(tick)

        ask_bid_spread = round(ask - bid, digits)
        if ask_bid_spread <= 0:
            seq +=1
            print 'upbit spread <= 0'; sys.stdout.flush()
            continue
            
        if int(ask_bid_spread/tick) <= 1:
            seq +=1
            print 'int <= 1'; sys.stdout.flush()
            continue

        mid_price = round(mid_price, digits)

        #random_tick = random.randint(1,int(ask_bid_spread/tick)-1)
        #print market, -1*random_tick,int(ask_bid_spread/tick)-1; sys.stdout.flush()
        #px = ask + (-1*random_tick*tick)
        random_tick = 1
        #px = bid + tick
        px = ask - tick
 
        px = round(px, digits)
        
        if ((float)(px) <= 0):
            seq += 1
            print 'upbit px negative'; sys.stdout.flush()
            continue
        
        if (ask-bid) <= (random_tick*tick):
            seq += 1
            print 'upbit spread no good'
            continue
        
        if ask == (float)(px) or bid == (float)(px):
            seq += 1
            print 'ask or bid equal to px'; sys.stdout.flush()
            continue
            
        round_px = round ((float)(px), digits)
        if round (ask, digits) == round_px or round (bid, digits) == round_px:
            seq += 1
            print 'rounded ask or bid equal to px'; sys.stdout.flush()
            continue
            
        self_seq += 1
        
        sell_order_id = buy_order_id = None

        print market, __timestamp, bid, ask; sys.stdout.flush()
        #sell_order_id, num_trade, try_again, _err = bithumb_sell_order (api, px, trade_size, cur, digits)
        sell_order_id, num_trade, try_again, _err = upbit_sell_order (api_key, api_secret, px, trade_size, cur, digits)
            
        #time.sleep(0.01)
            
        #buy_order_id, num_trade, try_again, _err = bithumb_buy_order (api, px, trade_size, cur, digits)
        buy_order_id, num_trade, try_again, _err = upbit_buy_order (api_key, api_secret, px, trade_size, cur, digits)
        
        print px, trade_size, sell_order_id, buy_order_id; sys.stdout.flush()

        time.sleep(0.01)

        if buy_order_id is not None:
            #bithumb_cancel_order(api, [buy_order_id,'bid'], cur)
            upbit_cancel_order(api_key, api_secret, [buy_order_id, 'bid'], 0, cur)
            print 'buy cancel'
        if sell_order_id is not None:
            #bithumb_cancel_order(api, [sell_order_id,'ask'], cur)
            upbit_cancel_order(api_key, api_secret, [sell_order_id, 'ask'], 1, cur)
            print 'sell cancel'
 
        telegram_send_all('%s: self %s %s %s' %(market, px, trade_size, __timestamp))
        #sys.stdout.flush()



########## END UPBIT ############



def cmd_echo(chat_id, params):
	bot.sendMessage(chat_id, "[ECHO] {text}".format(text=" ".join(params)))

def cmd_help(chat_id, params):
	#bot.sendMessage(chat_id, "{text}".format(text='wfx, resh, soc, isr\n\n/kill kill all operations\n\n/order coin buy|sell start_px end_px start_qty end_qty 789_ratio ex\ne.g.) /order wfx buy 1.0 2.0 100 200 1.2 coinzest\n\n/self coin qty seconds-apart, rounds, ex\ne.g.)/self wfx 1000 3 20 coinzest\n\n/cancel coin buy|sell start_px end_px coinzest'))
	#bot.sendMessage(chat_id, "{text}".format(text='vaip, addr\n\n/kill kill all operations\n\n/order coin buy|sell start_px end_px start_qty end_qty 789_ratio ex\ne.g.) /order vaip buy 500.0 500.0 100 200 1.2 coinzest\n\n/self coin qty seconds-apart, rounds, ex\ne.g.)/self vaip 1000 3 20 coinzest\n\n/cancel coin buy|sell start_px end_px coinzest'))
	#bot.sendMessage(chat_id, "{text}".format(text='con@bithumb\n\n/kill kill all operations\n\n/sellmm coin qty ex\n\n/order coin buy|sell start_px end_px start_qty end_qty 789_ratio ex\ne.g.) /order con buy 1.0 2.0 100 200 1.2 bithumb\n\n/self coin qty seconds-apart, rounds, ex\ne.g.)/self con 1000 3 20 bithumb\n\n/cancel coin buy|sell start_px end_px bithumb\n\n/show trade con bithumb'))
	#bot.sendMessage(chat_id, "{text}".format(text='eth,wfx-usdt@bithumbglobal\n\n/kill kill all operations\n\n/sellmm coin qty ex\n\n/order coin buy|sell start_px end_px start_qty end_qty 789_ratio ex\ne.g.) /order wfx buy 1.0 2.0 100 200 1.2 bithumbglobal\n\n/self coin qty seconds-apart, rounds, ex\ne.g.)/self wfx 1000 3 20 bithumbglobal\n\n/cancel coin buy|sell start_px end_px bithumbglobal'))
	#bot.sendMessage(chat_id, "{text}".format(text='eth,wfx-usdt@bithumbglobal\n\n/kill kill all operations\n\n/sellmm coin qty ex\n\n/order coin buy|sell start_px end_px start_qty end_qty 789_ratio ex\ne.g.) /order wfx buy 1.0 2.0 100 200 1.2 bg\n\n/self coin qty seconds-apart, rounds, ex\ne.g.)/self wfx 1000 3 20 bithumbglobal\n\n/cancel coin buy|sell start_px end_px bg\n\n/show trade wfx bg'))
	#bot.sendMessage(chat_id, "{text}".format(text='wfx\n\n/kill kill all operations\n\n/order coin buy|sell start_px end_px start_qty end_qty 789_ratio ex\ne.g.) /order wfx buy 1.0 2.0 100 200 1.2 coinbene\n\n/self coin qty seconds-apart, rounds, ex\ne.g.)/self wfx 1000 3 20 coinbene\n\n/cancel coin buy|sell start_px end_px coinbene'))
	#bot.sendMessage(chat_id, "{text}".format(text='xsr@bithumb\n\n/kill kill all operations\n\n/sellmm xsr qty bithumb 0 (Young)\n\n/order coin buy|sell start_px end_px start_qty end_qty 789_ratio ex\ne.g.) /order coin buy 1.0 2.0 100 200 1.2 bithumb\n\n/self coin qty seconds-apart, rounds, ex\ne.g.)/self coin 1000 3 20 bithumb\n\n/cancel coin buy|sell start_px end_px bithumb\n\n/show trade coin bithumb'))
	#bot.sendMessage(chat_id, "{text}".format(text='xsr soc@bithumb\n\n/kill kill all operations\n\n/sellmm soc qty bithumb 0\n\n/order coin buy|sell start_px end_px start_qty end_qty 789_ratio ex\ne.g.) /order soc buy 1.0 2.0 100 200 1.2 bithumb\n\n/self coin qty seconds-apart, rounds, ex\ne.g.)/self soc 1000 3 20 bithumb\n\n/cancel coin buy|sell start_px end_px bithumb\n\n/show trade coin bithumb'))
	#bot.sendMessage(chat_id, "{text}".format(text='xsr soc@bithumb\n\n/kill \n\n/sellmm soc qty bithumb 0\n\n/order coin buy|sell start_px end_px start_qty end_qty 789_ratio ex\ne.g.) /order soc buy 1.0 2.0 100 200 1.2 bithumb\n\n/self coin qty seconds-apart, rounds, ex\ne.g.)/self soc 1000 3 20 bithumb\n\n/cancel coin buy|sell start_px end_px bithumb\n\n/show trade coin bithumb'))
	#bot.sendMessage(chat_id, "{text}".format(text='basic@bithumb\n\n/kill \n\n/sellmm coin qty bithumb\n\n/buymm coin qty bithumb\n\n/twap coin buy|sell frequency bithumb\n\n/flash coin duration bithumb\n\n/order coin buy|sell start_px end_px start_qty end_qty 789_ratio ex\ne.g.) /order basic buy 1.0 2.0 100 200 1.2 bithumb\n\n/self coin qty seconds-apart, rounds, ex\ne.g.)/self basic 1000 3 20 bithumb\n\n/cancel coin buy|sell start_px end_px bithumb\n\n/show trade coin bithumb'))
	#bot.sendMessage(chat_id, "{text}".format(text='basic@bithumb ONLY\n\n/kill \n\n/sellmm coin qty\n\n/buymm coin qty\n\n/twap coin buy|sell frequency\n\n/flash coin duration\n\n/order coin buy|sell start_px end_px start_qty end_qty 789_ratio\ne.g.) /order basic buy 1.0 2.0 100 200 1.2\n\n/self coin qty seconds-apart, rounds\ne.g.)/self basic 1000 3 20\n\n/cancel coin buy|sell start_px end_px\n\n/show trade coin\n\n/openorder basic\n\n/nospreadbuy basic qty\n\n/nospreadsell basic qty'))
	#bot.sendMessage(chat_id, "{text}".format(text='basic@bithumb ONLY\n\n/kill \n\n/sellmm coin qty qtymult widthpct tick\n\n/buymm coin qty qtymult widthpct tick\n/buymm basic 20000 10 0.025 0.02\n\n/twap coin buy|sell frequency\n\n/flash coin duration\n\n/order coin buy|sell start_px end_px start_qty end_qty 789_ratio\ne.g.) /order basic buy 1.0 2.0 100 200 1.2\n\n/self coin qty seconds-apart, rounds\ne.g.)/self basic 1000 3 20\n\n/cancel coin buy|sell start_px end_px\n\n/show trade coin\n\n/openorder basic\n\n/nospreadbuy basic qty\n\n/nospreadsell basic qty'))
	#bot.sendMessage(chat_id, "{text}".format(text='basic@bithumb ONLY\n\n/kill \n\n/buymmimp coin qty\n\n/sellmmimp coin qty\n\n/sellmm coin qty qtymult widthpct tick\n\n/buymm coin qty qtymult widthpct tick\n/buymm basic 20000 10 0.025 0.02\n\n/twap coin buy|sell frequency\n\n/flash coin duration\n\n/order coin buy|sell start_px end_px start_qty end_qty 789_ratio\ne.g.) /order basic buy 1.0 2.0 100 200 1.2\n\n/self coin qty seconds-apart, rounds\ne.g.)/self basic 1000 3 20\n\n/cancel coin buy|sell start_px end_px\n\n/show trade coin\n\n/openorder basic\n\n/nospreadbuy basic qty\n\n/nospreadsell basic qty'))
	#bot.sendMessage(chat_id, "{text}".format(text='?@bithumb-ki ONLY\n\n/kill \n\n/buymmimp coin qty\n\n/sellmmimp coin qty\n\n/sellmm coin qty qtymult widthpct tick\n\n/buymm coin qty qtymult widthpct tick\n/buymm coin 1000 10 0.025 0.02\n\n/twap coin buy|sell frequency\n\n/flash coin duration\n\n/order coin buy|sell start_px end_px start_qty end_qty 789_ratio\ne.g.) /order coin buy 1.0 2.0 100 200 1.2\n\n/self coin qty seconds-apart, rounds\ne.g.)/self coin 1000 3 20\n\n/cancel coin buy|sell start_px end_px\n\n/show trade coin\n\n/openorder basic\n\n/nospreadbuy basic qty\n\n/nospreadsell basic qty'))
	#bot.sendMessage(chat_id, "{text}".format(text='ISR@COINONE ONLY\n\n/kill \n\n/buymm coin qty qtymult widthpct tick\n/buymm isr 1000 10 0.025 0.02\n\n/buymmimp coin qty\n\n/sellmmimp coin qty\n\n/sellmm coin qty qtymult widthpct tick\n\n/twap coin buy|sell frequency\n\n/order coin buy|sell start_px end_px start_qty end_qty 789_ratio\ne.g.) /order isr buy 1.0 2.0 100 200 1.2\n\n/cancel coin buy|sell start_px end_px\n\n/openorder isr\n\n/nospreadbuy coin qty\n\n/nospreadsell coin qty'))
	bot.sendMessage(chat_id, "{text}".format(text=help_msg))


def cmd_openorders(chat_id, params):
    
    #exch = 'bithumb'
    #exch = 'coinone'
    exch = global_exchange
    
    try:
        token = params[0].upper()
        #side = params[1].lower()
        #start_px = (float)(params[2])
        #end_px = (float)(params[3])
        #exch = params[4].lower()
    except:
        bot.sendMessage(chat_id, 'order param wrong, check again')
        return

    tick, api_key, api_secret, exchange, currency, base_cur = init_trade(token, exch)
    print 'api: ', api_key, exch; sys.stdout.flush()
    
    if tick == 0:
        bot.sendMessage(chat_id, '%s undefined, tick undefined' % currency)
        return

    p1 = None
    if exch == 'bithumb':
        api = XCoinAPI(api_key, api_secret);
        p1 = threading.Thread(target = bithumb_openorders, args=(chat_id, api, exchange, currency, base_cur,))
    elif exch == 'coinone':
        p1 = threading.Thread(target = coinone_openorders, args=(chat_id, api_key, api_secret, exchange, currency, base_cur,))
    elif exch == 'upbit':
        p1 = threading.Thread(target = upbit_openorders, args=(chat_id, api_key, api_secret, exchange, currency, base_cur,))
    else:
        return
    p1.start()


def cmd_cancel(chat_id, params):
    
    exch = global_exchange
    
    try:
        token = params[0].upper()
        side = params[1].lower()
        start_px = (float)(params[2])
        end_px = (float)(params[3])
    except:
        bot.sendMessage(chat_id, 'order param wrong, check again')
        return

    tick, api_key, api_secret, exchange, currency, base_cur = init_trade(token, exch)
    print 'api: ', api_key; sys.stdout.flush()
    
    if tick == 0:
        bot.sendMessage(chat_id, '%s undefined, tick undefined' % currency)
        return

    p1 = None
    if side == 'sell' or side == 'buy':
        if exch == 'bithumb':
            api = XCoinAPI(api_key, api_secret);
            p1 = threading.Thread(target = bithumb_cancel_all, args=(side, start_px, end_px, chat_id, api, exchange, currency, base_cur,))
        if exch == 'upbit':
            p1 = threading.Thread(target = upbit_cancel_all, args=(side, start_px, end_px, chat_id, api_key, api_secret, exchange, currency, base_cur,))
    else:
        return

    p1.start()

def cmd_order(chat_id, params):
    
    exch = global_exchange
    
    try:
        token = params[0].upper()
        side = params[1].lower()
        start_px = (float)(params[2])
        end_px = (float)(params[3])
        start_qty = (float)(params[4])
        end_qty = (float)(params[5])
        level_treshold = (float)(params[6])
    except:
        bot.sendMessage(chat_id, 'order param wrong, check again')
        return

    tick, api_key, api_secret, exchange, currency, base_cur = init_trade(token, exch)

    print 'api: ', api_key; sys.stdout.flush()

    if tick == 0:
        bot.sendMessage(chat_id, '%s undefined, tick undefined' % currency)
        return

    if start_px > end_px:
        bot.sendMessage(chat_id, 'start_px must be smaller, check again')
        return
    
    p1 = None
    if side == 'sell':
        if exch == 'bithumb':
            api = XCoinAPI(api_key, api_secret);
            p1 = threading.Thread(target = bithumb_fill_range, args=(side, start_qty, end_qty, start_px, end_px, tick, False, level_treshold, chat_id, api, exchange, currency, base_cur,))
        elif exch == 'upbit':
            p1 = threading.Thread(target = upbit_fill_range, args=(side, start_qty, end_qty, start_px, end_px, tick, False, level_treshold, chat_id, api_key, api_secret, exchange, currency, base_cur,))
        else:
            bot.sendMessage(chat_id, 'wrong: ' % exch)
            return

    elif side == 'buy':
        if exch == 'bithumb':
            api = XCoinAPI(api_key, api_secret);
            p1 = threading.Thread(target = bithumb_fill_range, args=(side, start_qty, end_qty, end_px, start_px, tick, False, level_treshold, chat_id, api, exchange, currency, base_cur,))
        elif exch == 'upbit':
            p1 = threading.Thread(target = upbit_fill_range, args=(side, start_qty, end_qty, end_px, start_px, tick, False, level_treshold, chat_id, api_key, api_secret, exchange, currency, base_cur,))
        else:
            bot.sendMessage(chat_id, 'wrong: ' % exch)
            return
    else:
        return
    p1.start()

def cmd_self(chat_id, params):
    
    exch = global_exchange

    try:
        token = params[0].upper()
        qty = (float)(params[1])
        frequency = (int)(params[2])
        final_seq = (int)(params[3])
        #exch = params[4].lower()
    
    except:
        bot.sendMessage(chat_id, 'self param wrong, check again')
        return
    
    heavy_flag = False
    if len(params) == 6:
        if params[5].lower() == 'heavy':
            heavy_flag = True
    #####################
    
    tick, api_key, api_secret, exchange, currency, base_cur = init_trade(token, exch)
    print 'api: ', api_key; sys.stdout.flush()
 
    #print (token, side, start_px, end_px, qty, tick)
    if tick == 0:
        bot.sendMessage(chat_id, 'self %s undefined, tick undefined' % currency)
        return

    p1 = None
    if exch == 'bithumb':
        api = XCoinAPI(api_key, api_secret);
        p1 = threading.Thread(target = bithumb_self, args=(qty, tick, frequency, final_seq, chat_id, api, exchange, currency, base_cur,))
    elif exch == 'upbit':
        p1 = threading.Thread(target = upbit_self, args=(qty, tick, frequency, final_seq, chat_id, api_key, api_secret, exchange, currency, base_cur,))
    else:
        return
    p1.start()

def cmd_sellmm(chat_id, params):

    exch = global_exchange
    
    try:
        token = params[0].upper()
        qty = (float)(params[1])
        qtymult = (float)(params[2])
        widthpct = (float)(params[3])
        new_tick = (float)(params[4])
    
    except:
        bot.sendMessage(chat_id, 'mm param wrong, check again')
        return

    tick, api_key, api_secret, exchange, currency, base_cur = init_trade(token, exch)
    print 'api: ', api_key; sys.stdout.flush()
 
    if tick == 0:
        bot.sendMessage(chat_id, 'mm %s undefined, tick undefined' % currency)
        return

    p1 = None
    if exch == 'bithumb': 
        api = XCoinAPI(api_key, api_secret);
        p1 = threading.Thread(target = bithumb_sellmm, args=(qtymult, widthpct, new_tick, qty, tick, 1, chat_id, api, exchange, currency, base_cur,))
    elif exch == 'upbit':
        p1 = threading.Thread(target = upbit_sellmm, args=(qtymult, widthpct, new_tick, qty, tick, 1, chat_id, api_key, api_secret, exchange, currency, base_cur,))
    else:
        return
    p1.start()

def cmd_sellmmimp(chat_id, params):

    exch = global_exchange
    
    try:
        token = params[0].upper()
        qty = (float)(params[1])
        limitpx = (float)(params[2])
        pctrestart = (float)(params[3])
    
    except:
        bot.sendMessage(chat_id, 'mm param wrong, check again')
        return

    qtymult = widthpct = new_tick = 0
    tick, api_key, api_secret, exchange, currency, base_cur = init_trade(token, exch)
    print 'api: ', api_key; sys.stdout.flush()
 
    if tick == 0:
        bot.sendMessage(chat_id, 'mm %s undefined, tick undefined' % currency)
        return

    p1 = None
    if exch == 'bithumb': 
        api = XCoinAPI(api_key, api_secret);
        p1 = threading.Thread(target = bithumb_sellmmimp, args=(qtymult, widthpct, new_tick, qty, tick, 1, chat_id, api, exchange, currency, base_cur,))
    elif exch == 'upbit':
        p1 = threading.Thread(target = upbit_sellmmimp, args=(qtymult, widthpct, new_tick, qty, limitpx, pctrestart,  tick, 1, chat_id, api_key, api_secret, exchange, currency, base_cur,))
    else:
        return
    
    p1.start()

def cmd_buymm(chat_id, params):
    
    exch = global_exchange
    
    try:
        token = params[0].upper()
        qty = (float)(params[1])
        qtymult = (float)(params[2])
        widthpct = (float)(params[3])
        new_tick = (float)(params[4])
    
    except:
        bot.sendMessage(chat_id, 'mm param wrong, check again')
        return

    tick, api_key, api_secret, exchange, currency, base_cur = init_trade(token, exch)
    print 'api: ', api_key; sys.stdout.flush()
 
    if tick == 0:
        bot.sendMessage(chat_id, 'mm %s undefined, tick undefined' % currency)
        return

    p1 = None
    if exch == 'bithumb': 
        api = XCoinAPI(api_key, api_secret);
        p1 = threading.Thread(target = bithumb_buymm, args=(qtymult, widthpct, new_tick, qty, tick, 1, chat_id, api, exchange, currency, base_cur,))
    elif exch == 'upbit':
        p1 = threading.Thread(target = upbit_buymm, args=(qtymult, widthpct, new_tick, qty, tick, 1, chat_id, api_key, api_secret, exchange, currency, base_cur,))
    else:
        return
    p1.start()

def cmd_buymmimp(chat_id, params):
    
    exch = global_exchange
    
    try:
        token = params[0].upper()
        qty = (float)(params[1])
        limitpx = (float)(params[2])
        pctrestart = (float)(params[3])

    except:
        bot.sendMessage(chat_id, 'mm param wrong, check again')
        return

    qtymult = widthpct = new_tick = 0
    tick, api_key, api_secret, exchange, currency, base_cur = init_trade(token, exch)
    print 'api: ', api_key; sys.stdout.flush()
 
    if tick == 0:
        bot.sendMessage(chat_id, 'mm %s undefined, tick undefined' % currency)
        return

    p1 = None
    if exch == 'bithumb': 
        api = XCoinAPI(api_key, api_secret);
        p1 = threading.Thread(target = bithumb_buymmimp, args=(qtymult, widthpct, new_tick, qty, tick, 1, chat_id, api, exchange, currency, base_cur,))
    elif exch == 'upbit':
        p1 = threading.Thread(target = upbit_buymmimp, args=(qtymult, widthpct, new_tick, qty, limitpx, pctrestart, tick, 1, chat_id, api_key, api_secret, exchange, currency, base_cur,))
    else:
        return
    
    p1.start()

def cmd_nospreadbuy(chat_id, params):
    
    exch = global_exchange
    side = 'bid'

    try:
        token = params[0].upper()
        qty = (float)(params[1])
    
    except:
        bot.sendMessage(chat_id, 'nospread param wrong, check again')
        return

    tick, api_key, api_secret, exchange, currency, base_cur = init_trade(token, exch)
    print 'api: ', api_key; sys.stdout.flush()
 
    if tick == 0:
        bot.sendMessage(chat_id, 'nospread %s undefined, tick undefined' % currency)
        return

    p1 = None
    if exch == 'bithumb': 
        api = XCoinAPI(api_key, api_secret);
        p1 = threading.Thread(target = bithumb_nospread, args=(side, qty, tick, 1, chat_id, api, exchange, currency, base_cur,))
    elif exch == 'upbit':
        p1 = threading.Thread(target = upbit_nospread, args=(side, qty, tick, 1, chat_id, api_key, api_secret, exchange, currency, base_cur,))
    else:
        return
    p1.start()


def cmd_nospreadsell(chat_id, params):
    
    exch = global_exchange
    side = 'ask'

    try:
        token = params[0].upper()
        qty = (float)(params[1])
    
    except:
        bot.sendMessage(chat_id, 'nospread param wrong, check again')
        return

    tick, api_key, api_secret, exchange, currency, base_cur = init_trade(token, exch)
    print 'api: ', api_key; sys.stdout.flush()
 
    if tick == 0:
        bot.sendMessage(chat_id, 'nospread %s undefined, tick undefined' % currency)
        return

    p1 = None
    if exch == 'bithumb': 
        api = XCoinAPI(api_key, api_secret);
        p1 = threading.Thread(target = bithumb_nospread, args=(side, qty, tick, 1, chat_id, api, exchange, currency, base_cur,))
    elif exch == 'upbit':
        p1 = threading.Thread(target = upbit_nospread, args=(side, qty, tick, 1, chat_id, api_key, api_secret, exchange, currency, base_cur,))
    else:
        return
    p1.start()


def cmd_twap(chat_id, params):
    
    exch = global_exchange
    
    try:
        token = params[0].upper()
        side = params[1].lower()
        frequency = (int)(params[2])
        twapMode = (int)(params[3])
        threshQty = (float)(params[4])
    
    except:
        bot.sendMessage(chat_id, 'twap param wrong, check again')
        return

    tick, api_key, api_secret, exchange, currency, base_cur = init_trade(token, exch)
    print 'api: ', api_key; sys.stdout.flush()
 
    if tick == 0:
        bot.sendMessage(chat_id, 'twap %s undefined, tick undefined' % currency)
        return

    p1 = None
    if exch == 'bithumb': 
        api = XCoinAPI(api_key, api_secret);
        p1 = threading.Thread(target = bithumb_twap, args=(side, tick, frequency, twapMode, threshQty, chat_id, api, exchange, currency, base_cur,))
    elif exch == 'upbit':
        p1 = threading.Thread(target = upbit_twap, args=(side, tick, frequency, twapMode, threshQty, chat_id, api_key, api_secret, exchange, currency, base_cur,))
    else:
        return
    p1.start()

def cmd_flash(chat_id, params):
    
    exch = global_exchange
    
    try:
        token = params[0].upper()
        duration = (int)(params[1])
    
    except:
        bot.sendMessage(chat_id, 'flash param wrong, check again')
        return

    tick, api_key, api_secret, exchange, currency, base_cur = init_trade(token, exch)
    print 'api: ', api_key; sys.stdout.flush()
 
    if tick == 0:
        bot.sendMessage(chat_id, 'flash %s undefined, tick undefined' % currency)
        return

    p1 = None
    if exch == 'bithumb': 
        api = XCoinAPI(api_key, api_secret);
        p1 = threading.Thread(target = bithumb_flash, args=(tick, duration, chat_id, api, exchange, currency, base_cur,))
    else:
        return
    p1.start()


def cmd_show(chat_id, params):
    
    exch = global_exchange

    try:
        op = params[0].lower()
        token = params[1].upper()
    
    except:
        bot.sendMessage(chat_id, 'show param wrong, check again')
        return

    tick, api_key, api_secret, exchange, currency, base_cur = init_trade(token, exch)
    print 'api: ', api_key; sys.stdout.flush()
 
    if tick == 0:
        bot.sendMessage(chat_id, 'self %s undefined, tick undefined' % currency)
        return

    p1 = None
    if exch == 'bithumb': 
        api = XCoinAPI(api_key, api_secret);
        p1 = threading.Thread(target = bithumb_show, args=(op, chat_id, api, exchange, currency, base_cur,))
    else:
        return
    p1.start()


def cmd_kill(chat_id, params):
    
    global stop_threads
    
    stop_threads = True

    time.sleep(2)

    thread_list = threading.enumerate()
    print thread_list

    telegram_send_all('killed everything')
    stop_threads = False

def add_command(cmd, func):
	global tg_commands
	tg_commands[cmd] = func

def parse_cmd(cmd_string):
	text_split = cmd_string.split()
	return text_split[0], text_split[1:]

def truncate(f, n):
    return math.floor(f * 10 ** n) / 10 ** n

def telegram_send_young(msg):
    bot = telepot.Bot(bot_api)

def handle(message):
    content_type, chat_type, chat_id = telepot.glance(message)
    print(content_type, chat_type, chat_id)
    if chat_id not in whitelist_id:
        #bot.kickChatMember (chat_id, chat_id)
        print 'illegal user, do not respnosive'
        return

    if content_type == "text":
		msg_text = message['text']
		chat_id = message['chat']['id']

		print("[MSG] {uid} : {msg}".format(uid=message['from']['id'], msg=msg_text))

		if msg_text[0] == '/':
			cmd, params = parse_cmd(msg_text)
			try:
				tg_commands[cmd](chat_id, params)
			except KeyError:
				bot.sendMessage(chat_id, "Unknown command: {cmd}".format(cmd=cmd))
		else:
			bot.sendMessage(chat_id, "Fail, cmd required")

def bot_listner():
    print bot.getMe()
    add_command("/nospreadbuy", cmd_nospreadbuy) #nospread
    add_command("/nospreadsell", cmd_nospreadsell) #nospread
    add_command("/openorder", cmd_openorders) #openorder
    add_command("/show", cmd_show)
    add_command("/sellmm", cmd_sellmm)
    add_command("/sellmmimp", cmd_sellmmimp)
    add_command("/buymm", cmd_buymm)
    add_command("/buymmimp", cmd_buymmimp)
    add_command("/twap", cmd_twap)
    add_command("/flash", cmd_flash)
    add_command("/kill", cmd_kill)
    add_command("/order", cmd_order)
    add_command("/self", cmd_self)
    add_command("/cancel", cmd_cancel)
    add_command("/help", cmd_help)
    bot.message_loop(handle)
    
    print ('Listening ...')
    
    # Keep the program running.
    while 1:
        time.sleep(5)


def init_trade (token, exch):
    
    exchange = exch

    currency = token.upper() 
    base_cur = 'KRW'

    if currency in global_coin_list: #
        api_key = global_api_key; api_secret = global_api_secret

        return 0.01, api_key, api_secret, exchange, currency, base_cur
     
    return 0, None, None #wrong tick size

def telegram_send_all(msg):
    
    lock.acquire()
    for user_session in whitelist_id:
        try:
            bot.sendMessage(user_session, msg)
        except:
            bot.sendMessage(user_session,'orders should be okay, message is too long. DONE')
    lock.release()

def telegram_send_doc(msg):
    
    lock.acquire()
    for user_session in whitelist_id:
        try:
            bot.sendDocument(user_session, open(msg, 'rb'))
        except:
            bot.sendMessage(user_session,'file problem?')
    lock.release()


urllib3.disable_warnings()

pd.set_option('precision', 8)
pd.set_option('display.precision', 8)


_dict_url = {
             'bithumb': ['https://api.bithumb.com/public/orderbook/%s/?count=10&group_orders=1', 'https://api.bithumb.com/public/transaction_history/%s/?count=10'],
             'upbit': ['https://api.upbit.com/v1/orderbook/?markets=%s', 'https://api.upbit.com/v1/trades/ticks/?market=%s&count=%d']
             }


#####################
lock = threading.Lock()
stop_threads = False
####################
tg_commands = {}

bot = telepot.Bot(bot_token)
bot_listner()
