Vimja:
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
 * G - end of file *

> Modes:
 * i - insert mode
 * Esc - normal mode/clear command buffer

> Cut/copy/paste:
 * dd - cut line **
 * yy - copy line **
 * p - paste line below **
 * x - cut current char **

* - all commands that use upper case characters are buggy, they look for the shift key
    press followed by that character as opposed to them being down at the same time

** - currently uses standard copy paste buffer, same as <Ctrl-c>, <Ctrl-x> and <Ctrl-p>
