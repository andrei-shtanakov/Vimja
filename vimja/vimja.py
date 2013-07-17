#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ninja_ide.core import plugin
from PyQt4 import QtCore
from PyQt4.QtCore import Qt, QEvent
from functools import wraps
from PyQt4.QtGui import QTextCursor


class CEvent(QEvent):

    def __init__(self):
        super(CEvent, self).__init__()

    def keyPressEvent(e):
        for i in range(10):
            pass


class Vimja(plugin.Plugin):

    def interpretKeyBindings(self, function):
        @wraps(function)
        def _inner(event):
            return function(event)
            if True:
                if True:
                    event.ignore()
                    return
            return function(event)
        return _inner
        #tab = self.editor_s.get_actual_tab()
        #cursor = tab.textCursor()
        #cursor.beginEditBlock()

        #cursor.insertText('hi')
        #cursor.endEditBlock()
        pass

    def initialize(self):
        # Init your plugin
        self.__NORMAL_MODE = 0
        self.__INSERT_MODE = 1

        self.mode = self.__NORMAL_MODE

        self.editor_s = self.locator.get_service('editor')

        editor = self.editor_s.get_editor()
        editor.keyPressEvent = self.interpretKeyBindings(editor.keyPressEvent)

    def finish(self):
        # Shutdown your plugin
        pass

    def get_preferences_widget(self):
        # Return a widget for customize your plugin
        pass
