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

def ltf(msg):
    with open('/tmp/ltf.log', 'a') as f:
        f.write('{}: {}'.format(datetime.now(), msg + '\n'))

@neovim.plugin
class NeoSlack(object):
    def __init__(self, nvim):
        logging.info('initializing class')
        self.nvim = nvim
        self.sc = SlackClient(os.environ['SLACK_TOKEN'])
        self.channels = self.sc.api_call("channels.list")['channels']
        self.users = self.sc.api_call("users.list")["members"]
        self.channel_buffers = {}

    def get_buffer(self, buffer_name):
        return [b for b in self.nvim.buffers if b.name == buffer_name][0]

    def get_channel_name(self, channel_id):
        logging.info('getting channels')
        return [ch['name'] for ch in self.channels if ch['id'] == channel_id][0]

    def get_channel_id(self, channel_name):
        ltf('getting channel: {}'.format(channel_name))
        return [ch['id'] for ch in self.channels if ch['name'] == channel_name][0]

    def get_user_name(self, user_id):
        logging.info('getting users')
        return [us['name'] for us in self.users if us['id'] == user_id][0]

    def create_channel_buffers(self):
        ltf('Creating buffers')
        for channel in self.channels:
            ltf('Creating buffer for {}'.format(channel))
            channel = self.get_channel_name(channel['id'])
            buff_name = '/tmp/slack_{}'.format(channel)
            self.nvim.command('new {}'.format(buff_name))
            self.nvim.command('view')
            self.channel_buffers[channel] = self.get_buffer(buff_name)
            ltf('Created {} buffer.'.format(channel))

    def write_event_to_buffer(self, event):
        ts = datetime.fromtimestamp(float(event['ts']))
        ts_out = datetime.strftime(ts, '%H:%M:%S')
        channel = self.get_channel_name(event['channel'])
        msg = '{} [{}]({}): {}'.format(
                ts_out,
                channel,
                self.get_user_name(event['user']),
                event['text']
            )
        ltf('{}: writing {} to {}'.format(datetime.now(), msg, channel))
        self.channel_buffers[channel].append(msg)

    @neovim.command("SlackStream")
    def process_slack_stream(self):
        ltf('{}: processing stream'.format(datetime.now()))
        self.create_channel_buffers()
        if self.sc.rtm_connect():
            while True:
                for event in self.sc.rtm_read():
                    if event['type'] in ['message']:
                        self.write_event_to_buffer(event)
                sleep(0.5)

    def get_summary(self):
        users = {u['id']:u['real_name'] for u in self.users}
        return  {
            channel['name']: {'members':[users[m] for m in channel['members']]}
            for channel in self.channels
        }

    @neovim.command("SlackSummary")
    def slack_summary(self):
        ltf('SUMMARY')
        buff_name = '/tmp/slack_channels'
        self.nvim.command('new {}'.format(buff_name))
        self.nvim.command('view')
        buff = self.get_buffer(buff_name)
        for line in json.dumps(self.get_summary(), indent=2).split('\n'):
            buff.append(line)

