import cexioapi
import time
import json
import math
import datetime
import colorama
from decimal import Decimal
from colorama import Fore
from colorama import init
from colorama import Back
import os
init(autoreset=True)
delay = 180 #minutes
threshold = .0001
## Limit API calls to prevent IP ban (600 calls per 10 minutes)
def RateLimited(maxPerSecond):
    #http://blog.gregburek.com/2011/12/05/Rate-limiting-with-decorators/
    minInterval = 1.0 / float(maxPerSecond)
    def decorate(func):
        lastTimeCalled = [0.0]
        def rateLimitedFunction(*args,**kargs):
            elapsed = time.clock() - lastTimeCalled[0]
            leftToWait = minInterval - elapsed
            if leftToWait>0:
                time.sleep(leftToWait)
            ret = func(*args,**kargs)
            lastTimeCalled[0] = time.clock()
            return ret
        return rateLimitedFunction
    return decorate

@RateLimited(5) #5/sec true max is 10/sec (600/10 mins) before IP ban
def callAPI(call):
    now = datetime.datetime.now()
    print(Fore.MAGENTA+ "API Call at " + str(time.time())+ ": " + str(now))
    return call
## End Limit API

## Classes and Encoders/Decoders
class Config:
    def __init__(self):
        self.users = []
        self.investments = []
        self.modes=["average", "percent", "any"]
        self.delay = 180
        self.currency = "GHS"#default
    def addUser(self, user):
        self.users.append(user)
    def getUsers(self):
        return self.users
    def setCurrency(self, currency):
        self.currency = currency
    def getCurrency(self):
        return self.currency
    def addInvestment(self, plan):
        self.investments.append(plan)
    def getInvestments(self):
        return self.investments
    def setDelay(self, t):
        if t <= 1:
            t = 1
        self.delay = t
    def getDelay(self):
        return self.delay
class User:
    def __init__(self, name, username, key, secret):
        self.name = name
        self.username = username
        self.key = key
        self.secret = secret
    def getAttr(self, attr):
        if attr=="name":
            return self.name
        elif attr=="username":
            return self.username
        elif attr=="key":
            return self.key
        elif attr=="secret":
            return self.secret
        else:
            return "Attribute not supported."
class InvestmentPlan:
    def __init__(self, currency, enabled, method, threshold):
        self.currency = currency
        self.enabled = enabled
        self.method = method
        self.threshold = threshold
    def getAttr(self, attr):
        if attr == "currency":
            return self.currency
        elif attr == "enabled":
            return self.enabled
        elif attr == "method":
            return self.method
        elif attr == "threshold":
            return self.threshold
        else:
            print("Attribute not supported")
def config_encoder(obj):
    if not isinstance(obj, User) and not isinstance(obj, Config) and not isinstance(obj, InvestmentPlan):
        return default(obj)
    return obj.__dict__
def config_decoder(dct):
    c = Config()
    users = dct['users']
    investments = dct['investments']
    for user in users:
        c.addUser(User(user['name'], user['username'],user['key'],user['secret']))
    for plan in investments:
        c.addInvestment(InvestmentPlan(plan["currency"],plan["enabled"], plan["method"], plan["threshold"]))
    c.setCurrency(dct['currency'])
    c.setDelay(dct['delay'])
    return c
class ConfigBuilder():
    def __init__(self):
        self.building = True
        self.ready = False
        self.config = Config()
        self.currencyIndex = 0
        self.stage = 1
        self.currencies = ["LTC", "NMC", "BTC", "GHS"]
        self.methods = ["average", "percent", "any"]
        while self.building:
            if self.stage == 1:
                self.addAccounts()
            elif self.stage == 2:
                x = input("What would you like to reinvest into? (Default: GHS)")
                try:
                    if len(x) > 0:
                        if self.currencies.index(x.upper()) > -1:
                            self.currency = x.upper()
                    else:
                        self.currency = "GHS"
                    print("Currency set to " + self.currency)
                    self.config.setCurrency(self.currency)
                    self.stage = 3
                except:
                    print("Invalid currency. Try one of these " + " ".join(self.currencies))
            elif self.stage == 3:
                cc = self.currencies[self.currencyIndex]
                if self.currency != cc:
                    x = input("Would you like to reinvest " + cc + " into " + self.currency + "? (y/n)")
                    if x.lower() == "y":
                        self.setupInvestment(cc)
                    elif x.lower() == "n":
                        self.setupCurrency(cc, False, "average", 0)
                        self.currencyIndex += 1
                        if self.currencyIndex > len(self.currencies):
                            self.stage = 4
                else:
                    self.setupCurrency(cc, False, "average", 0)
                    self.currencyIndex += 1
                    if self.currencyIndex >= len(self.currencies):
                        self.stage = 4
            elif self.stage == 4:
                print("A delay should be set between interations to reduce API calls and reduce unnecessary work, especially for low GHS rates.")
                print(Fore.RED+"If the API is called more than 600 times per 10 minutes, your IP may be banned.")
                print("The default is every 180 minutes. The minimum is 1, but not recommended.")
                t = input("How many minutes would you like the program to wait?")
                if t == "":
                    self.config.setDelay(180)
                elif int(t) <= 1:
                    self.config.setDelay(1)
                else:
                    self.config.setDelay(int(t))
                self.stage = 5
            elif self.stage == 5:
                self.building = False
                self.ready = True
    def save(self):
        return saveConfig(self.config)         
    def addAccounts(self):
        name = input("Display name: ")
        username = input("Username: ")
        apikey = input("API Key: ")
        secret = input("API Secret: ")
        user = User(name,username,apikey,secret)
        self.config.addUser(user)
        a = input("Add another? (y|n)")
        if(a == "n"):
            self.stage = 2;
    def setupCurrency(self, currency, enabled, method, threshold):
        self.config.addInvestment(InvestmentPlan(currency, enabled, method, threshold))
    def setupInvestment(self, currency):
        print("Now we need to determine what reinvestment method you'd like to use for " + currency)
        print("'average': Gets the daily average and reinvests at the last trade value if it's below this average.")
        print("'percent': Reinvests if last trade within x% of lowest trade today.")
        print("'any': Reinvests at last trade value, no restrictions.")
        m = input("Which method would you like to use?")
        try:
            if self.methods.index(m) > -1:
                #self.method = m.lower()
                p = 0
                if m == "percent":
                    p = input("What percent threshold would you like to use? (Value without '%')")
                    if round(float(p),5) > 0.00001:
                        p = round(float(p),5)
                    else:
                        print("Percent value must be greater than 0.00001")
                        print("Setting percent to .00001")
                        p = 0.00001
                self.setupCurrency(currency, True, m, p)
                self.currencyIndex += 1
        except:
            print("Invalid method. The options are " + " ".join(self.methods))
