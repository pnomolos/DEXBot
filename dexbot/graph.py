"""
A graph utility module
"""

from dexbot.storage import data_dir
from os.path import join
import os
import shutil, numpy

import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.cbook as cbook


def save_data(botname,*data):
    """
    Save some data into a per-bot file. Data items are space-separated. Timestamp is added as first column
    """
    with open(join(data_dir,botname+'.dat'),"a") as fd:
        now = time.time()
        fd.write(" ".join([str(now)]+data)+"\n")
        
def get_file(botname):
    f1 = join(data_dir,botname+'.dat')
    if not os.access(f1,os.R_OK): return
    f2 = join(data_dir,botname+'.dat2')
    try:
        os.rename(f1,f2)
        a1 = numpy.loadtxt(f2)
        a1.transpose() # so arrays of dates, value1, value2 and so on

        hourlocator = mdates.HourLocator()
        daylocator = mdates.DayLocator()
        daysFmt = mdates.DateFormatter('%d')

                        date = r.date.astype('O')

                fig, ax = plt.subplots()
                ax.plot(date, r.adj_close)


                # format the ticks
                ax.xaxis.set_major_locator(years)
                ax.xaxis.set_major_formatter(yearsFmt)
                ax.xaxis.set_minor_locator(months)

                datemin = datetime.date(date.min().year, 1, 1)
                datemax = datetime.date(date.max().year + 1, 1, 1)
                ax.set_xlim(datemin, datemax)


                # format the coords message box
                def price(x):
                        return '$%1.2f' % x
                    ax.format_xdata = mdates.DateFormatter('%Y-%m-%d')
                    ax.format_ydata = price
                    ax.grid(True)

                    # rotates and right aligns the x labels, and moves the bottom of the
                    # axes up to make room for them
                    fig.autofmt_xdate()

                    plt.show()
    finally:
        try:
            os.unlink(f2)
        except: pass
    
