#!/usr/bin/env python
# -*- coding: utf-8 -*-
# #########################################################################
# Copyright (c) 2018, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2018. UChicago Argonne, LLC. This software was produced       #
# under U.S. Government contract DE-AC02-06CH11357 for Argonne National   #
# Laboratory (ANL), which is operated by UChicago Argonne, LLC for the    #
# U.S. Department of Energy. The U.S. Government has rights to use,       #
# reproduce, and distribute this software.  NEITHER THE GOVERNMENT NOR    #
# UChicago Argonne, LLC MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR        #
# ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If software is     #
# modified to produce derivative works, such modified software should     #
# be clearly marked, so as not to confuse it with the version available   #
# from ANL.                                                               #
#                                                                         #
# Additionally, redistribution and use in source and binary forms, with   #
# or without modification, are permitted provided that the following      #
# conditions are met:                                                     #
#                                                                         #
#     * Redistributions of source code must retain the above copyright    #
#       notice, this list of conditions and the following disclaimer.     #
#                                                                         #
#     * Redistributions in binary form must reproduce the above copyright #
#       notice, this list of conditions and the following disclaimer in   #
#       the documentation and/or other materials provided with the        #
#       distribution.                                                     #
#                                                                         #
#     * Neither the name of UChicago Argonne, LLC, Argonne National       #
#       Laboratory, ANL, the U.S. Government, nor the names of its        #
#       contributors may be used to endorse or promote products derived   #
#       from this software without specific prior written permission.     #
#                                                                         #
# THIS SOFTWARE IS PROVIDED BY UChicago Argonne, LLC AND CONTRIBUTORS     #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT       #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS       #
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL UChicago     #
# Argonne, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,        #
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,    #
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;        #
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER        #
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT      #
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN       #
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE         #
# POSSIBILITY OF SUCH DAMAGE.                                             #
# #########################################################################

import sys


from AnyQt.QtWidgets import QMessageBox

from orangewidget import gui
from orangewidget.widget import Input, Output

from orangewidget.settings import Setting
from oasys2.widget import gui as oasysgui
from oasys2.widget.widget import OWLoopWidget, OWAction
from oasys2.widget.gui import ConfirmDialog, Styles
from oasys2.widget.util.widget_objects import TriggerIn, TriggerOut
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