## End classes         

## Save built config object to config file
def saveConfig(config):
    try:
        jdata = json.dumps(config,default=config_encoder, sort_keys=True,indent=4, separators=(',', ': '))
        fd = open("config.txt", "w+")
        fd.write(jdata)
        fd.close()
        print("Your config file has been generated successfully. If you'd like to make changes just open it with your favorite text editor.")
        print("If you'd like to start from scratch either rename the file or delete it")
        return config
    except:
        print("Error writing file.")
        pass
## end saveConfig()

## attempt to load file, if except then create config object
def loadConfig():
    try:
        f = open("config.txt","r")
        d = f.read()
        config = json.loads(d)
        config = config_decoder(config)
        f.close();
        return config
    except IOError:
        return ConfigBuilder().save()
        print("no file")
## End loadConfig()

## Begin reinvest using config attributes
def reinvest(name, key, secret, currency, investments):
    print(Fore.RED + "Currency: " + currency)
    api = cexioapi.api(name,key,secret)
    today = datetime.datetime.today()
    for plan in investments:
        pc = plan.getAttr("currency")
        method = plan.getAttr("method")
        threshold = plan.getAttr("threshold")
        enabled = plan.getAttr("enabled")
        color = Back.RED if enabled == False else Back.GREEN
        print(Fore.WHITE +color+ "Currency: " + pc + " Investment Method: " + method + " Threshold: " + str(threshold) + " Enabled: " + str(enabled))
        if enabled == True:#["LTC", "NMC", "BTC", "GHS"]
            couple = ""
            if pc == "LTC" and not currency == "BTC":
                #turn into btc first
                couple = "LTC/BTC"
            elif pc == "NMC" and (currency == "LTC" or currency == "FHM"):
                couple = "NMC/BTC"
                #turn into btc first
            elif pc == "GHS" and currency == "LTC":
                couple = "GHS/BTC"
            elif pc == "FHM" and currency == "GHS":
                #add FM* date checking to switch to GHS after the last day?
                #not here, but just making note
                continue
            else:
                couple = currency +"/"+pc
            print("Checking open orders for " + couple)
            current_orders = callAPI(api.current_orders(couple))
            #print("Length of orders: " + str(len(current_orders)))
            if len(current_orders) > 1:
                for order in current_orders:
                    orderTime = int(order["time"])
                    threeDaysAgo = (int(time.time()) - 259200)
                    if orderTime < threeDaysAgo:
                        wasSuccessful = callAPI(api.cancel_order(int(order["id"])))
                        print("Canceled order " + order["id"] + " ("+wasSuccessful+")")
            else:
                print("No open orders for " + couple)
            ticker = callAPI(api.ticker(couple))
            last = ticker['last']
            last = round(Decimal(last),6)
            print("    Last Trade: " + str(last))
            print("Checking reinvestment criteria for '" + method + "'")
            success = False
            if method == "average":
                average = round((Decimal(ticker["high"])+Decimal(ticker["low"]))/2,6)
                print("    Today's Average: " + str(average))
                if last <= average:
                    success = True
                    #attemptOrder(api,couple, last)
                else:
                    print(Fore.RED + "Last trade isn't below average.")
            elif method == "percent":
                percent = Decimal(threshold)/100;
                low = round(Decimal(ticker["low"]),6)
                print("    Today's low: " + str(low))
                low += low*percent
                print("    Max purhcase threshold (" + str(percent*100)+"%): " + str(low))
                if last <= low:
                    success = True
                    #attemptOrder(api,couple,last)
                else:
                    print("Last trade is not within " + str(percent*100) + "% of today's low")
            elif method == "any":
                success = True
                #attemptOrder(api,couple,last)
            else:
                success = False
                print(Fore.RED+"Invalid mode: " + mode + " please check config file.")
            if success == True:
                cs = couple.split("/")
                if( cs[0] != currency):
                    orderType = 'sell'
                else:
                    orderType = 'buy'
                attemptOrder(api,couple,orderType,last)
