"""
A module to provide an interactive text-based tool for dexbot configuration
The result is takemachine can be run without having to hand-edit config files.
If systemd is detected it will offer to install a user service unit (under ~/.local/share/systemd
This requires a per-user systemd process to be runnng

Requires the 'whiptail' tool: so UNIX-like sytems only

Note there is some common cross-UI configuration stuff: look in basestrategy.py
It's expected GUI/web interfaces will be re-implementing code in this file, but they should
understand the common code so bot strategy writers can define their configuration once
for each strategy class.

"""


import importlib
import os
import os.path
import sys
import collections
import re
import tempfile
import shutil
from dexbot.bot import STRATEGIES
from dexbot.whiptail import get_whiptail
from dexbot.find_node import start_pings, best_node

SYSTEMD_SERVICE_NAME = os.path.expanduser(
    "~/.local/share/systemd/user/dexbot.service")

SYSTEMD_SERVICE_FILE = """
[Unit]
Description=Dexbot

[Service]
Type=notify
WorkingDirectory={homedir}
ExecStart={exe} --systemd run
Environment=PYTHONUNBUFFERED=true
Environment=UNLOCK={passwd}

[Install]
WantedBy=default.target
"""


def select_choice(current, choices):
    """for the radiolist, get us a list with the current value selected"""
    return [(tag, text, (current == tag and "ON") or "OFF")
            for tag, text in choices]


def process_config_element(elem, d, config):
    """
    process an item of configuration metadata display a widget as appropriate
    d: the Dialog object
    config: the config dctionary for this bot
    """
    if elem.type == "string":
        txt = d.prompt(elem.description, config.get(elem.key, elem.default))
        if elem.extra:
            while not re.match(elem.extra, txt):
                d.alert("The value is not valid")
                txt = d.prompt(
                    elem.description, config.get(
                        elem.key, elem.default))
        config[elem.key] = txt
    if elem.type == "bool":
        config[elem.key] = d.confirm(elem.description)
    if elem.type in ("float", "int"):
        txt = d.prompt(
            elem.description, config.get(
                elem.key, str(
                    elem.default)))
        while True:
            try:
                if elem.type == "int":
                    val = int(txt)
                else:
                    val = float(txt)
                if val < elem.extra[0]:
                    d.alert("The value is too low")
                elif elem.extra[1] and val > elem.extra[1]:
                    d.alert("the value is too high")
                else:
                    break
            except ValueError:
                d.alert("Not a valid value")
            txt = d.prompt(
                elem.description, config.get(
                    elem.key, str(
                        elem.default)))
        config[elem.key] = val
    if elem.type == "choice":
        config[elem.key] = d.radiolist(elem.description, select_choice(
            config.get(elem.key, elem.default), elem.extra))


def setup_systemd(d, config):
    if config.get("systemd_status", "install") == "reject":
        return  # don't nag user if previously said no
    if not os.path.exists("/etc/systemd"):
        return  # no working systemd
    if os.path.exists(SYSTEMD_SERVICE_NAME):
        # dexbot already installed
        # so just tell cli.py to quietly restart the daemon
        config["systemd_status"] = "installed"
        return
    if d.confirm(
            "Do you want to install dexbot as a background (daemon) process?"):
        for i in ["~/.local", "~/.local/share",
                  "~/.local/share/systemd", "~/.local/share/systemd/user"]:
            j = os.path.expanduser(i)
            if not os.path.exists(j):
                os.mkdir(j)
        passwd = d.prompt(
            "The wallet password entered with uptick\nNOTE: this will be saved on disc so the bot can run unattended. This means anyone with access to this computer's file can spend all your money",
            password=True)
        # because we hold password be restrictive
        fd = os.open(SYSTEMD_SERVICE_NAME, os.O_WRONLY | os.O_CREAT, 0o600)
        with open(fd, "w") as fp:
            fp.write(
                SYSTEMD_SERVICE_FILE.format(
                    exe=sys.argv[0],
                    passwd=passwd,
                    homedir=os.path.expanduser("~")))
        # signal cli.py to set the unit up after writing config file
        config['systemd_status'] = 'install'
    else:
        config['systemd_status'] = 'reject'


