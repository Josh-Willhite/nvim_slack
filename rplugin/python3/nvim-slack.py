import json
import os

import neovim
from slackclient import SlackClient


@neovim.plugin
class NeoSlack(object):
    def __init__(self, nvim):
        self.nvim = nvim
        self.sc = SlackClient(os.environ['SLACK_TOKEN'])
        self.summary =

    def _get_buffer(self, buffer_name):
        return [b for b in self.nvim.buffers if b.name == buffer_name][0]

    def get_summary(self):
        channels = self.sc.api_call("channels.list")['channels']
        users = self.sc.api_call("users.list")["members"]
        users = {u['id']:u['real_name'] for u in users}
        return = {
            channel['name']: {'members':[users[m] for m in channel['members']]}
            for channel in channels
        }

    @neovim.command("SlackChannels")
    def slack_channels(self):
        buff_name = '/tmp/slack_channels'
        self.nvim.command('new {}'.format(buff_name))
        self.nvim.command('view')
        buff = self._get_buffer(buff_name)
        for line in json.dumps(self.get_summar(), indent=2).split('\n'):
            buff.append(line)
