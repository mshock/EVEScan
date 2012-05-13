##############################################################################
# EVEscan logic library (ELL)
#
# Copyright (C) 2010 Matt Shockley 
#
#    
#
##############################################################################

import cPickle as pickle, tkFileDialog, re, os, shutil, subprocess, time
from reverence import blue
from multiprocessing import Process, Queue

# EVE install directory
# TODO: add GUI control
EVEROOT = r"F:\Program Files\EVE"

# cache path
# TODO: add GUI control
cachepath = "C:\Users\Shockley\AppData\Local\CCP\EVE\f_program_files_eve_tranquility\cache\MachoNet\87.237.38.200\272\CachedMethodCalls"

# install path
# TODO: make installer, determine at installation
installpath = "F:\\EVEScan"

# determine OS and username (for default log path)
opsys = os.name
username = os.environ.get("USERNAME")

# global variables
regions = []
caches = []
hubs = ['Jita', 'Amarr', 'Rens', 'Dodixie', 'Hek', 'Oursulaert']

# version
version = "1.4 Alpha"

# load pickled system id:name and item name:size dicts
system_info = pickle.load(open(os.path.join("Data","systems.p")))
item_info = pickle.load(open(os.path.join("Data","item_info.p")))

# convert dates in EVE caches to YMD format
def evetime2date(evetime):
        s = (evetime - 116444736000000000) / 10000000 
        return time.strftime("%Y-%m-%d", time.gmtime(s))

# scan new cache files, export all market orders found to csv and then import
# old cache files will be ignored, returning empty list
def read_cache(filename):
    # only scan new cache files and the most recent
    # caches global var to keep track of this
    if filename in caches and filename != caches[-1]:
        return []
    if filename != [-1]:
        caches.append(filename)
    # fork dumper process and wait
    #subprocess.call([os.path.join(installpath, "dumper.exe"), "--market", os.path.join(cachepath, filename), '>'])
    # create dumper command
    dumper = os.path.join(installpath, "Dumper", "dumper.exe")
    args = ["--market",  os.path.join(cachepath, filename)]
    command = [dumper]
    command.extend(args)
    # execute and read the output pipe
    orders_raw = subprocess.Popen(command, stdout = subprocess.PIPE).communicate()[0]
    # throw out those headers in the first line...
    # convert to list of lines
    return orders_raw.splitlines()[1:]

# reverence cache reader function
def read_cache2():
    lines = []
    eve = blue.EVE(EVEROOT)
    cfg = eve.getconfigmgr()
    cachemgr = eve.getcachemgr()
    cmc = cachemgr.LoadCacheFolder("CachedMethodCalls")
    for key, obj in cmc.iteritems():
        if key[1]=="GetOrders":
            item = cfg.invtypes.Get(key[3])
            region = cfg.evelocations.Get(key[2])
            print "Processing " + item.name + " [" + region.locationName +"]... \n"
            for record in obj['lret']:
                for order in record:
                    lines.append("%(price).2f,%(volRemaining)i,%(type)s,%(range)i,%(orderID)i,%(volEntered)i,%(minVolume)i,%(bid)s,%(duration)i,%(stationID)i,%(region)s,%(solarSystemID)i,%(jumps)i,%(typeID)i\n" % \
                            {'price': order['price'],'volRemaining': order['volRemaining'], 'type': item.name, 'range': order['range'], 'orderID': order['orderID'], 'volEntered': order['volEntered'], 'minVolume': order['minVolume'], 'bid': order['bid'], 'duration': order['duration'], 'stationID': order['stationID'], 'region': region.locationName, 'solarSystemID': order['solarSystemID'], 'jumps': order['jumps'], 'typeID': order['typeID']})
    print "done"
    return lines                                                                                                                                                                                                                                                                                                                                                                                                                                                                
                                                                                                                                                                                                                    
                    

# archive all market logs in EVE log folder (EVE_log/Archive)
def archiveLogs(EVElogs):
    if not os.path.isdir(EVElogs):
        return "EVE market log directory does not exist"
    if not os.path.isdir(os.path.join(EVElogs, "Archive")):
        os.mkdir(os.path.join(EVElogs, "Archive"))
    for filename in os.listdir(EVElogs):
        if matchEVElog(filename):
            shutil.move(os.path.join(EVElogs,filename), os.path.join(EVElogs, "Archive"))
    return "All market logs have bene archived in " + os.path.join(EVElogs, "Archive")
            

# return current version
def getversion():
    return version

