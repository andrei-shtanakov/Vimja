#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:

# ==============================================================================
# IMPORTS
# ==============================================================================

    import os
    from traceback import format_exc as stackTrace

    from collections import Iterable
    from collections import Mapping

    from ninja_ide.core import plugin
    from ninja_ide.tools import json_manager

    from PyQt4.QtCore import Qt
    from PyQt4.QtGui import QTextCursor

    import re

# ==============================================================================
# GLOBAL VARIABLES
# ==============================================================================

    LOG_FILE = 'vimja.log'
    PATH = os.path.dirname(__file__)

    import logging
    logger = logging.getLogger(LOG_FILE)
    hdlr = logging.FileHandler(os.path.join(PATH, '..', LOG_FILE))
    hdlr.setFormatter(logging.Formatter(
        '%(levelname)-8s %(asctime)s %(name)s:%(lineno)-4d %(message)s'))

    logger.addHandler(hdlr)
    logger.setLevel(logging.INFO)

except Exception as e:
    errMessage = ''

    try:
        if isinstance(e, ImportError) and stackTrace is not None:
            errMessage = 'Import Error: {}'.format(stackTrace())

        else:
            errMessage = 'Unknown Error during import process: {}'.format(stackTrace())

    finally:
        raise Exception(errMessage)


class Vimja(plugin.Plugin):
    ''' A vim plugin for the Ninja-IDE.

    Gives Basic vim functionality such as the vim movements and standard commands.

    '''

