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

#TODO: Remove as it is debug info
import logging
logging.basicConfig(filename='vimja.log', level=logging.DEBUG)
logger = logging.getLogger('vimja.log')
hdlr = logging.FileHandler('/tmp/vimja.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.WARNING)


class Vimja(plugin.Plugin):
    ''' A vim plugin for the Ninja-IDE.

    Gives Basic vim functionality such as the vim movements and standard commands.

    '''

    # ==============================================================================
    # PRIVATE HELPERS
    # ==============================================================================

    def getPos(self):
        ''' Get the line and column number of the cursor.

        @ret tuple(line, col): A two element tuple containing the line and column numbers

        '''
        line = self.editor.textCursor().blockNumber()
        col = self.editor.textCursor().columnNumber()

        return (line, col)

    def getKeyMap(self, path):
        ''' Gets the key map from the given json file

        @arg filePath(path): Path to keyMap.json

        '''

        return self.convertCollection(json_manager.read_json(path))

    #TODO: Clean this logic to remove multiple returns and have only getattr call
    def convertCollection(self, data):
        ''' Converts a collection recursively, turning all unicode strings into
        either strings, ints or attributes of the Vimja class.

        @arg data: A variable who's contents are to be converted from unicode

        @ret data: The initial variable except the contents have now been changed from
            unicode to any of the above mentioned types.

        '''

        #If the data is a string (including unicode)
        if isinstance(data, basestring):
            #If data is an attribute of Vimja return it as such
            if getattr(self, data, False) is not False:
                return getattr(self, data, False)

            #If the data is a number return it as such
            if self.isNum(data):
                return float(data)

            #Else return it as a standard string
            else:
                return str(data)

        #If we have a dictionary
        elif isinstance(data, Mapping):
            #Iterate through the items of said dictionary
            return dict(map(self.convertCollection, data.iteritems()))

        #If we have an iterable
        elif isinstance(data, Iterable):
            #Iterate through all of items in the iterable
            return type(data)(map(self.convertCollection, data))

        else:
            return data

    def isNum(self, string):
        ''' Checks to see if a given string is a valid number.

        @arg str(string): A string to be checked as a potential number

        @ret bool(isNum): True if the string is a number, False otherwise.
            Accepts strings of the format: [+-]\d*(\.){1}\d*

        '''

        isNum = True
        for c in string:
            isNum &= c.isdigit() or c == '.' or c == '-' or c == '+'

        return isNum

    #TODO: Don't flip flop between integer and string
    def appendDelimitedStr(self, newVal, string, resetVal, delimiter):
        if newVal == resetVal or string == '':
            string = newVal
        else:
            string = '{0}{1}{2}'.format(string, delimiter, newVal)

        logger.warning('string: {0}'.format(string))
        return string

# ==============================================================================
# PLUGIN INIT
# ==============================================================================

    def initialize(self):
        ''' Creates constants for the different vim modes and sets the default mode.
        It also sets the editor's keyPressEvent handler to Vimja's interceptor

        '''

        #vim command mode
        self.NORMAL_MODE = 0

        #text editor mode
        self.INSERT_MODE = 1

        #cut text mode
        self.DELETE_MODE = 2

        #copy text mode
        self.YANK_MODE = 3

        #TODO: Get rid of "custom" constants, solution along the same lines as changing
            #the indices of the keyMap from hard code to Qt values
        self.MOVE_ANCHOR = QTextCursor.MoveAnchor

        self.KEEP_ANCHOR = QTextCursor.KeepAnchor

        #set the default mode to normal mode
        self.mode = self.INSERT_MODE

        #set the default cursor movement to MoveAnchor as opposed to KeepAnchor
        #as when the IDE is in DELETE_MODE
        self.defaultCursorMoveType = self.MOVE_ANCHOR

        #get the key map
        self.keyMap = self.getKeyMap(os.path.join(self._path, 'keyMap.json'))
        logger.warning('keyMap: {}'.format(self.keyMap))

        #buffer used to hold all of the key presses between valid commands or until
        #the escape key is pressed
        self.keyPressBuffer = ''

        #get the editor service
        self.editorService = self.locator.get_service('editor')

        #get the actual editor
        self.editor = self.editorService.get_editor()

        #set the editor's key press event handler to the interceptor
        self.editor.keyPressEvent = self.getKeyEventInterceptor(self.editor.keyPressEvent)

# ==============================================================================
# EVENT HANDLING
# ==============================================================================

    #TODO: Remove determineEventHandler, make one function. The issue is that
        #said function needs to accept one argument but still needs access to the rest
        #of the Vimja class
    #TODO: Generalize interceptor to take in various events
    def getKeyEventInterceptor(self, function):
        ''' Returns a key event interceptor that determines how to handle
        said events depending on whether or not the user is in normal mode or
        insert mode

        @arg function: The default event handler.

        @ret func(intercepKeyEvent): A key event interceptor, decides what to do with
            each key press.

        '''

        def interceptKeyEvent(event):
            ''' Intercepts all key press events and determines how to handle
            said events depending on whether or not the user is in normal mode or
            insert mode

            '''

            #If the key was the escape key or the user is in normal mode take over the
            #event handling
            #TODO: Add in a check for user defined key binding exceptions
            if event.key() == Qt.Key_Escape or self.mode != self.INSERT_MODE:
                self.keyEventMapper(event)

                return

            #Otherwise allow the editor to handle said event in the default manner
            return function(event)
        return interceptKeyEvent

    def keyEventMapper(self, event):
        ''' Takes in the key event and determines what function should be called
        in order to handle said event.

        @arg event: KeyPressEvent that is used to determine the appropriate handler

        @ret success: Returns the exit status of the event handler (True or False) or
            it returns None if no handler was found

        '''

        key = event.key()
        self.keyPressBuffer = self.appendDelimitedStr(key, self.keyPressBuffer,
            Qt.Key_Escape, ',')

        customKeyEvent = (self.keyMap.get(self.keyPressBuffer, False), key)

        if customKeyEvent[0] and callable(customKeyEvent[0]['Function']):
            success = customKeyEvent[0]['Function'](customKeyEvent)
            self.keyPressBuffer = ''

        else:
            success = None

        return success

# ==============================================================================
# CUSTOM EVENT HANDLERS
# ==============================================================================

    #TODO: Remove the residual cursor size that occurs when changing from insert
        #to command mode
    def switchMode(self, event):
        ''' Changes the mode of the editor

        @arg event: tuple containing a mode dictionary created from the keyPressEvent and
            it's corresponding keyMap json object

        @ret success: returns True

        '''

        self.mode = event[0]['Mode']
        self.defaultCursorMoveType = event[0]['Anchor']
        self.editor.setCursorWidth(event[0]['CursorWidth'])

        return True

    def move(self, event):
        ''' Moves the cursor

        @arg event: tuple containing a movement dictionary created from the keyPressEvent
            and it's corresponding keyMap json object

        @ret success: True if the cursor was successfully moved

        '''

        success = True

        moveOperation = getattr(QTextCursor, event[0]['MoveOperation'], False)
        if moveOperation is not False:
            cursor = self.editor.textCursor()
            cursor.movePosition(moveOperation, self.defaultCursorMoveType, event[0]['N'])
            self.editor.setTextCursor(cursor)

        else:
            success = False

        return success

    def deleteChars(self, event):
        cursor = self.editorService.get_actual_tab().textCursor()
        cursor.beginEditBlock()

        event[0]['Selection'](cursor)

        self.editor.setTextCursor(cursor)
        self.editor.cut()

        cursor.endEditBlock()

    def selectLine(self, cursor):
        cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor, 1)
        cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor, 1)
        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 1)

    def selectChar(self, cursor):
        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 1)

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

# ==============================================================================
# INSERT INTO EDITOR
# ==============================================================================
#tab = self.editorService.get_actual_tab()
#cursor = tab.textCursor()
#cursor.beginEditBlock()

#cursor.insertText('hi')
#cursor.endEditBlock()

# ==============================================================================
# LOGGER
# ==============================================================================
#logger.warning('direction: {}'.format(direction))
#logger.warning('curPos1: {}'.format(self.getPos()))

#cursor = self.editor.textCursor()
#cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor, 1)
#cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor, 1)
#e = self._main.get_actual_editor()
#e.cut()
#return True

# ==============================================================================
# DELETE A LINE
# ==============================================================================
#cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor, 1)
#cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor, 1)
#cursor.removeSelectedText()
#cursor.deleteChar()
