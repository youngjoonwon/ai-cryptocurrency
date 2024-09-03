# Feature: calculating midprice using orderbook

# @params

# gr_bid_level: all bid level
# gr_ask_level: all ask level
# group_t: trade data

def cal_mid_price (gr_bid_level, gr_ask_level, group_t):
    
    level = 5 
    #gr_rB = gr_bid_level.head(level)
    #gr_rT = gr_ask_level.head(level)
    
    if len(gr_bid_level) > 0 and len(gr_ask_level) > 0:
        bid_top_price = gr_bid_level.iloc[0].price
        bid_top_level_qty = gr_bid_level.iloc[0].quantity
        ask_top_price = gr_ask_level.iloc[0].price
        ask_top_level_qty = gr_ask_level.iloc[0].quantity
        mid_price = (bid_top_price + ask_top_price) * 0.5 #what is mid price?
    
        if mid_type == 'wt':
            mid_price = ((gr_bid_level.head(level))['price'].mean() + (gr_ask_level.head(level))['price'].mean()) * 0.5
        elif mid_type == 'mkt':
            mid_price = ((bid_top_price*ask_top_level_qty) + (ask_top_price*bid_top_level_qty))/(bid_top_level_qty+ask_top_level_qty)
            mid_price = truncate(mid_price, 1)
        elif mid_type == 'vwap':
            mid_price = (group_t['total'].sum())/(group_t['units_traded'].sum())
            mid_price = truncate(mid_price, 1)
        
        #print mid_type, mid_price

        return (mid_price, bid_top_price, ask_top_price, bid_top_level_qty, ask_top_level_qty)

    else:
        print 'Error: serious cal_mid_price'
        return (-1, -1, -2, -1, -1)

