# Feature: calculating 'T' using orderbook and trade
#
# @description
# Trade Feature
#
# @params
#
# gr_bid_level: all bid level
# gr_ask_level: all ask level
# diff: summary of trade, refer to get_diff_count_units()
# var: can be empty
# mid: midprice

def live_cal_T_v1(param, gr_bid_level, gr_ask_level, diff, var, mid):
    
    ratio = param[0]; level = param[1]; interval = param[2]; normal_fn = param[3]
    #print ('processing... %s %s,level:%s,decay:%s,normal_fn:%s' % (sys._getframe().f_code.co_name,ratio,level,interval,normal_fn)), 
    
    _l_fn = {'power':power_fn, 'log':log_fn, 'sqrt':sqrt_fn, 'raw':raw_fn}
    if normal_fn not in _l_fn:
        print 'Error: normal_fn does not exist'; exit(-1)
    
    decay = np.exp(-1.0/interval)
    
    _flag = var['_flag']
    
    tradeIndicator = var['tradeIndicator']
    #bidSideTrade = var['bidSideTrade']
    #askSideTrade = var['askSideTrade']

    if _flag:
        var['_flag'] = False
        return 0.0
    
    #BSideTrade = ASideTrade = 0
    #BSideTradeQty = ASideTradeQty = 0
    
    (_count_1, _count_0, _units_traded_1, _units_traded_0, _price_1, _price_0) = diff
    
    BSideTrade = _l_fn[normal_fn](ratio, _units_traded_1)
    ASideTrade = _l_fn[normal_fn](ratio, _units_traded_0)


    #bidSideTrade += (BSideTrade)
    #askSideTrade += (ASideTrade)
    #tradeIndicator += -bidSideTrade + askSideTrade
    
    tradeIndicator += (-1*BSideTrade + ASideTrade)

    var['tradeIndicator'] = tradeIndicator * decay
    #var['bidSideTrade'] = bidSideTrade * decay
    #var['askSideTrade'] = askSideTrade * decay

    return tradeIndicator

# Feature: calculating 'T' using orderbook and trade
#
# @description
# Trade Feature
#
# @params
#
# gr_bid_level: all bid level
# gr_ask_level: all ask level
# diff: summary of trade, refer to get_diff_count_units()
# var: can be empty
# mid: midprice


def live_cal_trade_indicator_v2(param, gr_bid_level, gr_ask_level, diff, var, mid):
    
    mid_price = mid

    ratio = param[0]; level = param[1]; interval = param[2]; normal_fn = param[3]
    #print ('processing... %s %s,level:%s,decay:%s,normal_fn:%s' % (sys._getframe().f_code.co_name,ratio,level,interval,normal_fn)), 
    
    _l_fn = {'power':power_fn, 'log':log_fn, 'sqrt':sqrt_fn, 'raw':raw_fn}
    if normal_fn not in _l_fn:
        print 'Error: normal_fn does not exist'; exit(-1)
    
    decay = np.exp(-1.0/interval)

    _flag = var['_flag']

    tradeIndicator = var['tradeIndicator']
    #bidSideTrade = var['bidSideTrade']
    #askSideTrade = var['askSideTrade']

    if _flag:
        var['_flag'] = False
        return 0.0
 
    midPrice = mid_price
    
    #BSideTrade = ASideTrade = 0
    #BSideTradeQty = ASideTradeQty = 0
    
    (_count_1, _count_0, _units_traded_1, _units_traded_0, _price_1, _price_0) = diff
    
    #print _units_traded_1, _price_1, _units_traded_0, _price_0, midPrice

    #BSideTrade = ((_l_fn[normal_fn](ratio,_units_traded_1))*(midPrice-_price_1))
    #ASideTrade = ((_l_fn[normal_fn](ratio,_units_traded_0))*(_price_0-midPrice))
    BSideTrade = (_l_fn[normal_fn](ratio,_units_traded_1))*(_price_1)
    ASideTrade = (_l_fn[normal_fn](ratio,_units_traded_0))*(_price_0)
 
    #bidSideTrade += (BSideTrade)
    #askSideTrade += (ASideTrade)
    #tradeIndicator = -bidSideTrade + askSideTrade
    tradeIndicator += (-1*BSideTrade + ASideTrade)
    
    var['tradeIndicator'] = tradeIndicator * decay
    #var['bidSideTrade'] = bidSideTrade * decay
    #var['askSideTrade'] = askSideTrade * decay

    return tradeIndicator
   

