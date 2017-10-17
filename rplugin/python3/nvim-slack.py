import json
import os

import neovim
from slackclient import SlackClient

@neovim.plugin
class NeoSlack(object):
    def __init__(self, nvim):
        self.nvim = nvim
        self.sc = SlackClient(os.environ['SLACK_TOKEN'])

    def _get_buffer(self, buffer_name):
        return [b for b in self.nvim.buffers if b.name == buffer_name][0]

    @neovim.command("SlackChannels")
    def slack_channels(self):
        buff_name = '/tmp/slack_channels'
        self.nvim.command('new {}'.format(buff_name))
        self.nvim.command('view')
        buff = self._get_buffer(buff_name)
        channels = self.sc.api_call("channels.list")['channels']
        for channel in channels:
            for line in json.dumps(channel, indent=2):
                buff.append(line)
