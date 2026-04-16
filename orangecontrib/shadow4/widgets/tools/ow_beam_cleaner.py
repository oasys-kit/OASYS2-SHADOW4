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
                output_data.beam.clean_lost_rays()
                try:
                    output_data.footprint.clean_lost_rays()
                except:
                    pass

            self.Outputs.shadow_data.send(output_data)
            self.Outputs.trigger.send(TriggerIn(new_object=True))

add_widget_parameters_to_module(__name__)