# returns a list of all regions in the eve market logs 
def getRegions(logpath):
    # loop over all log files in EVE log directory
    for filename in os.listdir(logpath):
        # regex to pull region, item name, and date from file name
        match = matchEVElog(filename)
        if match:
            region = match.group(1)
            if region not in regions:
                regions.append(region)
    return regions

# sets the tkinter variables to the OS-appropriate default logpath
def setlogs(EVE_logs, logpath):
    if opsys == 'nt':
        EVE_logs.set(os.path.join("C:","Users", username, "Documents", "EVE", "logs", "Marketlogs"))
    elif opsys == 'mac':
        EVE_logs.set(os.path.join("~", "Library", "Preferences", "EVE Online Preferences", "p_drive", "My Documents", "EVE"))
    else:
        EVE_logs.set("path not found")
    logpath.set(os.path.join(os.path.expanduser("~"), "EVEscan"))

# sets the title of the tkinter window object to EVEscan + version
def setTitleVersion(window):
    window.title("EVEscan " + version)

# folder path select dialog window
def select_path(path):
    directory = tkFileDialog.askdirectory()
    return path.set(directory)


# itemObject class, stores item market info
class itemObject:
    def __init__(self):
        self.buy_prices = []
        self.sell_prices = []
        self.buy_systems = []
        self.sell_systems = []
        self.buy_volumes = []
        self.sell_volumes = []
        self.buy_regions = []
        self.sell_regions = []
        self.id = -1;

class itemObject2:
    def __init__(self):
        self.buy_info = []
        self.sell_info = []
        self.id = -1;

# numberFormat func, takes numeric returns formatted string
def numberFormat(number):
    if number >= 1e6:
        return str(round(number / 1e6, 2)) + "M"
    elif number >= 1e3:
        return str(round(number / 1e3, 2)) + "k"
    else:
        return  str(round(number, 2))

# returns a regex match group on EVE market log filename
#   group(1) = region name
#   group(2) = item name
#   group(3-5) = year (DDDD), month (DD), day (DD)
def matchEVElog(name):
    return re.match("([^-]+)-(.+)-(.+)\.(.+)\.(.+) .*", name)

# fork a new process to execute a function
# return the result via IPC
# http://code.activestate.com/recipes/511474-run-function-in-separate-process/
# untested, only works on unix
def fork_func(func, *args, **kwds):
    pread, pwrite = os.pipe()
    pid = os.fork()
    if pid > 0:
        os.close(pwrite)
        with os.fdopen(pread, 'rb') as f:
            status, result = pickle.load(f)
        os.waitpid(pid, 0)
        if status == 0:
            return result
        else:
            raise result
    else: 
        os.close(pread)
        try:
            result = func(*args, **kwds)
            status = 0
        except Exception, exc:
            result = exc
            status = 1
        with os.fdopen(pwrite, 'wb') as f:
            try:
                pickle.dump((status,result), f, pickle.HIGHEST_PROTOCOL)
            except pickle.PicklingError, exc:
                pickle.dump((2,exc), f, pickle.HIGHEST_PROTOCOL)
        os._exit(0)

# scan cache in a different process
def scan_cache2(digest):
    return fork_func2(digest)

                            
def fork_func2(analysis, log, items, digest):
    q = Queue()
    print "forking new process"
    p = Process(target=scan_cache, args=(digest,q,))
    p.start()
    print "waiting for results..."
    return q.get(block = True)
            
            