class SourceSeedLoopPoint(OWLoopWidget):

    name = "Source Seed Loop Point"
    description = "Loops: LoopPoint"
    icon = "icons/cycle.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 1
    category = "User Defined"
    keywords = ["data", "file", "load", "read"]

    class Inputs:
        trigger_in = Input("Trigger", TriggerIn, default=True, auto_summary=False)

    class Outputs:
        trigger_out = Output("Trigger", TriggerOut, default=True, auto_summary=False)

    want_main_area = 0

    number_of_new_objects = Setting(1)
    current_new_object = 0
    run_loop = True
    suspend_loop = False

    seed_increment=Setting(1)

    #################################
    process_last = True
    #################################

    def __init__(self):
        self.runaction = OWAction("Start", self)
        self.runaction.triggered.connect(self.startLoop)
        self.addAction(self.runaction)

        self.runaction = OWAction("Stop", self)
        self.runaction.triggered.connect(self.stopLoop)
        self.addAction(self.runaction)

        self.runaction = OWAction("Suspend", self)
        self.runaction.triggered.connect(self.suspendLoop)
        self.addAction(self.runaction)

        self.runaction = OWAction("Restart", self)
        self.runaction.triggered.connect(self.restartLoop)
        self.addAction(self.runaction)

        self.setFixedWidth(400)
        self.setFixedHeight(270)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=True, orientation="horizontal")

        self.start_button = gui.button(button_box, self, "Start", callback=self.startLoop)
        self.start_button.setFixedHeight(35)

        stop_button = gui.button(button_box, self, "Stop", callback=self.stopLoop)
        stop_button.setStyleSheet("color: red; font-weight: bold; height: 35px;")

        self.stop_button = stop_button

        button_box = gui.widgetBox(self.controlArea, "", addSpace=True, orientation="horizontal")

        suspend_button = gui.button(button_box, self, "Suspend", callback=self.suspendLoop)
        suspend_button.setStyleSheet("color: orange; font-weight: bold; height: 35px;")

        self.re_start_button = gui.button(button_box, self, "Restart", callback=self.restartLoop)
        self.re_start_button.setFixedHeight(35)
        self.re_start_button.setEnabled(False)

        left_box_1 = oasysgui.widgetBox(self.controlArea, "Loop Management", addSpace=True, orientation="vertical", width=380, height=120)

        oasysgui.lineEdit(left_box_1, self, "number_of_new_objects", "Number of new " + self.get_object_name() + "s", labelWidth=250, valueType=int, orientation="horizontal")

        self.le_current_new_object = oasysgui.lineEdit(left_box_1, self, "current_new_object", "Current New " + self.get_object_name(), labelWidth=250, valueType=int, orientation="horizontal")
        self.le_current_new_object.setReadOnly(True)
        self.le_current_new_object.setStyleSheet(Styles.line_edit_read_only)

        gui.separator(left_box_1)

        oasysgui.lineEdit(left_box_1, self, "seed_increment", "Source Montecarlo Seed Increment", labelWidth=250, valueType=int, orientation="horizontal")

        gui.rubber(self.controlArea)

    def startLoop(self):
        self.current_new_object = 1
        self.start_button.setEnabled(False)
        self.setStatusMessage("Running " + self.get_object_name() + " " + str(self.current_new_object) + " of " + str(self.number_of_new_objects))

        self.Outputs.trigger_out.send(TriggerOut(new_object=True, additional_parameters={"seed_increment" : self.seed_increment}))

    def stopLoop(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Interruption of the Loop?"):
            self.run_loop = False
            self.setStatusMessage("Interrupted by user")

    def suspendLoop(self):
        try:
            if ConfirmDialog.confirmed(parent=self, message="Confirm Suspension of the Loop?"):
                self.run_loop = False
                self.suspend_loop = True
                self.stop_button.setEnabled(False)
                self.re_start_button.setEnabled(True)
                self.setStatusMessage("Suspended by user")
        except:
            pass


    def restartLoop(self):
        try:
            self.run_loop = True
            self.suspend_loop = False
            self.stop_button.setEnabled(True)
            self.re_start_button.setEnabled(False)
            self.passTrigger(TriggerIn(new_object=True))
        except:
            pass

    @Inputs.trigger_in
    def passTrigger(self, trigger):
        if self.run_loop:
            if trigger:
                if trigger.interrupt:
                    self.current_new_object = 0
                    self.start_button.setEnabled(True)
                    self.setStatusMessage("")
                    self.Outputs.trigger_out.send(TriggerOut(new_object=False))
                elif trigger.new_object:
                    if self.current_new_object == 0:
                        QMessageBox.critical(self, "Error", "Loop has to be started properly: press the button Start", QMessageBox.Ok)
                        return

                    if self.current_new_object < self.number_of_new_objects:
                        self.current_new_object += 1
                        self.setStatusMessage("Running " + self.get_object_name() + " " + str(self.current_new_object) + " of " + str(self.number_of_new_objects))
                        self.start_button.setEnabled(False)
                        self.Outputs.trigger_out.send(TriggerOut(new_object=True,
                                                                 additional_parameters={"seed_increment" : self.seed_increment}))
                    else:
                        self.current_new_object = 0
                        self.start_button.setEnabled(True)
                        self.setStatusMessage("")
                        self.Outputs.trigger_out.send(TriggerOut(new_object=False))
        else:
            if not self.suspend_loop:
                self.current_new_object = 0
                self.start_button.setEnabled(True)

            self.Outputs.trigger_out.send(TriggerOut(new_object=False))
            self.setStatusMessage("")
            self.run_loop = True
            self.suspend_loop = False

    def get_object_name(self):
        return "Beam"

add_widget_parameters_to_module(__name__)
