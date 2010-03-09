import buttifier
import irclib
import random
import time
import re
import fnmatch
import yaml

class ignore_list(list):
    _regex_mode = re.compile(r"^/(.*)/(i?)$")
    _glob_mode = re.compile(r"[\*\?\[\]]")

    def __init__(self, enemies):
        for i in enemies:
            m = self._regex_mode.search(i)
            if m:
                if len(m.group(2)) == 0:
                    self.append(re.compile(m.group(1)))
                else:
                    self.append(re.compile(m.group(1), re.I))
                continue
            elif self._glob_mode.search(i):
                self.append(re.compile( fnmatch.translate(i) ))
            else:
                self.append(i)

    def __contains__(self, name):
        for i in self:
            if isinstance(i, str):
                if i == name: return True
            elif i.search(name):
                return True
        return False



class buttbot(irclib.SimpleIRCClient):
    def __init__(self, config_file="config"):
        irclib.SimpleIRCClient.__init__(self)
        f = open(config_file)
        config = yaml.load(f)
        f.close()

        self.connect(config['server'], config['port'], config['nick'])
        self.default_channels = config['channels']
        self.command = config['command']
        try:
            self.channels_left = config['max_channels']
        except:
            self.channels_left = 5

        self.enemies = ignore_list(config['enemies'])

        self.last_butt = 0.0 # the epoch

    def on_welcome(self, connection, event):
        for channel in self.default_channels:
            connection.join(channel)

    def on_pubmsg(self, connection, event):
        msg = event.arguments()[0]
        user = event.source().split('!')[0]
        channel = event.target()

        if user in self.enemies: return

        bits = msg.split(' ', 1)
        if bits[0] == self.command:
            if len(msg) > 1:
                try:
                    connection.privmsg(channel, user+": "+
                                       buttifier.buttify(bits[1], 
                                                         allow_single=True))
                except:
                    connection.action(channel, "can't butt the unbuttable!")
        else:
            now = time.time()
            if now - self.last_butt > 15 and random.random() < 0.05:
                try:
                    connection.privmsg(channel, buttifier.buttify(msg))
                    self.last_butt = now
                except:
                    pass

    def on_invite(self, connection, event):
        if self.channels_left > 0:
            connection.join(event.arguments()[0])
            self.channels_left -= 1

if __name__ == "__main__":
    buttbot().start()
