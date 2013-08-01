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

    def isNum(self, str):
        ''' Checks to see if a given string is a valid number.

        @arg str(str): A string to be checked as a potential number

        @ret bool(isNum): True if the string is a number, False otherwise.
            Accepts strings of the format: [+-]\d*(\.){1}\d*

        '''

        isNum = True
        for c in str:
            isNum &= c.isdigit() or c == '.' or c == '-' or c == '+'

        return isNum

    def appendDelimitedStr(self, newVal, string, resetVal, delimiter):
        logger.warning('newVal: {0}; string{1}; resetVal: {2}; delimiter: {3}'.format(
            newVal, string, resetVal, delimiter))

        if newVal == resetVal or string == '':
            logger.warning('in if')
            string = newVal
        else:
            logger.warning('in else')
            string += '{0} {1}'.format(delimiter, newVal)

        logger.warning('string: {}'.format(string))
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

        #set the default mode to normal mode
        self.mode = self.INSERT_MODE

        #get the key map
        self.keyMap = self.getKeyMap(os.path.join(self._path, 'keyMap.json'))

        self.keyPressHist = ''

        self.editorService = self.locator.get_service('editor')

        self.editor = self.editorService.get_editor()

        #set the editor's key press event handler to the interceptor
        self.editor.keyPressEvent = self.getKeyEventInterceptor(self.editor.keyPressEvent)

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
            #TODO: Add in a check for user defined key bindings
            if event.key() == Qt.Key_Escape or self.mode == self.NORMAL_MODE:
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
        self.keyPressHist = self.appendDelimitedStr(key, self.keyPressHist,
            Qt.Key_Escape, ',')

        logger.warning('keyPressHist: {}'.format(self.keyPressHist))
        customKeyEvent = (key, self.keyMap.get(key, False))

        if customKeyEvent[1] and callable(customKeyEvent[1]['Function']):
            success = customKeyEvent[1]['Function'](customKeyEvent)

        else:
            success = None

        return success

# ==============================================================================
# CUSTOM EVENT HANDLERS
# ==============================================================================

    #TODO: Implement the buffer clearing functionality of Escape
    #TODO: Remove the residual cursor size that occurs when changing from insert
        #to command mode
    def switchMode(self, event):
        ''' Changes the mode of the editor

        @arg event: tuple containing a mode dictionary created from the keyPressEvent and
            it's corresponding keyMap json object

        @ret success: returns True
        '''

        self.mode = event[1]['Mode']
        self.editor.setCursorWidth(event[1]['CursorWidth'])

        return True

    #TODO: Change the jump to head of document from S to gg to meet vim defaults
    #TODO: Change the jump to bottom to be G as opposed to non-case sensitive
    def move(self, event):
        ''' Moves the cursor

        @arg event: tuple containing a movement dictionary created from the keyPressEvent
            and it's corresponding keyMap json object

        @ret success: True if the cursor was successfully moved

        '''

        success = True

        moveOperation = getattr(QTextCursor, event[1]['MoveOperation'], False)
        if moveOperation is not False:
            cursor = self.editor.textCursor()
            cursor.movePosition(moveOperation, QTextCursor.MoveAnchor, event[1]['N'])
            self.editor.setTextCursor(cursor)

        else:
            success = False

        return success

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

#self.editor.set_cursor_position(self.editor.get_cursor_position() +
    #event[1]['Direction']['Right'])

#pos = self.getPos()
#if event[1]['Direction']['Up'] != 0:
    #self.editor.go_to_line(int(pos[0] + event[1]['Direction']['Up']))
    #curPos = self.getPos()

    #while (curPos[1]) <= pos[1] and curPos[0] < pos[0]:
        #self.editor.set_cursor_position(self.editor.get_cursor_position() + 1)
        #curPos = self.getPos()
        #pass

    #self.editor.set_cursor_position(self.editor.get_cursor_position() - 1)

#self.emit(SIGNAL("cursorPositionChange(int, int)"), 109, 15)
    #self.textCursor().blockNumber() + 1,
    #self.textCursor().columnNumber())

#cursor.insertText('\n{}\n'.format(cursor.position()))
#cursor.setPosition(cursor.position())
#cursor.insertText('\n{}\n'.format(cursor.position()))
#cursor.insertText('done: {}'.format(x))

##Return value
#success = True

##Extract the direction mapping
#direction = event[1]['Direction']

##Get the current line column values
#curPos = self.getPos()

##Calculate the desired line column values
#newPos = (curPos[0] + direction['Up'], curPos[1] + direction['Right'])

##Determine the direction the cursor must move; it must be incremented to move
##down or right and decremented for up or left.
##The values Up and Right for now will only be 1, 0 or -1 and only one of them
##will be non-zero at a time thus giving cursorPosDiff a value of either 1 or -1
#cursorPosDiff = direction['Up'] + direction['Right']

##If we need to move down or right
#if cursorPosDiff > 0:
    ##Continue incrementing the cursor position while the line or the column is
    ##less than their desired values
    #while curPos[0] < newPos[0] or curPos[1] < newPos[1]:
        #self.editor.set_cursor_position(self.editor.get_cursor_position() + 1)
        #curPos = self.getPos()

##If we need to move up or left
#elif cursorPosDiff < 0:
    ##Continue decrementing the cursor position while the line or column is greater
    ##than their desired values
    #while curPos[0] > newPos[0] or curPos[1] > newPos[1]:
        #self.editor.set_cursor_position(self.editor.get_cursor_position() - 1)
        #curPos = self.getPos()

##If we don't need to move then the json has an error
#else:
    #success = False

#return success

#logger.warning('direction: {}'.format(direction))
#logger.warning('curPos1: {}'.format(self.getPos()))

#cursor = self.editor.textCursor()
#cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor, 1)
#cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor, 1)
#e = self._main.get_actual_editor()
#e.cut()
#return True
