#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import Iterable
from collections import Mapping

from ninja_ide.core import plugin
from ninja_ide.tools import json_manager

from PyQt4 import QtCore
from PyQt4.QtCore import Qt, QEvent
from PyQt4.QtGui import QTextCursor


class Vimja(plugin.Plugin):
    ''' A vim plugin for the Ninja-IDE.

    Gives Basic vim functionality such as the vim movements and standard commands.

    '''

    def keyEventMapper(self, event):
        key = event.key()

        tab = self.editor_s.get_actual_tab()
        cursor = tab.textCursor()
        cursor.beginEditBlock()
        cursor.insertText('\n{}\n\n'.format(self.keyMap))
        if key in self.keyMap:
            cursor.insertText('\nkey: {0} | event: {1}\n'.format(
                key, self.keyMap[key]))
        else:
            cursor.insertText('\nUnknown key\n')

        if key == Qt.Key_Escape:
            self.mode = self.__NORMAL_MODE
            cursor.insertText('\nnow in normal mode\n')

        elif key == Qt.Key_I:
            self.mode = self.__INSERT_MODE
            cursor.insertText('\nnow in insert mode\n')

        cursor.endEditBlock()

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

    def initialize(self):
        ''' Creates constants for the different vim modes and sets the default mode.
        It also sets the editor's keyPressEvent handler to Vimja's interceptor

        '''

        #vim command mode
        self.__NORMAL_MODE = 0

        #text editor mode
        self.__INSERT_MODE = 1

        #set the default mode to normal mode
        self.mode = self.__NORMAL_MODE

        #TODO: remove hardcoded path
        self.keyMap = self.__getKeyMap(
            '/home/richard/.BashScripts/python/Projects/Vimja/vimja/keyMaps.json')

        self.editor_s = self.locator.get_service('editor')

        editor = self.editor_s.get_editor()

        #set the editor's key press event handler to the interceptor
        editor.keyPressEvent = self.getKeyEventInterceptor(editor.keyPressEvent)

    def finish(self):
        # Shutdown your plugin
        pass

    def get_preferences_widget(self):
        # Return a widget for customize your plugin
        pass

    def __getKeyMap(self, path):
        ''' Gets the key map from the given json file '''

        return self.__convertCollection(json_manager.read_json(path))

    def __convertCollection(self, data):
        ''' Converts a collection recursively, turning all unicode strings into
        either strings or ints

        '''

        #If the data is a string (including unicode)
        #This is the first check because strings are iterables
        if isinstance(data, basestring):
            #If the data is a number return it as such
            if data.isdigit():
                return int(data)

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
# Dev Example Code
# ==============================================================================

#tab = self.editor_s.get_actual_tab()
#cursor = tab.textCursor()
#cursor.beginEditBlock()

#cursor.insertText('hi')
#cursor.endEditBlock()


#tab = self.editor_s.get_actual_tab()
#cursor = tab.textCursor()
#cursor.beginEditBlock()

#cursor.insertText('hi')
#cursor.endEditBlock()