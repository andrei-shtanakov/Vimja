#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ninja_ide.core import plugin
from PyQt4 import QtCore
from PyQt4.QtCore import Qt, QEvent
from PyQt4.QtGui import QTextCursor


class Vimja(plugin.Plugin):
    ''' A vim plugin for the Ninja-IDE.

    Gives Basic vim functionality such as the vim movements and standard commands

    '''

    def interpretKeyEvent(self, event):
        tab = self.editor_s.get_actual_tab()
        cursor = tab.textCursor()
        cursor.beginEditBlock()
        #cursor.insertText('\n{0} | {1} | {2}\n'.format(
            #event.key(), Qt.Key_I, event.key() == Qt.Key_I))

        if event.key() == Qt.Key_I:
            self.mode = self.__INSERT_MODE
            cursor.insertText('\nnow in insert mode\n')

        elif event.key() == Qt.Key_Escape:
            self.mode = self.__NORMAL_MODE
            cursor.insertText('\nnow in normal mode\n')

        cursor.endEditBlock()

    #TODO: Remove determineEventHandler, make one function. The issue is that
    #    said function needs to accept one argument but still needs access to the rest
    #    of the Vimja class
    #TODO: Generalize interceptor to take in various events
    def getKeyEventInterceptor(self, function):
        ''' Returns a key event interceptor '''

        def interceptKeyEvent(event):
            ''' Intercepts all key press events and determines how to handle
            said events depending on whether or not the user is in normal mode or
            insert mode

            '''

            #If the key was the escape key or the user is in normal mode take over the
            #event handling
            #TODO: Add in a check for user defined key bindings
            if event.key() == Qt.Key_Escape or self.mode == self.__NORMAL_MODE:
                self.interpretKeyEvent(event)

                return

            #Otherwise allow the editor to handle said event in the default manner
            return function(event)
        return interceptKeyEvent

    def initialize(self):
        ''' Creates constants for the different vim modes and sets the default mode
        to normal. It also sets the editor's keyPressEvent handler to Vimja's interceptor

        '''

        #vim command mode
        self.__NORMAL_MODE = 0

        #text editor mode
        self.__INSERT_MODE = 1

        #set the default mode to normal mode
        self.mode = self.__NORMAL_MODE

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