# ==============================================================================
# PRIVATE HELPERS
# ==============================================================================

    def addNewLine(self):
        ''' Inserts a new line below the current line

        @arg QTextCursor cursor cursor being used

        '''

        self.cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.MoveAnchor)
        self.cursor.insertBlock()

    def getPos(self):
        ''' Get the line and column number of the cursor.

        @ret tuple (line, col) A two element tuple containing the line and column numbers

        '''
        line = self.editor.textCursor().blockNumber()
        col = self.editor.textCursor().columnNumber()

        return (line, col)

    def getKeyMap(self, path):
        ''' Gets the key map from the given json file

        @arg filePath path Path to keyMap.json

        '''

        return self.convertCollection(json_manager.read_json(path))

    #TODO: Clean this logic to remove multiple returns and have only getattr call
    def convertCollection(self, data):
        ''' Converts a collection recursively, turning all unicode strings into
        either strings, ints or attributes of the Vimja class.

        @arg mixed data A variable who's contents are to be converted from unicode

        @ret mixed data The initial variable except the contents have now been changed
            from unicode to any of the above mentioned types.

        '''

        #If the data is a string (including unicode)
        if isinstance(data, basestring):
            #If data is an attribute of Vimja return it as such
            if getattr(self, data, False) is not False:
                return getattr(self, data, False)

            #If the data is a number return it as such
            if self.isNum(data):
                return float(data)

            #If the data is a boolean value return it as such
            elif data == 'True' or data == 'False':
                return True if data == 'True' else False

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

        @arg str string A string to be checked as a potential number

        @ret bool isNum True if the string is a number, False otherwise.
            Accepts strings of the format: [+-]\d*(\.){1}\d*

        '''

        isNum = True
        for c in string:
            isNum &= c.isdigit() or c == '.' or c == '-' or c == '+'

        return isNum

    #TODO: Don't flip flop between integer and string
    def appendDelimitedStr(self, newVal, string, resetVal, delimiter):
        ''' Adds the passed in value to the passed in string using the passed in
        delimiter and clears the string if the value is the reset value

        @arg mixed newVal value to be added
        @arg str string the string to be added to
        @arg mixed resetVal the value that is specified to reset the entire string
        @arg chr delimiter the char that delimits the string

        @ret string string the string after processing

        '''

        if newVal == resetVal or string == '':
            string = newVal
        else:
            string = '{0}{1}{2}'.format(string, delimiter, newVal)

        logger.info('string: {0}'.format(string))
        return string

# ==============================================================================
# PLUGIN INIT
# ==============================================================================

    def initialize(self):
        ''' Creates constants for the different vim modes and sets the default mode.
        It also sets the editor's keyPressEvent handler to Vimja's interceptor

        '''

        logger.info('initializing')

        #vim command mode
        self.NORMAL_MODE = 0

        #text editor mode
        self.INSERT_MODE = 1

        #cut text mode
        self.DELETE_MODE = 2

        #copy text mode
        self.YANK_MODE = 3

        self.copyPasteBuffer = {0: {'text': '', 'isLine': False}}

        self.isSearching = False

        self.regexString = ''

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
        self.keyMap = self.getKeyMap(os.path.join(PATH, 'keyMap.json'))
        logger.info('keyMap: {}'.format(self.keyMap))

        #buffer used to hold all of the key presses between valid commands or until
        #the escape key is pressed
        self.keyPressBuffer = ''

        #get the editor service
        self.editorService = self.locator.get_service('editor')

        #initialize the editor and cursor to None
        self.editor = None
        self.cursor = None

        #TODO: find a better way to intercept the events
        #hack to get around the fact that there is no editor when the plugin is being
        #initialized, this makes the first key press event connect the editor's event
        #handler to vimja
        self.editorService.editorKeyPressEvent.connect(self.connectKeyPressHandler)

# ==============================================================================
# EVENT HANDLING
# ==============================================================================

    def connectKeyPressHandler(self):
        ''' Connects Vimja's key event interceptor to the default key press events '''

        logger.info('connecting')

        #if there is no editor then we haven't captured the key events yet
        if self.editor is None:
            #get the actual editor
            self.editor = self.editorService.get_editor()

            #get the cursor
            self.cursor = self.editor.textCursor()

            #set the editor's key press event handler to the interceptor
            self.editor.keyPressEvent = self.getKeyEventInterceptor(
                self.editor.keyPressEvent)

    #TODO: Remove determineEventHandler, make one function. The issue is that
        #said function needs to accept one argument but still needs access to the rest
        #of the Vimja class
    #TODO: Generalize interceptor to take in various events
    def getKeyEventInterceptor(self, function):
        ''' Returns a key event interceptor that determines how to handle
        said events depending on whether or not the user is in normal mode or
        insert mode

        @arg func function The default event handler.

        @ret func intercepKeyEvent A key event interceptor, decides what to do with
            each key press.

        '''

        def interceptKeyEvent(event):
            ''' Intercepts all key press events and determines how to handle
            said events depending on whether or not the user is in normal mode or
            insert mode

            '''

            try:
                #If the key was the escape key or the user is in normal mode take over the
                #event handling
                #TODO: Add in a check for user defined key binding exceptions
                if event.key() == Qt.Key_Escape or self.mode != self.INSERT_MODE:
                    self.keyEventMapper(event.key())
                    return

                #elif self.mode == self.DELETE_MODE or self.mode == self.YANK_MODE or \
                    #event.key() == Qt.Key_X:

                    #self.bufferKeyEventMapper(event.key())
                    #return

            except Exception:
                logger.warning('There was an error in processing key: {} - trace:\n{}'.
                    format(event.key(), stackTrace()))

            #Otherwise allow the editor to handle said event in the default manner
            return function(event)
        return interceptKeyEvent

    def keyEventMapper(self, key):

        self.keyPressBuffer = self.appendDelimitedStr(key, self.keyPressBuffer,
            Qt.Key_Escape, ',')

        if self.mode == self.DELETE_MODE or self.mode == self.YANK_MODE:
            isBuffer = True
            bufferSrc = self.keyMap['BUFFER_COMMANDS']

        else:
            isBuffer = False
            bufferSrc = self.keyMap

        customKeyEvent = {'details': bufferSrc.get(self.keyPressBuffer, False),
            'key': key}

        logger.info('customKeyEvent: {}'.format(customKeyEvent))

        if customKeyEvent['details'] and callable(customKeyEvent['details']['Function']):
            if isBuffer or self.keyPressBuffer == Qt.Key_X:
                #self.cursor.beginEditBlock()

                #perform the appropriate selection
                customKeyEvent['details']['MoveOperation']()

            else:
                pass
                #self.cursor = None

            success = customKeyEvent['details']['Function'](customKeyEvent)

            if isBuffer:
                pass
                #self.cursor.endEditBlock()

            self.keyPressBuffer = ''

        else:
            success = None

        return success

