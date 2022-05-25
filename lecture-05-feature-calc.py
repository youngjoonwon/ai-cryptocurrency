def get_sim_df (fn):

    print 'loading... %s' % fn
    df = pd.read_csv(fn).apply(pd.to_numeric,errors='ignore')
    
    #print df.to_string();print '------'
    
    group = df.groupby(['timestamp'])
    return group

def get_sim_df_trade (fn):

    print 'loading... %s' % fn
    df = pd.read_csv(fn).apply(pd.to_numeric,errors='ignore')
    
    group = df.groupby(['timestamp'])
    return group

def faster_calc_indicators(raw_fn):
    
    start_time = timeit.default_timer()

    # FROM CSV FILES (DAILY)
    group_o = get_sim_df(raw_book_csv(raw_fn, ('%s-%s-%s' % (_tag, exchange, currency))))
    group_t = get_sim_df_trade(raw_trade_csv(raw_fn, ('%s-%s-%s' % (_tag, exchange, currency)))) #fix for book-1 regression
    
    delay = timeit.default_timer() - start_time
    print 'df loading delay: %.2fs' % delay
     
    level_1 = 2 
    level_2 = 5

    print 'param levels', exchange, currency, level_1, level_2

    #(ratio, level, interval seconds )   
    book_imbalance_params = [(0.2,level_1,1),(0.2,level_2,1)] 
    book_delta_params = [(0.2,level_1,1),(0.2,level_1,5),(0.2,level_1,15), (0.2,level_2,1),(0.2,level_2,5),(0.2,level_2,15)]
    trade_indicator_params = [(0.2,level_1,1),(0.2,level_1,5),(0.2,level_1,15)]

    variables = {}
    _dict = {}
    _dict_indicators = {}

    for p in book_imbalance_params:
        indicator = 'BI'
        _dict.update( {(indicator, p): []} )
        _dict_var = init_indicator_var(indicator, p)
        variables.update({(indicator, p): _dict_var})
        
    for p in book_delta_params:
        indicator = 'BDv1'
        _dict.update( {(indicator, p): []} )
        _dict_var = init_indicator_var(indicator, p)
        variables.update({(indicator, p): _dict_var})
        
        indicator = 'BDv2'
        _dict.update( {(indicator, p): []} )
        _dict_var = init_indicator_var(indicator, p)
        variables.update({(indicator, p): _dict_var})

        indicator = 'BDv3'
        _dict.update( {(indicator, p): []} )
        _dict_var = init_indicator_var(indicator, p)
        variables.update({(indicator, p): _dict_var})

    for p in add_norm_fn(trade_indicator_params):

        indicator = 'TIv1'
        _dict.update( {(indicator, p): []} )
        _dict_var = init_indicator_var(indicator, p)
        variables.update({(indicator, p): _dict_var})
 
        indicator = 'TIv2'
        _dict.update( {(indicator, p): []} )
        _dict_var = init_indicator_var(indicator, p)
        variables.update({(indicator, p): _dict_var})

    _timestamp = []
    _mid_price = []

    seq = 0
    print 'total groups:', len(group_o.size().index), len(group_t.size().index)
    
    #main part
    for (gr_o, gr_t) in itertools.izip (group_o, group_t):
        
        if gr_o is None or gr_t is None:
            print 'Warning: group is empty'
            continue
        
        if (wrong_trade_time_diff(gr_t[1])):
            #print 'Warning: trade_time is big'
            continue

        timestamp = (gr_o[1].iloc[0])['timestamp']
        
        if banded:
            gr_o = agg_order_book(gr_o[1], timestamp)
            gr_o = gr_o.reset_index(); del gr_o['index']
        else:
            gr_o = gr_o[1]
 
        gr_t = gr_t[1]

        gr_bid_level = gr_o[(gr_o.type == 0)]
        gr_ask_level = gr_o[(gr_o.type == 1)]
        diff = get_diff_count_units(gr_t)

        mid_price, bid, ask, bid_qty, ask_qty = short_cal_mid_price(gr_bid_level, gr_ask_level, gr_t)

        if bid >= ask:
            seq += 1
            continue

        _timestamp.append (timestamp)
        _mid_price.append (mid_price)
        
        _dict_group = {}
        for (indicator, p) in _dict.keys(): #indicator_fn, param
            level = p[1]
            if level not in _dict_group:
                
                orig_level = level
                level = min (level, len(gr_bid_level), len(gr_ask_level))
                
                _dict_group[level] = (gr_bid_level.head(level), gr_ask_level.head(level))
                
            p1 = () 
            if len(p) == 3:
                p1 = (p[0], level, p[2]) 
            if len(p) == 4:
                p1 = (p[0], level, p[2], p[3]) 
            
            #print indicator

            _i = _l_indicator_fn[indicator](p1, _dict_group[level][0], _dict_group[level][1], diff, variables[(indicator,p)], mid_price)
            _dict[(indicator,p)].append(_i)
        
        for (indicator, p) in _dict.keys(): #indicator_fn, param
            
            col_name = '%s-%s-%s-%s' % (_l_indicator_name[indicator].replace('_','-'),p[0],p[1],p[2])
            if indicator == 'TIv1' or indicator == 'TIv2':
                col_name = '%s-%s-%s-%s-%s' % (_l_indicator_name[indicator].replace('_','-'),p[0],p[1],p[2],p[3])
            
            _dict_indicators[col_name] = _dict[(indicator,p)]

        _dict_indicators['timestamp'] = _timestamp
        _dict_indicators['mid_price'] = _mid_price

        seq += 1
        #print seq,

    fn = indicators_csv (raw_fn)
    df_dict_to_csv (_dict_indicators, fn)


