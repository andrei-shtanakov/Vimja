# -*- coding: UTF-8 -*-

from ninja_ide.core import plugin


class Vimja(plugin.Plugin):
    def test(self, event):
        tab = self.editor_s.get_actual_tab()
        cursor = tab.textCursor()
        cursor.beginEditBlock()
        cursor.insertText('hello ninja_ide')
        cursor.endEditBlock()

    def initialize(self):
        # Init your plugin
        self.editor_s = self.locator.get_service('editor')
        self.editor_s.editorKeyPressEvent.connect(self.test)

    def finish(self):
        # Shutdown your plugin
        pass

    def get_preferences_widget(self):
        # Return a widget for customize your plugin
        pass
