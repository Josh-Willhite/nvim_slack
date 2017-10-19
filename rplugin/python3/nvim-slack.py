from datetime import datetime
import logging
import json
import os
import threading
from time import sleep

import neovim
from slackclient import SlackClient

SLACK_LOG = '/tmp/slack.log'
logging.basicConfig(filename='/tmp/slack-plugin.log',level=logging.DEBUG)

@neovim.plugin
class NeoSlack(object):
    def __init__(self, nvim):
        logging.info('initializing class')
        self.nvim = nvim
        self.sc = SlackClient(os.environ['SLACK_TOKEN'])
        self.channels = self.sc.api_call("channels.list")['channels']
        self.users = self.sc.api_call("users.list")["members"]

    def get_buffer(self, buffer_name):
        return [b for b in self.nvim.buffers if b.name == buffer_name][0]

    def get_channel_name(self, channel_id):
        logging.info('getting channels')
        return [ch['name'] for ch in self.channels if ch['id'] == channel_id][0]

    def get_user_name(self, user_id):
        logging.info('getting users')
        return [us['name'] for us in self.users if us['id'] == user_id][0]

    def process_slack_stream(self):
        if self.sc.rtm_connect():
            while True:
                logging.info('processing stream')
                events = self.sc.rtm_read()
                if events:
                    logging.info('processing events')
                    with open(SLACK_LOG, 'w') as slack_file:
                        slack_events = json.load(slack_file)
                        slack_events += events
                        json.dump(slack_events, slack_file, indent=2)
                sleep(1)

    @neovim.command("SlackStream")
    def start_stream_thread(self):
        t = threading.Thread(target=self.process_slack_stream)
        t.daemon = True
        t.start()

    def get_summary(self):
        users = {u['id']:u['real_name'] for u in self.users}
        return  {
            channel['name']: {'members':[users[m] for m in channel['members']]}
            for channel in self.channels
        }

    @neovim.command("SlackSummary")
    def slack_summary(self):
        buff_name = '/tmp/slack_channels'
        self.nvim.command('new {}'.format(buff_name))
        self.nvim.command('view')
        buff = self.get_buffer(buff_name)
        for line in json.dumps(self.get_summary(), indent=2).split('\n'):
            buff.append(line)

