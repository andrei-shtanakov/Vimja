#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ninja_ide.core import plugin


class Vimja(plugin.Plugin):
    def initialize(self):
        # Init your plugin
        self.editor_s = self.locator.get_service('editor')

    def finish(self):
        # Shutdown your plugin
        pass

    def get_preferences_widget(self):
        # Return a widget for customize your plugin
        pass
