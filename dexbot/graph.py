"""
A graph utility module
"""

from dexbot.storage import data_dir
from os.path import join
import os
import numpy

import datetime, time
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def save_data(botname,*data,tardis=None):
    """
    Save some data into a per-bot file. Data items are space-separated. Current timestamp is added as first column
    (Mainly for testing, "tardis" allows a different time to be specified)
    """
    with open(join(data_dir,botname+'.dat'),"a") as fd:
        now = tardis or time.time()
        fd.write(" ".join(str(i) for i in [now]+list(data))+"\n")
        
def get_file(botname,cols):
    f1 = join(data_dir,botname+'.dat')
    if not os.access(f1,os.R_OK): return None
    f2 = join(data_dir,botname+'.dat2')
    try:
        os.rename(f1,f2)
        a1 = numpy.loadtxt(f2)
        a1 = a1.transpose() # so now arrays of dates, value1, value2 and so on

        dates = [datetime.datetime.utcfromtimestamp(i) for i in a1[0]]
        daylocator = mdates.DayLocator()
        daysFmt = mdates.DateFormatter('%b %d')

        fig, ax = plt.subplots()
        args = []
        i = 1
        for i in range(0,len(cols)):
            args.extend([dates,a1[i+1],cols[i][0]])
        lines = ax.plot(*args)
        for i in range(0,len(cols)):
            lines[i].set_label(cols[i][1])
        # format the ticks
        ax.xaxis.set_major_locator(daylocator)
        ax.xaxis.set_major_formatter(daysFmt)
        ax.set_xlim(min(dates), max(dates))

        # format the coords message box
        def price(x):
            return '$%1.2f' % x
        #ax.format_xdata = mdates.DateFormatter('%Y-%m-%d')
        ax.format_ydata = price
        ax.grid(True)
        ax.legend()
        # rotates and right aligns the x labels, and moves the bottom of the
        # axes up to make room for them
        fig.autofmt_xdate()
        
        plotfile = join(data_dir,botname+'.png')
        plt.savefig(plotfile,bbox_inches='tight')
        return plotfile
    
    finally:
        try:
            os.unlink(f2)
        except: pass
    
if __name__ == '__main__':
    save_data('fakebot',17.0,25,tardis=time.mktime((2018,1,30,10,20,0,0,0,-1)))
    save_data('fakebot',18.3,26,tardis=time.mktime((2018,2,1,10,24,0,0,0,-1)))
    save_data('fakebot',21.4,32,tardis=time.mktime((2018,2,2,10,0,0,0,0,-1)))
    save_data('fakebot',25.2,34,tardis=time.mktime((2018,2,3,8,20,0,0,0,-1)))
    save_data('fakebot',26.8,34,tardis=time.mktime((2018,2,4,7,20,0,0,0,-1)))
    save_data('fakebot',16.4,36,tardis=time.mktime((2018,2,5,21,40,0,0,0,-1)))
    save_data('fakebot',15.1,37,tardis=time.mktime((2018,2,6,12,14,20,0,0,-1)))
    print(get_file('fakebot',[('g','AUD'),('r','BTS')]))
