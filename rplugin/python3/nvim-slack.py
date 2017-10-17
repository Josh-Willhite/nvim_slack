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
        return [b for b in nvim.buffers if b.name == buffer_name][0]

    @neovim.command("SlackChannels")
    def slack_channels(self):
        nvim.command('new /tmp/slack_channels')
        nvim.command('view')
        buff = self._get_buffer('/tmp/slack_channels')

        channels = self.sc.api_call("channels.list")['channels']
        channels = [ch['name'] for ch in channels]
        for channel in channels:
            buff.append(channel)