# scans the logfiles in the EVE market logs directory for possible trades
# returns a list of strings, where each element is a new line of output for the GUI display window (Listbox)
# previous cache scanning ability moved to scan_cache (not using the dumper.exe method read_cache)
def scan(digest):
    # initializations
    analysis = {}
    items = []
    slogpath = digest.textlog
    sEVE_logs = digest.EVElog

    # check EVE log directory
    if not os.path.isdir(sEVE_logs):
        return "EVE market log path does not exist."    
    # open results log file
    if not os.path.isdir(slogpath):
        os.mkdir(slogpath)
    log = open(os.path.join(slogpath, time.strftime("%m-%d-%Y_%Hh%Mm.txt",time.localtime())), 'w')
    
   

    # loop over all log files in EVE log directory
    for filename in os.listdir(sEVE_logs):
        if os.path.isdir(os.path.join(sEVE_logs,filename)):
            continue
        # scanning log files...        
        # regex to pull region, item name, and date from file name
        match = matchEVElog(filename)
        if match:
            region = match.group(1)
            # if forcing regions, skip this file if not within user specified regions
            if digest.force_regions and not (region in digest.from_region or region in digest.to_region):
                continue
            # if region not logged, add it to the regions list
            if region not in regions:
                regions.append(region)
            item = match.group(2)
            # if item not logged, add it to the items list
            if item not in items:
                items.append(item)
                # create new itemObject to hold item market info
                analysis[item] = itemObject()
            # get current item
            i = analysis[item]
            # open next EVE log file
            f = open(os.path.join(sEVE_logs,filename))
            # discard first line (table headers)
            f.readline()
            for line in f:
                if not line:
                    continue
                # parse CSV
                col = line.split(',')
                price = col[0]
                volume = col[1]
                regionid = col[11]
                systemid = col[12]
                sell = col[7]
                # get system name from lookup dict
                system = system_info[systemid]['name']

                i.id = col[2]
                
                # buy order
                if sell == 'False':
                    i.buy_prices.append(float(price))
                    i.buy_systems.append(system)
                    i.buy_volumes.append(float(volume))
                    i.buy_regions.append(region)
                # sell order
                elif sell == 'True':
                    i.sell_prices.append(float(price))
                    i.sell_systems.append(system)
                    i.sell_volumes.append(float(volume))
                    i.sell_regions.append(region)
        return analyze(analysis, log, items, digest)
        #fork_func2(analysis, log, items, digest)

# scans the cache files for all orders
# TODO: added functionality to trade finder
#   - find potentially profitable sell orders
#
def scan_cache(digest):
    csv = read_cache2()
    analysis = {}
    systems = {}
    items = []
    slogpath = digest.textlog
    sec_thresh = digest.security_thresh
    sEVE_logs = digest.EVElog
    spec = digest.speculate
    print "scanning cache..."
    if not os.path.isdir(slogpath):
        os.mkdir(slogpath)
    log = open(os.path.join(slogpath, time.strftime("%m-%d-%Y_%Hh%Mm.txt",time.localtime())), 'w')
    
    for line in csv:
        if not line:
            continue
        
            
        
        line = line.rstrip()
        col = line.split(',')
        # filter all those scams out (min volume)
        if int(col[6]) > 1:
            print "throwing out scam: (" + str(col[6]) + ") " + str(col[2])
            continue
        item = col[2]
        region = col[10]

        price = col[0]
        volume = col[1]
        systemid = col[11]
        sell = col[7]        
        
        # throw this region out if it is below the security threshold
        security = round(float(system_info[systemid]['security']),2)
        if security < sec_thresh:
            continue

        system = system_info[systemid]['name']
        
        if digest.force_regions and not (region in digest.from_region or region in digest.to_region):
            continue
        if not region in regions:
            regions.append(region)
        if not item in items:
            items.append(item)
            analysis[item] = itemObject()
        if not system in systems.keys():
            systems[system] = {}
        if not item in systems[system].keys():
            systems[system][item] = itemObject2()
                

        # get system name from lookup dict
        system_name = system + " (" + str(security) + ")"
        # get current item
        i = analysis[item]
        i.id = col[13]
        # get current system item
        s = systems[system][item]
        s.id = col[13]
        
        # buy order
        if sell == 'False':
            i.buy_prices.append(float(price))
            i.buy_systems.append(system_name)
            i.buy_volumes.append(float(volume))
            i.buy_regions.append(region)
            
            s.buy_info.append((float(price), float(volume), region, str(security)))
        # sell order
        elif sell == 'True':
            
            i.sell_prices.append(float(price))
            i.sell_systems.append(system_name)
            i.sell_volumes.append(float(volume))
            i.sell_regions.append(region)

            s.sell_info.append((float(price), float(volume), region, str(security)))
    #return fork_func2(analysis, log, digest, systems)
    return analyze(analysis, log, items, digest, systems)

