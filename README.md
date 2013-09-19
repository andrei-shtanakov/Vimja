Vimja
======
## A vim plugin for the Ninja-IDE (beta)

Features:

> Movement:
 * j - down
 * k - up
 * h - left
 * l - right
 * w - word
 * b - back
 * 0 - start of line
 * $ - end of line
 * gg - start of file
 * G - end of file **

> Modes:
 * i - insert mode
 * Esc - normal mode/clear command buffer

> Cut/copy/paste:
 * dd - cut line ^ ++
 * yy - copy line ^ ++
 * p - post cursor paste ^
 * P - pre cursor paste ^ ** @
 * x - cut current char ^

** - all commands that use upper case characters are buggy, they look for the shift key
    press followed by that character as opposed to them being down at the same time

^ - uses seperate text buffer from standard copy paste (dd followed by Ctrl-v != dd followed by p)

++ dy == dd and yd == yy (might be fixed in future version if it bothers enough people since that command
                         doesn't exist in vim anyway)

@ The pre cursor paste is buggy for a full line paste. It currently inserts a newline above current line and
  then pastes the text at the start of the current line
