import cexioapi
import time
import json
import math
import datetime
import colorama
from decimal import Decimal
from colorama import Fore
from colorama import init
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
    print(Fore.GREEN + "API Call at " + str(time.time())+ ": " + str(now))
    return call
## End Limit API

## Classes and Encoders/Decoders
class Config:
    def __init__(self):
        self.users = []
        self.modes=["average", "percent", "any"]
        self.delay = 180
    def addUser(self, user):
        self.users.append(user)
    def getUsers(self):
        return self.users
    def setReinvestMode(self, mode):
        if mode not in self.modes:
            return False
        else:
            self.mode = mode
            return True
    def getReinvestmentMode(self):
        return self.mode
    def setPercent(self, value):
        self.percent = value
    def getPercent(self):
        return round(float(self.percent),5)
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
def config_encoder(obj):
    if not isinstance(obj, User) and not isinstance(obj, Config):
        return default(obj)
    return obj.__dict__
def config_decoder(dct):
    c = Config()
    users = dct['users']
    for user in users:
        c.addUser(User(user['name'], user['username'],user['key'],user['secret']))
    c.setReinvestMode(dct['mode'])
    c.setPercent(dct['percent'])
    c.setDelay(dct['delay'])
    return c
## End classes

## Create Config object since config file wasn't found
def buildConfig():
    config = Config()
    adding = True
    print("Config file not found. Let's take a few minutes to set it up.")
    i = 0
    while adding:
        if i == 0:
            name = input("Display name: ")
            username = input("Username: ")
            apikey = input("API Key: ")
            secret = input("API Secret: ")
            user = User(name,username,apikey,secret)
            config.addUser(user)
            a = input("Add another? (y|n)")
            if a == "n":
                i += 1
        elif i == 1:
            print("Now we need to determine what reinvestment mode you'd like to use.")
            print("'average': Gets the daily average and reinvests at the last trade value if it's below this average.")
            print("'percent': Reinvests if last trade within x% of lowest trade today.")
            print("'any': Reinvests at last trade value, no restrictions.")
            m = input("Which mode would you like to use?")
            if config.setReinvestMode(m) == False:
                print("Sorry that wasn't a valid reinvestment mode.")
            else:
                if m == "percent":
                    p = input("What percent threshold would you like to use? (Value without '%')")
                    if round(float(p),5) > 0.00001:
                        config.setPercent(round(float(p),5))
                        ##adding = False
                        i += 1
                    else:
                        print("Percent value must be greater than 0.00001")
        elif i == 2:
            print("A delay should be set between interations to reduce API calls and reduce unnecessary work, especially for low GHS rates.")
            print(Fore.RED+"If the API is called more than 600 times per 10 minutes, your IP may be banned.")
            print("The default is every 180 minutes. The minimum is 1, but not recommended.")
            t = input("How many minutes would you like the program to wait?")
            if t == "":
                config.setDelay(180)
            elif int(t) <= 1:
                config.setDelay(1)
            else:
                config.setDelay(int(t))
            adding = False
    saveConfig(config)
## End buildConfig()

## Save built config object to config file
def saveConfig(config):
    try:
        jdata = json.dumps(config,default=config_encoder, sort_keys=True,indent=4, separators=(',', ': '))
        fd = open("config.txt", "w+")
        fd.write(jdata)
        fd.close()
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
        return buildConfig()
        print("no file")
## End loadConfig()

## Begin reinvest using config attributes
def reinvest(name, key, secret):
    api = cexioapi.api(name,key,secret)
    currency = 'GHS/BTC'
    today = datetime.datetime.today()
    if datetime.date(today.year, today.month,today.day) < datetime.date(2014,5,26):
        currency = 'FHM/BTC'
    print("Currency: " + currency)
    current_orders = callAPI(api.current_orders())
    data = current_orders
    if len(data)>0:
        for order in data:
            orderTime = int(order['time'])
            threeDaysAgo = (int(time.time()) - 259200)
            if orderTime < threeDaysAgo:
                #cancel order
                wasSuccessful = callAPI(api.cancel_order(int(order["id"])))
                print("Canceled order " + order["id"] + " ("+wasSuccessful+")")
    else:
        print("No open orders")
    ticker = callAPI(api.ticker(currency))
    mode = config.getReinvestmentMode()
    last = round(Decimal(ticker["last"]),6)
    print("    Last Trade: " + str(last))
    if mode == "average":
        average = round((Decimal(ticker["high"])+Decimal(ticker["low"]))/2,6)
        print("    Today's Average: " + str(average))
        if last <= average:
            attemptOrder(api,currency, last)
        else:
            print(Fore.RED + "Last trade isn't below average.")
    elif mode == "percent":
        percent = Decimal(config.getPercent())/100;
        low = round(Decimal(ticker["low"]),6)
        print("    Today's low: " + str(low))
        low += low*percent
        print("    Max purhcase threshold (" + str(percent*100)+"%): " + str(low))
        if last <= low:
            attemptOrder(api,currency,last)
        else:
            print("Last trade is not within " + str(percent*100) + "% of today's low")
    elif mode == "any":
        attemptOrder(api,currency,last)
    else:
        print(Fore.RED+"Invalid mode: " + mode + " please check config file.")
## End reinvest loop and sleep

## Attempt to place order through API, called during reinvest loop
def attemptOrder(api,currency, last):
    balance = callAPI(api.balance())
    available = round(Decimal(balance['BTC']["available"]),6)
    myGH = round(Decimal(balance['GHS']["available"]),6)
    print("Available BTC Balance: " + str(available))
    print("Available GH/S: " + str(myGH))
    mod = Decimal(threshold) + Decimal(.00001)
    if myGH <= 5:
        gh = round(Decimal((available-mod)/last),4)
        print("Possible purchase " + str(gh) + " ghs")
        print("My GHS: " + str(myGH) + " <= 5")
        if gh > 0.0001:
            wasSuccess = callAPI(api.place_order('buy', gh, last, currency))
            print("Order of " + str(gh) + " GH/s at " + str(last) + " GH/BTC Total: " + str(gh*last) +" Success: " + str(wasSuccess))
        else:
            print("No order placed, can't purchase GH/s less than threshold ("+str(threshold)+").")
    else:
        gh = round(Decimal((available-mod)/last),5)
        print("Possible purchase " + str(gh) + " ghs")
        gh = math.floor(gh)
        if gh >= 1:
            wasSuccess = callAPI(api.place_order('buy', gh, last, currency))
            print("Order of " + str(gh) + " GH/s at " + str(last) + " GH/BTC Total: " + str(gh*last) +" Success: " + str(wasSuccess))
        elif gh < 1:
            print("No order placed, gh purchase total didn't meet threshhold of 1 GH/S")
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
            print(Fore.BLUE + user.getAttr("name"))
            reinvest(user.getAttr("username"), user.getAttr("key"), user.getAttr("secret"))
            if num > 1:
                time.sleep(30)#delay multiple user accounts, help lower API call rate
            print("End of reinvest for " + user.getAttr("name"))
        print("End of user interation, sleeping for " + str(delay) + " minutes.")
    else:
        print(Fore.RED + " No users found in config. Please check file or recreate.")
    time.sleep(60*delay)
## End of file
