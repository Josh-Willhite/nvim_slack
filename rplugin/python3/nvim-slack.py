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

    def get_channel_id(self, channel_name):
        return [ch['id'] for ch in self.channels if ch['name'] == channel_name][0]

    def get_user_name(self, user_id):
        logging.info('getting users')
        return [us['name'] for us in self.users if us['id'] == user_id][0]

    def process_slack_stream(self):
        if self.sc.rtm_connect():
            if not os.path.isfile(SLACK_EVENTS):
                with open(SLACK_EVENTS, 'w') as slack_file:
                    slack_file.write('')
            while True:
                events = self.sc.rtm_read()
                if events:
                    with open(SLACK_EVENTS, 'a') as slack_file:
                        for event in events:
                            if event['type'] in ['message']:
                                json.dump(event, slack_file)
                                slack_file.write('\n')
                sleep(0.5)

    @neovim.command("SlackStream")
    def start_stream_thread(self):
        t = threading.Thread(target=self.process_slack_stream)
        t.daemon = True
        t.start()

    def stream_channel_thread(self, channel, buff):
        most_recent_ts = datetime.now() - timedelta(minutes=30)
        while True:
            with open(SLACK_EVENTS, 'r') as slack_file:
                events = slack_file.readlines()
            for event in events:
                event = json.loads(event)
                ts = datetime.fromtimestamp(float(event['ts']))
                ts_out = datetime.strftime(ts, '%H:%M:%S')
                if event['channel'] == channel and ts > most_recent_ts:
                    buff.append(
                        '{} [{}]({}): {}\n'.format(
                            ts_out,
                            self.get_channel_name(event['channel']),
                            self.get_user_name(event['user']),
                            event['text']
                        )
                    )
                    most_recent_ts = ts
            sleep(0.25)

    @neovim.command("SlackChannel", channel='')
    def start_channel_thread(self, channel):
        buff_name = '/tmp/slack_{}'.format(channel)
        self.nvim.command('new {}'.format(buff_name))
        self.nvim.command('view')
        buff = self.get_buffer(buff_name)
        channel_id = self.get_channel_id(channel)
        t = threading.Thread(target=self.stream_channel_thread, args=(channel_id, buff,))
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