def configure_bot(d, bot):
    strategy = bot.get('module', 'dexbot.strategies.echo')
    bot['module'] = d.radiolist(
        "Choose a bot strategy", select_choice(
            strategy, STRATEGIES))
    # its always Strategy now, for backwards compatibilty only
    bot['bot'] = 'Strategy'
    # import the bot class but we don't __init__ it here
    klass = getattr(
        importlib.import_module(bot["module"]),
        bot["bot"]
    )
    # use class metadata for per-bot configuration
    configs = klass.configure()
    if configs:
        for c in configs:
            process_config_element(c, d, bot)
    else:
        d.alert("This bot type does not have configuration information. You will have to check the bot code and add configuration values to config.yml if required")
    return bot

def setup_reporter(d, config):
    reporter_config = config.get('reports',{})
    frequency = d.radiolist("DEXBot can send an e-mail report on its activities at regular intervals", select_choice(
        str(reporter_config.get('days',0)),
        [("0",'Never'), ('1','Daily'), ('2','Second-daily'), ('3','Third-daily'), ('7','Weekly')]))
    if frequency == '0':
        if 'reporter' in config:
            del config['reporter']
        return
    reporter_config['days'] = int(frequency)
    reporter_config['send_to'] = d.prompt("E-mail address to send to",default=reporter_config.get('send_to',''))
    reporter_config['send_from'] = d.prompt("E-mail address to send from (blank will use local user and host name)",
                                            default=reporter_config.get('send_from',reporter_config['send_to']))
    reporter_config['server'] = d.prompt("SMTP server to use (blank means this server)",
                                         default=reporter_config.get('server',''))
    reporter_config['port'] = d.prompt("SMTP server port to use",
                                       default=reporter_config.get('port','25'))
    reporter_config['login'] = d.prompt("Login username for the SMTP server (blank means don't login)",
                                        default=reporter_config.get('login',
                                                                    reporter_config['send_to'].split('@')[0]))
    if reporter_config['login']:
        reporter_config['password'] = d.prompt("SMTP server password to use",password=True)
    config['reports'] = reporter_config

def configure_dexbot(config):
    d = get_whiptail()
    bots = config.get('bots', {})
    if len(bots) == 0:
        ping_results = start_pings()
        while True:
            txt = d.prompt("Your name for the bot")
            config['bots'] = {txt: configure_bot(d, {})}
            if not d.confirm("Set up another bot?\n(DEXBOt can run multiple bots in one instance)"):
                break
        setup_reporter(d, config)
        setup_systemd(d, config)
        node = best_node(ping_results)
        if node:
            config['node'] = node
        else:
            # search failed, ask the user
            config['node'] = d.prompt(
                "Search for best BitShares node failed.\n\nPlease enter wss:// url of chosen node.")
    else:
        action = d.menu("You have an existing configuration.\nSelect an action:",
                        [('NEW', 'Create a new bot'),
                         ('DEL', 'Delete a bot'),
                         ('EDIT', 'Edit a bot'),
                         ('CONF', 'Redo general config')])
        if action == 'EDIT':
            botname = d.menu("Select bot to edit", [(i, i) for i in bots])
            config['bots'][botname] = configure_bot(d, config['bots'][botname])
        elif action == 'DEL':
            botname = d.menu("Select bot to delete", [(i, i) for i in bots])
            del config['bots'][botname]
        if action == 'NEW':
            txt = d.prompt("Your name for the new bot")
            config['bots'][txt] = configure_bot(d, {})
        else:
            setup_reporter(d, config)
            config['node'] = d.prompt("BitShares node to use",default=config['node'])
    d.clear()
    return config


if __name__ == '__main__':
    print(repr(configure({})))
