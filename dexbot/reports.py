from dexbot.storage import Storage
import re
import datetime
import smtplib
import getpass
import socket
import io
import time
import logging
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import COMMASPACE, formatdate

log = logging.getLogger(__name__)

EMAIL_DEFAULT = {'server': '127.0.0.1', 'port': 25, 'subject': 'DEXBot Report'}

signalled = False

INTRO = """
<html>
  <head>
    <style>
       tr.debug {
         color: gray;
         background_color: white;
       }
       tr.warn {
         color: black;
         background-color: lightsalmon;
       }
       tr.critical {
         font-weight: bold;
         background-color: orangered;
         color: black;
       }
       table#log {
          font-size: smaller;
       } 
    </style>
  </head>
  <body>"""


LOGLEVELS = {0:'debug', 1:'info', 2:'warn', 3:'critical'}

try:
    # on platofrms that can do it, listen for SIGUSR2 for sending reports
    def set_signal(sig, frame):
        global signalled
        signalled = True
    import signal
    signal.signal(signal.SIGUSR2, set_signal)
except BaseException:
    # pass
    raise


class Reporter(Storage):

    def __init__(self, config, bots):
        self.bots = bots
        self.config = config
        Storage.__init__(self, "reporter")
        if not "lastrun" in self:
            self['lastrun'] = self.lastrun = time.time()
        else:
            self.lastrun = self['lastrun']

    def ontick(self):
        global signalled
        now = time.time()
        # because we are consulting lastrun every tick, we keep a RAM copy
        # as well as one serialised via storage.Storage
        if now - self.lastrun > 24 * 60 * 60 * self.config['days']:
            try:
                self.run_report(datetime.datetime.fromtimestamp(self.lastrun))
            finally:
                self['lastrun'] = self.lastrun = now
        if signalled:
            try:
                # report for the last week
                self.run_report(datetime.datetime.fromtimestamp(
                    now - 7 * 24 * 60 * 60))  
            finally:
                signalled = False

    def run_report(self, start):
        msg = io.StringIO()
        files = []
        msg.write(INTRO)
        for botname, bot in self.bots.items():
            msg.write("<h1>Bot {}</h1>\n".format(botname))
            msg.write('<h2>Settings</h2><table id="bot">')
            for key, value in bot.bot.items():
                msg.write("<tr><td>{}</td><td>{}</tr>".format(key, value))
            msg.write("</table><h2>Graph</h2>")
            fname = bot.graph(start=start)
            msg.write("<p><img src=\"cid:{}\"></p>".format(basename(fname)))
            files.append(fname)
            msg.write('<h2>Log</h2><table id="log">')
            logs = bot.query_log(start=start)
            for entry in logs:
                msg.write('<tr class="{}"><td>{}</td><td>{}</td></tr>'.format(
                    LOGLEVELS[entry.severity],
                    entry.stamp,
                    entry.message))
        msg.write("</table></body></html>")
        self.send_mail(msg.getvalue(), files)

    def send_mail(self, text, files=None):
        nc = EMAIL_DEFAULT.copy()
        nc.update(self.config)
        self.config = nc
        msg = MIMEMultipart('related')
        if not "send_from" in self.config:
            self.config['send_from'] = getpass.getuser() + "@" + \
                socket.gethostname()
        msg['From'] = self.config['send_from']
        msg['To'] = self.config.get('send_to', self.config['send_from'])
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = self.config['subject']

        msg.attach(MIMEText(text, "html"))

        for f in files or []:
            with open(f, "rb") as fd:
                part = MIMEImage(
                    fd.read(),
                    name=basename(f)
                )
            # After the file is closed
            part['Content-Disposition'] = 'inline; filename="%s"' % basename(
                f)
            part['Content-ID'] = '<{}>'.format(basename(f))
            msg.attach(part)

        smtp = smtplib.SMTP(self.config['server'], port=self.config['port'])
        if "user" in self.config:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(self.config['user'], self.config['password'])
        smtp.send_message(msg)
        smtp.close()
