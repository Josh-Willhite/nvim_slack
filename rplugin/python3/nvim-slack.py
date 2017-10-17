import json
import os

import neovim
from slackclient import SlackClient

@neovim.plugin
class NeoSlack(object):
    def __init__(self, nvim):
        self.nvim = nvim
        self.sc = SlackClient(os.environ['SLACK_TOKEN'])

    @neovim.command("SlackChannels")
    def slack_channels(self):
        channels = self.sc.api_call("channels.list")['channels']
        channels = [ch['name'] for ch in channels]
        self.nvim.current.line = channels
