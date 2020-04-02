from defconAppKit.windows.baseWindow import BaseWindowController
from mojo.events import addObserver, removeObserver, extractNSEvent, getActiveEventTool
from lib.tools.defaults import getDefault, getDefaultColor
from lib.tools.misc import NSColorToRgba
from mojo.drawingTools import *

'''
Type: RoboFont startup script.

Allows you to select the margins as if you would any point or segment.
Click on the sidebearing and move it with the mouse or arrows!

Ryan Bugden and Bahman Eslami
with thanks to Erik van Blokland and Frederik Berlaen

v0.2.0:   2020.03.31
v0.1.5:   2019.12.20
v0.1.1:   2019.04.10
v0.1.0:   2019.03.07
'''

ACTIVE_TOOLS = ('EditingTool', 'ScalingEditTool')  # works only while these tool(s) are active

class MarginSelector():

    def __init__(self):
        self.glyphViewSelectionColor = NSColorToRgba(getDefaultColor("glyphViewSelectionColor"))
        self.rightMarginIsSelected = False
        self.leftMarginIsSelected = False
        self.glyph = None
        self.font = None
        self.mousePoint = None
        self.mouseDelta = None
        self.deltaX = 0
        self.threshold = 5
        self.increment = 1
        self.stroke_width = 2
        self.glyphViewShiftIncrement = getDefault("glyphViewShiftIncrement")
        self.glyphViewCommandShiftIncrement = getDefault("glyphViewCommandShiftIncrement")
        self.shiftDown = False
        self.commandDown = False
        addObserver(self, 'mouseDragged', 'mouseDragged')
        addObserver(self, 'mouseUp', 'mouseUp')
        addObserver(self, 'mouseDown', 'mouseDown')
        addObserver(self, 'keyDown', 'keyDown')
        addObserver(self, 'modifiersChanged', 'modifiersChanged')
        addObserver(self, 'draw', 'draw')
        addObserver(self, 'viewDidChangeGlyph', 'viewDidChangeGlyph')

    @property
    def isValid(self):
        return getActiveEventTool().__class__.__name__ in ACTIVE_TOOLS and self.glyph is not None

    def destroy(self, sender):
        removeObserver(self, 'mouseDragged')
        removeObserver(self, 'mouseUp')
        removeObserver(self, 'mouseDown')
        removeObserver(self, 'keyDown')
        removeObserver(self, 'modifiersChanged')
        removeObserver(self, 'draw')
        removeObserver(self, 'viewDidChangeGlyph')

    def mouseDown(self, notification):
        if self.isValid:
            if self.glyph.selectedPoints == ():
                self.rightMarginIsSelected = False
                self.leftMarginIsSelected = False
            self.mousePoint = notification['point']
            self.mouseDelta = self.mousePoint
            self.deltaX = 0
            self.glyph.prepareUndo()

    def mouseDragged(self, notification):
        if self.isValid:
            self.mouseDelta = notification['point']
            newDeltaX = notification['delta'].x - self.deltaX
            self.deltaX = notification['delta'].x
            if self.glyph.selectedPoints != () and not self.shiftDown:
                if self.rightMarginIsSelected:
                    self.moveMargin(newDeltaX)
                if self.leftMarginIsSelected:
                    self.moveMargin(newDeltaX)

    def moveMargin(self, delta):
        if self.rightMarginIsSelected:
            self.glyph.rightMargin += delta
            self.glyph.changed()
        if self.leftMarginIsSelected:
            self.glyph.leftMargin -= delta
            self.glyph.changed()

    def mouseUp(self, notification):
        if self.isValid:
            if self.mouseDelta is not None:
                start, end = sorted([self.mousePoint.x - self.threshold, self.mouseDelta.x + self.threshold])
                if start <= self.glyph.width < end:
                    if self.shiftDown and self.rightMarginIsSelected:
                        self.rightMarginIsSelected = False
                    else:
                        self.rightMarginIsSelected = True
                if start <= 0 < end:
                    if self.shiftDown and self.leftMarginIsSelected:
                        self.leftMarginIsSelected = False
                    else:
                        self.leftMarginIsSelected = True
                if self.leftMarginIsSelected and self.rightMarginIsSelected:
                    self.leftMarginIsSelected = False
                    self.rightMarginIsSelected = False
                self.glyph.performUndo()
            self.mousePoint = None
            self.mouseDelta = None

    def keyUp(self, notification):
        if self.isValid:
            self.glyph.performUndo()

    def viewDidChangeGlyph(self, notification):
        self.glyph = notification['glyph']
        if self.glyph is not None:
            self.font = self.glyph.font

    def keyDown(self, event):
        if self.isValid:
            ns_event = extractNSEvent(event)
            leftDown = ns_event['left']
            rightDown = ns_event['right']
            delta = self.increment
            if self.shiftDown:
                multiplier = self.glyphViewShiftIncrement
                if self.commandDown:
                    multiplier = self.glyphViewCommandShiftIncrement
                delta *= multiplier
            if leftDown:
                self.moveMargin(-delta)
            if rightDown:
                self.moveMargin(delta)

    def modifiersChanged(self, event):
        ns_event = extractNSEvent(event)
        self.shiftDown = ns_event['shiftDown']
        self.commandDown = ns_event['commandDown']

    def draw(self, notification):
        if self.isValid:
            strokeWidth(self.stroke_width*notification['scale'])
            stroke(*self.glyphViewSelectionColor)
            if self.rightMarginIsSelected:
                line((self.glyph.width, self.font.info.descender),
                     (self.glyph.width, self.font.info.ascender))
            elif self.leftMarginIsSelected:
                line((0, self.font.info.descender),
                     (0, self.font.info.ascender))

def installMarginSelector(debug=False):
    if debug:
        from vanilla import FloatingWindow

        class DebuggerWindow(BaseWindowController):
            def __init__(self):
                self.w = FloatingWindow((123, 44), 'debug!')
                ms = MarginSelector()
                self.w.open()
                self.w.bind("close", ms.destroy)
        DebuggerWindow()
    else:
        MarginSelector()

if __name__ == '__main__':
    installMarginSelector(True)
