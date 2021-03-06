# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2009, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#
import os,subprocess
from Xlib import display
from PyQt4 import QtGui
from PyQt4.QtCore import SIGNAL, QString

from kaptan.screen import Screen

#Pds Stuff
import kaptan.screens.context as ctx
from kaptan.screens.context import *
from kaptan.plugins import Desktop

FOR_LXDE = ctx.Pds.session == ctx.pds.LXDE
FOR_ENLIGHTENMENT = ctx.Pds.session == ctx.pds.Enlightenment
FOR_FLUXBOX = ctx.Pds.session == ctx.pds.Fluxbox
FOR_GNOME = ctx.Pds.session == ctx.pds.Gnome
FOR_XFCE=ctx.Pds.session == ctx.pds.Xfce
FOR_GNOME3 = ctx.Pds.session == ctx.pds.Gnome3
SHOW_MOUSE_SPEED = FOR_LXDE | FOR_ENLIGHTENMENT | FOR_FLUXBOX | FOR_GNOME | FOR_XFCE | FOR_GNOME3
if SHOW_MOUSE_SPEED:
    from kaptan.screens.ui_scrMouse_comak import Ui_mouseWidget
else:
    from kaptan.screens.ui_scrMouse import Ui_mouseWidget

RIGHT_HANDED, LEFT_HANDED = range(2)

class Widget(QtGui.QWidget, Screen):
    screenSettings = {}
    screenSettings["hasChanged"] = False

    # title and description at the top of the dialog window
    title = i18n("Mouse")
    desc = i18n("Setup Mouse Behavior")


    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_mouseWidget()
        self.ui.setupUi(self)
        if SHOW_MOUSE_SPEED:
            self.ui.Sensitivity.hide() #FIXME: use these or delete that option
            self.ui.lbl_Sensitivity.hide() #FIXME: 

        # Our default click behavior is double click. So make SingleClick = false (kdeglobals)
        self.clickBehavior = False

        # read default settings
        try:
            self.__class__.screenSettings["selectedMouse"] = Desktop.mouse.getMouseHand()


            self.__class__.screenSettings["selectedBehavior"] = Desktop.mouse.getMouseSingleClick()

            self.ui.singleClick.setChecked(self.str2bool(self.__class__.screenSettings["selectedBehavior"]))
            self.clickBehavior = self.str2bool(self.__class__.screenSettings["selectedBehavior"])

            if self.__class__.screenSettings["selectedMouse"] == "LeftHanded":
                self.ui.radioButtonLeftHand.setChecked(True)

        except:
            pass

        # set signals
        self.connect(self.ui.radioButtonRightHand, SIGNAL("toggled(bool)"), self.setHandedness)
        self.connect(self.ui.checkReverse, SIGNAL("toggled(bool)"), self.setHandedness)
        if SHOW_MOUSE_SPEED:
            self.connect(self.ui.Acceleration, SIGNAL("sliderMoved(int)"), self.setMouseAcceleration)
            self.getMouseAcceleration()
        else:
            self.connect(self.ui.singleClick, SIGNAL("clicked()"), self.clickBehaviorToggle)
            self.connect(self.ui.DoubleClick, SIGNAL("clicked()"), self.clickBehaviorToggle)

    def str2bool(self, s):
        return bool(eval(s).capitalize())

    def clickBehaviorToggle(self):
        self.clickBehavior = self.ui.singleClick.isChecked()

    def getMouseMap(self):
        self.mapMouse = {}

        if self.ui.radioButtonRightHand.isChecked():
            self.handed = RIGHT_HANDED

        else:
            self.handed = LEFT_HANDED

        self.mapMouse = display.Display().get_pointer_mapping()
        self.num_buttons = len(self.mapMouse)

    def setHandedness(self, item):
        self.getMouseMap()

        # mouse has 1 button
        if self.num_buttons == 1:
            self.mapMouse[0] = 1

        # mouse has 2 buttons
        elif self.num_buttons == 2:
            if self.handed == RIGHT_HANDED:
                self.mapMouse[0], self.mapMouse[1] = 1, 3
            else:
                self.mapMouse[0], self.mapMouse[1] = 3, 1

        # mouse has 3 or more buttons
        else:
            if self.handed == RIGHT_HANDED:
                self.mapMouse[0], self.mapMouse[2] = 1, 3
            else:
                self.mapMouse[0], self.mapMouse[2] = 3, 1

            if self.num_buttons >= 5:
                # get wheel position
                for pos in range(0, self.num_buttons):
                    if self.mapMouse[pos] in (4,5): break

                if pos < self.num_buttons -1:
                    if self.ui.checkReverse.isChecked():
                        self.mapMouse[pos], self.mapMouse[pos + 1] = 5, 4
                    else:
                        self.mapMouse[pos], self.mapMouse[pos + 1] = 4, 5

        display.Display().set_pointer_mapping(self.mapMouse)


        if self.handed == RIGHT_HANDED:
            Desktop.mouse.setMouseHand(QString("RightHanded"))
            self.__class__.screenSettings["selectedMouse"] = "RightHanded"
        else:
            Desktop.mouse.setMouseHand(QString("LeftHanded"))
            self.__class__.screenSettings["selectedMouse"] = "LeftHanded"

        Desktop.mouse.setReverseScrollPolarity(QString(str(self.ui.checkReverse.isChecked())))
    def getMouseAcceleration(self):
        command = subprocess.Popen(["xset","q"], stdout=subprocess.PIPE)
        out,err = command.communicate()
        rate = out.split("acceleration:")[1].split()[0]
        #turn rational number that is in form a/b into float
        exec("rate="+rate+".0")
        rate = rate*33
        self.ui.Acceleration.setValue(rate)

    def setMouseAcceleration(self,rate):
        #turn integer to x/5 form
        rate = (rate*15)/100
        os.system("xset m %s/5 0"%rate)

    def shown(self):
        pass

    def execute(self):
        self.__class__.screenSettings["summaryMessage"] ={}

        self.__class__.screenSettings["summaryMessage"].update({"selectedMouse": i18n("Left Handed") if self.__class__.screenSettings["selectedMouse"] == "LeftHanded" else i18n("Right Handed")})
        self.__class__.screenSettings["summaryMessage"].update({"clickBehavior": i18n("Single Click ") if self.clickBehavior else i18n("Double Click")})
        Desktop.mouse.setMouseSingleClick(str(self.clickBehavior))
        return True

