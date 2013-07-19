#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from collections import Iterable
from collections import Mapping

from ninja_ide.core import plugin
from ninja_ide.tools import json_manager

from PyQt4 import QtCore
from PyQt4.QtCore import Qt, QEvent
from PyQt4.QtGui import QTextCursor
from PyQt4.QtGui import QPlainTextEdit
from PyQt4.QtCore import SIGNAL


class Vimja(plugin.Plugin):
    ''' A vim plugin for the Ninja-IDE.

    Gives Basic vim functionality such as the vim movements and standard commands.

    '''

    # ==============================================================================
    # PRIVATE HELPERS
    # ==============================================================================

    def __isNum(self, str):
        ret = True
        for c in str:
            ret &= c.isdigit() or c == '.' or c == '-' or c == '+'

        return ret

    def __getKeyMap(self, path):
        ''' Gets the key map from the given json file '''

        return self.__convertCollection(json_manager.read_json(path))

    def __getPos(self):
        line = self.editor.textCursor().blockNumber()
        col = self.editor.textCursor().columnNumber()

        return (line, col)

    #TODO: Clean this logic to remove multiple returns and have only getattr call
    def __convertCollection(self, data):
        ''' Converts a collection recursively, turning all unicode strings into
        either strings or ints

        '''

        #If the data is a string (including unicode)
        if isinstance(data, basestring):
            #If data is an attribute of Vimja return it as such
            if getattr(self, data, False) is not False:
                return getattr(self, data, False)

            #If the data is a number return it as such
            if self.__isNum(data):
                return float(data)

            #Else return it as a standard string
            else:
                return str(data)

        #If we have a dictionary
        elif isinstance(data, Mapping):
            #Iterate through the items of said dictionary
            return dict(map(self.__convertCollection, data.iteritems()))

        #If we have an iterable
        elif isinstance(data, Iterable):
            #Iterate through all of items in the iterable
            return type(data)(map(self.__convertCollection, data))

        else:
            return data

# ==============================================================================
# PLUGIN INIT
# ==============================================================================

    def initialize(self):
        ''' Creates constants for the different vim modes and sets the default mode.
        It also sets the editor's keyPressEvent handler to Vimja's interceptor

        '''

        #vim command mode
        self.__NORMAL_MODE = 0

        #text editor mode
        self.__INSERT_MODE = 1

        #set the default mode to normal mode
        self.mode = self.__INSERT_MODE

        #get the key map
        self.keyMap = self.__getKeyMap(os.path.join(self._path, 'keyMap.json'))

        self.editorService = self.locator.get_service('editor')

        self.editor = self.editorService.get_editor()

        #set the editor's key press event handler to the interceptor
        self.editor.keyPressEvent = self.getKeyEventInterceptor(self.editor.keyPressEvent)

        #self.emit(SIGNAL("cursorPositionChange(int, int)"), 109, 15)
            #self.textCursor().blockNumber() + 1,
            #self.textCursor().columnNumber())

# ==============================================================================
# EVENT HANDLING
# ==============================================================================

    #TODO: Remove determineEventHandler, make one function. The issue is that
    #    said function needs to accept one argument but still needs access to the rest
    #    of the Vimja class
    #TODO: Generalize interceptor to take in various events
    def getKeyEventInterceptor(self, function):
        ''' Returns a key event interceptor that determines how to handle
        said events depending on whether or not the user is in normal mode or
        insert mode

        '''

        def interceptKeyEvent(event):
            ''' Intercepts all key press events and determines how to handle
            said events depending on whether or not the user is in normal mode or
            insert mode

            '''

            #If the key was the escape key or the user is in normal mode take over the
            #event handling
            #TODO: Add in a check for user defined key bindings
            if event.key() == Qt.Key_Escape or self.mode == self.__NORMAL_MODE:
                self.keyEventMapper(event)

                return

            #Otherwise allow the editor to handle said event in the default manner
            return function(event)
        return interceptKeyEvent

    def keyEventMapper(self, event):
        ''' Takes in the key event and determines what function should be called
        in order to handle said event.

        '''

        tab = self.editorService.get_actual_tab()
        cursor = tab.textCursor()
        cursor.beginEditBlock()

        #cursor.insertText('\nkeyMap: {}\n'.format(self.keyMap))
        #cursor.insertText('__dict__: {}\n'.format(self.__dict__))
        #cursor.insertText('\n{}\n'.format(self.editor.get_cursor_position()))

        key = event.key()
        customKeyEvent = (key, self.keyMap.get(key, False))

        #cursor.insertText('key: {}; event: {}\n'.format(*customKeyEvent))

        if customKeyEvent[1] and callable(customKeyEvent[1]['Function']):
            customKeyEvent[1]['Function'](customKeyEvent)

        cursor.endEditBlock()

# ==============================================================================
# CUSTOM EVENT HANDLERS
# ==============================================================================

    #TODO: Implement the buffer clearing functionality of Escape
    def switchMode(self, event):
        ''' Changes the mode of the editor '''

        self.mode = event[1]['Mode']
        self.editor.setCursorWidth(event[1]['CursorWidth'])

    def move(self, event):
        self.editor.set_cursor_position(self.editor.get_cursor_position() +
            event[1]['Direction']['Right'])

        pos = self.__getPos()
        if event[1]['Direction']['Up'] != 0:
            self.editor.go_to_line(int(pos[0] + event[1]['Direction']['Up']))
            curPos = self.__getPos()

            while (curPos[1]) <= pos[1] and curPos[0] < pos[0]:
                self.editor.set_cursor_position(self.editor.get_cursor_position() + 1)
                curPos = self.__getPos()
                pass

            self.editor.set_cursor_position(self.editor.get_cursor_position() - 1)

        pass
        #tab = self.editorService.get_actual_tab()
        #cursor = tab.textCursor()
        #cursor.beginEditBlock()

        #cursor.insertText(event[1]['Direction'])

        #cursor.endEditBlock()

# ==============================================================================
# USELESS
# ==============================================================================

    def finish(self):
        # Shutdown your plugin
        pass

    def get_preferences_widget(self):
        # Return a widget for customize your plugin
        pass


# ==============================================================================
# Dev Example Code
# ==============================================================================

#tab = self.editorService.get_actual_tab()
#cursor = tab.textCursor()
#cursor.beginEditBlock()

#cursor.insertText('hi')
#cursor.endEditBlock()
