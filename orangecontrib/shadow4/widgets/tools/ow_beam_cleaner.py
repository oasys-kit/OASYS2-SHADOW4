#!/usr/bin/env python
# -*- coding: utf-8 -*-
# #########################################################################
# Copyright (c) 2020, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2020. UChicago Argonne, LLC. This software was produced       #
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

import numpy, copy

from orangewidget import gui
from orangewidget.widget import Input, Output

from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module
from oasys2.widget.widget import OWWidget

from orangecontrib.shadow4.util.shadow4_objects import ShadowData

from orangecontrib.shadow4.util.shadow4_util import ShadowCongruence, TriggerToolsDecorator
from oasys2.widget.util.widget_objects import TriggerIn

class BeamCleaner(OWWidget, TriggerToolsDecorator):
    name = "Beam Cleaner"
    description = "Tools: Beam Cleaner"
    icon = "icons/clean.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 30
    category = "User Defined"
    keywords = ["data", "file", "load", "read"]

    class Inputs:
        shadow_data = Input("Shadow Data", ShadowData, default=True, auto_summary=False)

    class Outputs:
        shadow_data = Output("Shadow Data", ShadowData, default=True, auto_summary=False)
        trigger = TriggerToolsDecorator.get_trigger_output()

    want_main_area = 0
    want_control_area = 1

    def __init__(self):
         self.setFixedWidth(300)
         self.setFixedHeight(120)

         gui.separator(self.controlArea, height=20)
         gui.label(self.controlArea, self, "         LOST RAYS REMOVER", orientation="horizontal")
         gui.rubber(self.controlArea)

    @Inputs.shadow_data
    def set_shadow_data(self, shadow_data: ShadowData):
        if ShadowCongruence.check_empty_data(shadow_data):
            output_data = shadow_data.duplicate()

            if ShadowCongruence.check_good_beam(input_beam=output_data.beam):
                good = numpy.where(output_data.beam.rays[:, 9] == 1)
                output_data.beam.rays = copy.deepcopy(output_data.beam.rays[good])

            self.Outputs.shadow_data.send(output_data)
            self.Outputs.trigger.send(TriggerIn(new_object=True))

add_widget_parameters_to_module(__name__)