def analyze(analysis, log, items, digest, systems):
    # some logging variable inits
    logged_count = 0
    printed_count = 0
    results = "\n"
    results2 = []            
    spec = digest.speculate
    invest = digest.invest
    routes = {}

    print "beginning analysis"
    
    # iterate over all systems and find best deals for trades between them over all items available
    for key in systems.keys():
        system = systems[key]
        if False:
                disp = 1
        else:
                disp = 0
        print "checking trades from system: " + key
        for key2 in system.keys():
            item = system[key2]
            if disp:
                    print "for item: " + key2
            # check prices against all the other systems, calculate total potential profit for each item
            for key3 in systems.keys():
                system2 = systems[key3]
                if disp:
                        print "sell system: " + key3
                # check if item is in second system
                if key2 in system2.keys():
                    #print "item match found"
                    item2 = system2[key2]
                    # check if there are sell orders in first system and buy orders in the second system
                    if (spec and item.buy_info and item2.buy_info) or (not spec and item.buy_info and item2.sell_info):
                        #print "potential trades found"
                        # sort prices: sell ascending and buy ascending
                        if not invest:
                            # either immediate buy low, sell high
                            temp_item1 = sorted(item.buy_info, key=lambda price: price[0], reverse=True)
                            
                            if not spec:    
                                temp_item2 = sorted(item2.sell_info, key=lambda price: price[0])
                            else:
                                # if speculating, we are buying to post sell orders
                                temp_item2 = sorted(item2.buy_info, key=lambda price: price[0], reverse=True)
                        else:
                            # placing buy orders to later post sell orders
                            temp_item1 = sorted(item.sell_info, key=lambda price: price[0], reverse=True)
                            temp_item2 = sorted(item2.buy_info, key=lambda price: price[0])
                        
                        
                        sell_vol = 0
                        buy_vol = 0
                        profit = 0
                        capital = 0
                        quantity = 0
                        buymax = temp_item1[-1][0]
                        sellmin = temp_item2[-1][0]
                        buyregion = temp_item1[0][2] 
                        sellregion = temp_item2[0][2]
                        buysec = " (" + temp_item1[0][3] + ")"
                        sellsec = " (" + temp_item2[0][3] + ")"
                        if disp:
                            print temp_item1
                            print temp_item2
                            print "min: " + str(sellmin)
                            print "max: " + str(buymax)
                        # keep calculating profit until out of buy or sell orders
                        while True:
                            if not buy_vol:
                                try:
                                    buy_item = temp_item1.pop()
                                except Exception:
                                    #print "break on buy pop"
                                    break
                                buy_price = buy_item[0]
                                buy_vol = buy_item[1]
                            if not sell_vol:
                                try:
                                    sell_item = temp_item2.pop()
                                except Exception:
                                    #print "break on sell pop"
                                    break
                                sell_price = sell_item[0]
                                sell_vol = sell_item[1]
                          
                            if disp:
                                    print "buy price: " + str(buy_price) + "buy vol: " + str(buy_vol)
                                    print "sell price: " + str(sell_price) + "sell vol: " + str(sell_vol)
                                    
                            
                            if sell_price > buy_price:
                                if not spec:
                                    if sell_vol <= buy_vol:
                                        buy_vol -= sell_vol
                                        profit += sell_vol * (sell_price - buy_price)
                                        capital += sell_vol * buy_price
                                        quantity += sell_vol
                                        sell_vol = 0
                                    else:
                                        sell_vol -= buy_vol
                                        profit += buy_vol * (sell_price - buy_price)
                                        capital += buy_vol * buy_price
                                        quantity += buy_vol
                                        buy_vol = 0
                                else:
                                    if spec:
                                        if not key3 in hubs:
                                            break
                                    quantity += buy_vol
                                    profit += buy_vol * (sell_price - buy_price)
                                    capital += buy_vol * buy_price
                                    buy_vol = 0
                            else:
                                #print "break on price comp"
                                break
                        try:
                            test = item_info[str(item.id)]
                            volume = quantity * float(item_info[str(item.id)]['vol'])
                        except KeyError:
                            print "item not in database: " + key2
                            break
                        
                        fprofit = numberFormat(profit)
                        
                        
                        if profit >= digest.print_thresh:
                            if volume:
                                cargo_eff = numberFormat(profit / volume)
                            else:
                                cargo_eff = "ER"
                            if capital:
                                cap_eff = numberFormat(profit / capital)
                            else:
                                cap_eff = "ER"
                            if disp:
                                print key2 + " (" + key + " -> " + key3 + ") " + fprofit
                                print "sellregion: " + sellregion + " buyregion: " + buyregion
                        # user control conditionals
                            if ((sellregion in digest.to_region or digest.to_region == "Any") and
                                (buyregion in digest.from_region or digest.from_region == "Any") and
                                (digest.cargo_thresh >= volume or digest.cargo_thresh == 0) and
                                (digest.capital_thresh >= capital or digest.capital_thresh == 0)):
                                #print "added"    
                                results2.append((key2,fprofit,cargo_eff,cap_eff,buyregion,sellregion,key + buysec,key3 + sellsec,numberFormat(buymax),numberFormat(sellmin),numberFormat(capital),numberFormat(volume),numberFormat(quantity)))
                            
                            
    """                        
    # iterate through all items for which orders were found
    for key in analysis.keys():
        # get current item
        current = analysis[key]
        # if there are no buy or sell orders, no profit can be made
        if current.buy_prices != [] and current.sell_prices != []:
            # get maximum sell and minimum buy prices and their indices
            buymin = min(current.buy_prices)
            buyvol = current.buy_volumes[current.buy_prices.index(buymin)]
            sellmax = max(current.sell_prices)
            sellvol = current.sell_volumes[current.sell_prices.index(sellmax)]
            buysys = -1
            sellsys = -1
            profit = 0
            buytotal = 0
            selltotal = 0
            
            # if there is a potential profit
            if buymin < sellmax:

                # check total potential region profit for this item
                
                # iterate through all buy orders for this item
                for index,order in enumerate(current.buy_prices):
                    if order < sellmax:
                        projected_profit = (sellmax - order) * min(current.buy_volumes[index], sellvol)
                        if  projected_profit >= profit:
                            profit = projected_profit
                            buymin = order
                            buysys = index
                            buyvol = current.buy_volumes[index]
                            
                # iterate through all sell orders for this item                        
                for index,order in enumerate(current.sell_prices):
                    if order > buymin:
                        projected_profit = (order - buymin) * min(current.sell_volumes[index], buyvol)
                        if projected_profit >= profit:
                            profit = projected_profit
                            sellmax = order
                            sellsys = index
                            sellvol = current.sell_volumes[index]
                            
                # txt file log
                if profit > digest.log_thresh:
                    logged_count += 1

                    if not str(current.id) in item_info:
                        continue
                    
                    # calculate all log values
                    volume = float(item_info[str(current.id)]['vol']) * min(current.buy_volumes[buysys],current.sell_volumes[sellsys])
                    capital = min(current.buy_volumes[buysys],current.sell_volumes[sellsys]) * buymin
                    quantity = min(current.buy_volumes[buysys],current.sell_volumes[sellsys])
                    buyprice = current.buy_prices[buysys]
                    sellprice = current.sell_prices[sellsys]
                    buysystem = current.buy_systems[buysys]
                    sellsystem = current.sell_systems[sellsys]
                    buyregion = current.buy_regions[buysys]
                    sellregion = current.sell_regions[sellsys]
                    fprofit = numberFormat(profit)

                    log.write(key + '\n')
                    log.write("PROFIT: " + fprofit + ' isk\n')
                    log.write("VOLUME: " + numberFormat(volume) + ' m3\n')
                    log.write("CAPITAL: " + numberFormat(capital) + ' isk\n')
                    log.write("QUANTITY: " + numberFormat(quantity) + '\n')
                    log.write(buyregion + " => " + sellregion + '\n')
                    log.write(buysystem + " -> " + sellsystem + '\n')
                    log.write(numberFormat(buyprice) + " -> " + numberFormat(sellprice) + '\n\n')
                    
                    # terminal log
                    if profit >= digest.print_thresh:
                        # user control conditionals
                        if ((sellregion in digest.to_region or digest.to_region == "Any") and
                            (buyregion in digest.from_region or digest.from_region == "Any") and
                            (digest.cargo_thresh >= volume or digest.cargo_thresh == 0) and
                            (digest.capital_thresh >= capital or digest.capital_thresh == 0)):
                            printed_count += 1
                            results2.append((key,fprofit,buyregion,sellregion,buysystem,sellsystem,numberFormat(buyprice),numberFormat(sellprice),numberFormat(capital),numberFormat(volume),numberFormat(quantity)))
                                
##                            results += key + "\n"
##                            results += "PROFIT: " + fprofit + " isk\n"
##                            results += "VOLUME: " + numberFormat(volume) + " m3\n"
##                            results += "CAPITAL: " + numberFormat(capital) + " isk\n"
##                            results += "QUANTITY: " + numberFormat(quantity) + "\n"
##                            results += buyregion + " => " + sellregion + "\n"
##                            results += buysystem + " -> " + sellsystem + "\n"
##                            results += numberFormat(buyprice) + " -> " + numberFormat(sellprice) + "\n\n"

    log.close()
    # print results and statistics
    results += "[REGIONS SCANNED] : " + ', '.join(regions) + '\n'
    results += "[ITEMS INDEXED] : " + str(len(items)) + '\n'
    results += "[TRADES FOUND] : " + str(logged_count) + '\n'
    results += "[MATCHES FOUND] : " + str(printed_count) + '\n'
    #return results.split('\n')
    """
    #q.put(results2)
    print "done with analysis"
    return results2