# ==============================================================================
# CUSTOM EVENT HANDLERS
# ==============================================================================

    # ==============================================================================
    # BUFFER HANDLING
    # ==============================================================================

    #TODO: Make the select function instances of this function as opposed to vimja
    def bufferChars(self, event, bufferName=0):
        ''' Selects the appropriate text then adds it to the appropriate buffer then
        deletes it if it was cut event.

        @arg dict event containing a buffer dictionary created from the keyPressEvent and
            it's corresponding keyMap json object

        @arg mixed bufferName the index for the buffer to be added to

        @ret mixed True if copy/cut was success False otherwise

        '''

        try:
            #get the cursor and prepare to edit the file
            #self.cursor = self.editor.textCursor()
            #self.cursor.beginEditBlock()

            ##perform the appropriate selection
            #event['details']['MoveOperation'](cursor)

            #add the text to the buffer
            self.copyPasteBuffer[bufferName]['text'] = self.cursor.selectedText()

            #if the text was a full line special behaviour is expected for pasting
            self.copyPasteBuffer[bufferName]['isLine'] = event['details']['isLine']

            logger.info('text: "{}"'.format(self.copyPasteBuffer[bufferName]['text']))
            logger.info('isLine: {}'.format(
                self.copyPasteBuffer[bufferName]['isLine']))

            #if we are in delete mode or key pressed was x remove the text
            if self.mode == self.DELETE_MODE or event['key'] == Qt.Key_X:
                self.cursor.removeSelectedText()

                #if we are removing a whole line make sure to remove the new line chr
                if event['details']['isLine']:
                    self.cursor.deleteChar()

        except Exception:
            logger.warning('copy/cut error: {}'.format(stackTrace()))

        self.switchMode({'details': self.keyMap[Qt.Key_Escape], 'key': Qt.Key_Escape})
        #self.cursor.endEditBlock()

    def selectLine(self):
        ''' Selects the whole line

        @arg QTextCursor cursor cursor being used

        '''

        self.cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor, 1)
        self.cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor, 1)

    def selectChar(self):
        ''' Selects the next character

        @arg QTextCursor cursor cursor being used

        '''

        self.cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 1)

    def paste(self, event, bufferName=0):
        ''' Selects the appropriate text then adds it to the appropriate buffer then
        deletes it if it was cut event.

        @arg dict event containing a buffer dictionary created from the keyPressEvent and
            it's corresponding keyMap json object

        @arg mixed bufferName the index for the buffer to be added to

        @ret mixed True if copy/cut was success False otherwise

        '''

        try:
            logger.info('pasting: {}'.format(self.copyPasteBuffer[bufferName]))

            #get the cursor and prepare to edit the file
            #self.cursor = self.editor.textCursor()
            #self.cursor.beginEditBlock()

            #if we are pasting a whole line we need to create an empty line above/below
            #the current line
            if self.copyPasteBuffer[bufferName]['isLine']:
                logger.info('in if')

                #if we are pasting before the cursor we need to move up so as to create
                #an empty line above the current one
                if not event['details']['after']:
                    logger.info('in if not')
                    self.move({'details': self.keyMap[Qt.Key_K], 'key': Qt.Key_K})

                #create a new line and move the cursor to the beginning of it to ignore
                #the auto indentation
                self.addNewLine()
                self.cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor)

            #if we are not pasting a whole line and are pasting after the cursor
            #we need to move the cursor to the right
            elif event['details']['after']:
                self.cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor)

            #insert the buffered text into the file
            self.cursor.insertText(self.copyPasteBuffer[bufferName]['text'])

        except Exception:
            logger.warning('pasting error: {}'.format(stackTrace()))

        #self.cursor.endEditBlock()

    # ==============================================================================
    # MODE HANDLING
    # ==============================================================================

    #TODO: Remove the residual cursor size that occurs when changing from insert
        #to command mode
    def switchMode(self, event):
        ''' Changes the mode of the editor

        @arg dict event containing a mode dictionary created from the keyPressEvent and
            it's corresponding keyMap json object

        @ret bool success returns True if there were no errors, False otherwise

        '''

        success = True

        try:
            self.mode = event['details']['Mode']
            self.defaultCursorMoveType = event['details']['Anchor']
            self.editor.setCursorWidth(event['details']['CursorWidth'])

        except Exception:
            logger.warning('Error while switching mode: {}'.format(stackTrace()))
            success = False

        return success

    # ==============================================================================
    # MOVEMENT HANDLING
    # ==============================================================================

    def move(self, event, moveType=QTextCursor.MoveAnchor):
        ''' Moves the cursor

        @arg dict event containing a movement dictionary created from the keyPressEvent
            and it's corresponding keyMap json object

        @ret bool success True if the cursor was successfully moved

        '''

        success = True

        try:

            moveOperation = getattr(QTextCursor, event['details']['MoveOperation'], False)

            if moveOperation is not False:
                #self.cursor = self.editor.textCursor()
                #self.cursor.movePosition(moveOperation, self.defaultCursorMoveType,
                self.cursor.movePosition(moveOperation, moveType,
                    event['details']['N'])

                self.editor.setTextCursor(self.cursor)

            else:
                raise Exception('Invalid move operation: {}'.format(stackTrace()))

        except Exception:
            logger.warning('Error while moving: {}'.format(stackTrace()))
            success = False

        return success

    # ==============================================================================
    # SEARCHING
    # ==============================================================================

    #TODO: Implement search highlighting
    def searchDocument(self, key):
        ''' Searches the file for the current regex (case insensitive)

        @arg int key the integer value of the key that was just pressed

        '''

        if key == Qt.Key_Enter:
            self.isSearching = False
            pass

        elif key == Qt.Key_Backspace:
            self.regexString = self.regexString[:-1]

        else:
            self.regexString += chr(key)

            docText = self.editor.get_text().upper()
            word = re.search(self.regexString, docText)

            self.editor.highlight_selected_word(word.string)
            self.editor.set_cursor_position(word.start())

