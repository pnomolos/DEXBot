from math import fabs
from pprint import pprint
from collections import Counter
from bitshares.amount import Amount
from bitshares.price import Price, Order, FilledOrder
from dexbot.basestrategy import BaseStrategy, ConfigElement

import pdb
        
class Strategy(BaseStrategy):

    @classmethod
    def configure(cls):
        return BaseStrategy.configure()+[
            ConfigElement("spread","float",5,"Percentage difference between buy and sell",(0,100)),
            ConfigElement("wall","float",0.0,"the default amount to buy/sell, in quote",(0.0,None)),
            ConfigElement("max","float",100.0,"bot will not trade if price above this",(0.0,None)),
            ConfigElement("min","float",100.0,"bot will not trade if price below this",(0.0,None)),
            ConfigElement("start","float",100.0,"Starting price, as percentage of bid/ask spread",(0.0,100.0)),
            ConfigElement("reset","bool",False,"bot will alwys reset orders on start",(0.0,None)),
            ConfigElement("staggers","int",1,"Number of additional staggered orders to place",(1,100)),
            ConfigElement("staggerspread","float",5,"Percentage difference between staggered orders",(1,100))
        ]


    def safe_dissect(self,thing,name):
        try:
            self.log.debug("%s() returned type: %r repr: %r dict: %r" % (name,type(thing),repr(thing),dict(thing)))
        except:
            self.log.debug("%s() returned type: %r repr: %r" % (name,type(thing),repr(thing)))


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Define Callbacks
        self.onMarketUpdate += self.onmarket
        if self.bot.get("reset",False):
            self.cancel_all()
        self.reassess()
                                           
    def updateorders(self,newprice):
        """ Update the orders
        """

        self.log.info("Replacing orders. Baseprice is %f" % newprice)
        self['price'] = newprice
        step1 = (self.bot['spread']/2)/100.0
        step2 = self.bot['staggerspread']/100.0
        # Canceling orders
        self.cancel_all()
        myorders = {}

        if newprice < self.bot["min"]:
            self.disabled = True
            self.log.critical("Price %f is below minimum %f" % (newprice,self.bot["min"]))
            return
        if newprice > self.bot["max"]:
            self.disabled = True
            self.log.critical("Price %f is above maximum %f" % (newprice,self.bot["max"]))
            return
        
        if float(self.balance(self.market["quote"])) < self.bot["wall"]*self.bot['staggers']:
            self.log.critical("insufficient sell balance: %r (needed %f)" % (self.balance(self.market["quote"]),self.bot["wall"]))
            self.disabled = True # now we get no more events
            return

        if self.balance(self.market["base"]) < newprice * self.bot["wall"] * self.bot['staggers']:
            self.disabled = True
            self.log.critical("insufficient buy balance: %r (need: %f)" % (self.balance(self.market["base"]),self.bot["wall"]*buy_price))
            return
    
        amt = Amount(self.bot["wall"], self.market["quote"])
        
        sell_price = newprice+step1
        for i in range(0,self.bot['staggers']):
            self.log.info("SELL {amt} at {price} {base}/{quote} (= {inv_price} {quote}/{base})".format(
                amt=repr(amt),
                price=sell_price,
                inv_price = 1/sell_price,
                quote=self.market['quote']['symbol'],
                base=self.market['base']['symbol']))
            ret = self.market.sell(
                sell_price,
                amt,
                account=self.account,
                returnOrderId="head"
            )
            self.log.debug("SELL order done")
            myorders[ret['orderid']] = sell_price
            sell_price += step2
            
        buy_price = newprice-step1
        for i in range(0,self.bot['staggers']):
            self.log.info("BUY {amt} at {price} {base}/{quote} (= {inv_price} {quote}/{base})".format(
                amt=repr(amt),
                price = buy_price,
                inv_price = 1/buy_price,
                quote=self.market['quote']['symbol'],
                base=self.market['base']['symbol']))
            ret = self.market.buy(
                buy_price,
                amt,
                account=self.account,
                returnOrderId="head",
            )
            self.log.debug("BUY order done")
            myorders[ret['orderid']] = buy_price
            buy_price -= step2
        self['myorders'] = myorders
        #ret = self.execute() this doesn't seem to work reliably
        #self.safe_dissect(ret,"execute")

    def onmarket(self, data):
        self.safe_dissect(data)
        if type(data) is FilledOrder and data['account_id'] == self.account['id']:
            self.log.debug("data['quote']['asset'] = %r self.market['quote'] = %r" % (data['quote']['asset'],self.market['quote']))
            if data['quote']['asset'] == self.market['quote']:
                self.log.debug("I think its a SELL to us of %r" % data['quote'])
            if data['base']['asset'] == self.market['quote']:
                self.log.debug("I think its a BUY from us of %r" % data['base'])
            self.reassess()

    def reassess(self):
        # sadly no smart way to match a FilledOrder to an existing order
        # even price-matching won't work as we can buy at a better price than we asked for
        # so look at what's missing
        self.account.refresh()
        still_open = set(i['id'] for i in self.account.openorders)
        if len(still_open) == 0:
            self.log.info("no open orders, recalculating the startprice")
            t = self.market.ticker()
            bid = float(t['highestBid'])
            ask = float(t['lowestAsk'])
            self.updateorders(bid+((ask-bid)*self.bot['start']/100.0))
            return
        missing = set(self['myorders'].keys()) - still_open
        if missing:
            found_price = 0.0
            highest_diff = 0.0
            for i in missing:
                diff = fabs(self['price']-self['myorders'][i])
                if diff > highest_diff:
                    found_price = self['myorders'][i]
                    highest_diff = diff
            self.updateorders(found_price)
            self.reassess() # check if order has been filled while we were busy entering orders