## End reinvest loop and sleep

## Attempt to place order through API, called during reinvest loop
def attemptOrder(api,couple,orderType,last):
    balance = callAPI(api.balance())
    cs = couple.split("/")
    threshold = round(Decimal(0.00000001),8)
    if orderType == 'sell':
        switch = [1,0]
    elif orderType == 'buy':
        switch = [0,1]
    available = round(Decimal(balance[cs[switch[1]]]["available"]),8)
    mod = threshold + Decimal(0.000000001) + Decimal(available*Decimal(0.2))#threshold plus 1 decimal place - added fee of 0.00000072 5/27
                                                                #updated fee to 2% 7/7/14
    if cs[0] != "GHS":
        print("Available "+cs[switch[1]]+" Balance: " + "{number:.{digits}f}".format(number=available, digits=8))#str(available))
        if orderType == 'buy':
            order = round(Decimal((available-mod)/last),8)
        elif orderType == 'sell':
            order = round(Decimal((available-mod)),8)
        if order > threshold:
            wasSuccess = callAPI(api.place_order(orderType, order, last, couple))
            #checking cs[switch[1]]
            print(Fore.GREEN+orderType+" of " + "{number:.{digits}f}".format(number=order, digits=8) + " " + cs[0] +" at " + "{number:.{digits}f}".format(number=last, digits=8) + " " + cs[1] + " Total: " + "{number:.{digits}f}".format(number=(order*last), digits=8) +" Success: " + str(wasSuccess))
        else:
            print(Fore.RED+"No order placed, can't trade less than threshold ("+"{number:.{digits}f}".format(number=threshold, digits=8)+").")
    elif cs[0] == "GHS" or cs[0] == "FHM":
        myGH = round(Decimal(balance[cs[switch[0]]]["available"]),8)
        print("Available "+cs[switch[1]]+" Balance: " + "{number:.{digits}f}".format(number=available, digits=8))
        print("Available GH/S: " + "{number:.{digits}f}".format(number=myGH, digits=8))
        if myGH <= 5:
            gh = round(Decimal((available-mod)/last),8)
            print("Possible purchase " + "{number:.{digits}f}".format(number=gh, digits=8) + " ghs")
            print("My GHS: " + "{number:.{digits}f}".format(number=myGH, digits=8) + " <= 5")
            if gh > threshold:
                wasSuccess = callAPI(api.place_order(orderType, gh, last, couple))
                total = round(Decimal(gh*last), 8)
                print(Fore.GREEN+orderType+" of " + "{number:.{digits}f}".format(number=gh, digits=8) + " GHS at " + "{number:.{digits}f}".format(number=last, digits=8) + " " + couple + " Total: " + "{number:.{digits}f}".format(number=total, digits=8) +" Success: " + str(wasSuccess))
            else:
                print(Fore.RED+"No order placed, can't purchase GHS less than threshold ("+"{number:.{digits}f}".format(number=threshold, digits=8)+").")
        else:
            gh = round(Decimal((available-mod)/last),5)
            print("Possible purchase " + str(gh) + " ghs")
            gh = math.floor(gh)
            if gh >= 1:
                wasSuccess = callAPI(api.place_order('buy', gh, last, couple))
                total = round(Decimal(gh*last))
                print(Fore.GREEN+"Order of " + str(gh) + " GH/s at " + str(last) + " " + cs[1] + " Total: " + str(total) +" Success: " + str(wasSuccess))
            elif gh < 1:
                print(Fore.RED+"No order placed, GHS purchase total didn't meet threshhold of 1 GHS")
## End attemptOrder call

#Begin program
while True:
    print("Starting reinvestment interation...")
    print("Loading config file.")
    config = loadConfig()
    delay = config.getDelay()
    num = len(config.getUsers())
    if num > 0:
        for user in config.getUsers():
            print(Fore.CYAN + user.getAttr("name"))
            reinvest(user.getAttr("username"), user.getAttr("key"), user.getAttr("secret"), config.getCurrency(), config.getInvestments())
            if num > 1:
                time.sleep(30)#delay multiple user accounts, help lower API call rate
            print("End of reinvest for " + user.getAttr("name"))
        print("End of user interation, sleeping for " + str(delay) + " minutes.")
    else:
        print(Fore.RED + " No users found in config. Please check file or recreate.")
    time.sleep(60*delay)
## End of file