# ==============================================================================
# USELESS
# ==============================================================================

    def finish(self):
        # Shutdown your plugin
        logger.info('Shutting down Vimja\n')

    def get_preferences_widget(self):
        # Return a widget for customize your plugin
        pass


# ==============================================================================
# DEV EXAMPLE CODE
# ==============================================================================

    # ==============================================================================
    # INSERT INTO EDITOR
    # ==============================================================================

        #tab = self.editorService.get_actual_tab()
        #self.cursor = tab.textCursor()
        #self.cursor.beginEditBlock()

        #self.cursor.insertText('hi')
        #self.cursor.endEditBlock()

    # ==============================================================================
    # LOGGER
    # ==============================================================================

        #logger.warning('direction: {}'.format(direction))
        #logger.warning('curPos1: {}'.format(self.getPos()))

        #self.cursor = self.editor.textCursor()
        #self.cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor, 1)
        #self.cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor, 1)
        #e = self._main.get_actual_editor()
        #e.cut()
        #return True

    # ==============================================================================
    # DELETE A LINE
    # ==============================================================================

        #self.cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor, 1)
        #self.cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor, 1)
        #self.cursor.removeSelectedText()
        #self.cursor.deleteChar()

    # ==============================================================================
    # MOVING
    # ==============================================================================

        #def selectLine(self, cursor):
            #self.cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor, 1)
            #self.cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor, 1)
            #self.cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 1)

        #def selectChar(self, cursor):
            #self.cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 1)
        #

        #self.editor.insert_new_line()
