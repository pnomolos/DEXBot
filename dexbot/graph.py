"""
A graph utility module
"""

from dexbot.storage import data_dir
from os.path import join
import os, tempfile
import numpy

import datetime, time
import matplotlib.pyplot as plt
import matplotlib.dates as mdates



def query_to_graph(self, plot, rows):
    """Translate SQLAlchemy rows result (from Journal) into arrays and graph them
    """
    by_dates = {}
    for i in rows:
        if not i.stamp in by_dates:
            by_dates[i.stamp] = {}
        by_dates[i.stamp][i.key] = i.amount
    dates = sorted(list(by_dates.keys()))
    all_keys = list(by_dates[dates[0]].keys())
    for k in all_keys:
        ydata = [by_dates[d][k] for d in dates]
        plot.plot(dates,ydata,label=k)
    plot.set_xlim(min(dates), max(dates))
        
def do_graph(rows):
    
    daylocator = mdates.DayLocator()
    daysFmt = mdates.DateFormatter('%b %d')
    
    fig, ax = plt.subplots()

    query_to_graph(ax, rows)
    # format the ticks
    ax.xaxis.set_major_locator(daylocator)
    ax.xaxis.set_major_formatter(daysFmt)
        
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
    
    fd, plotfile = tempfile.mkstemp(suffix='.png')
    os.close(fd)
    plt.savefig(plotfile,bbox_inches='tight')
    return plotfile
    
    
