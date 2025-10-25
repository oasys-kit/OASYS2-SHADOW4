import copy
import numpy

from orangewidget import gui
from orangewidget.widget import Input, Output

from orangewidget.settings import Setting
from oasys2.widget import gui as oasysgui
from oasys2.widget.gui import ConfirmDialog, Styles
from oasys2.widget.util.widget_objects import TriggerIn
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from orangecontrib.shadow4.util.shadow4_objects import ShadowData, S4Beam
from orangecontrib.shadow4.util.shadow4_util import ShadowCongruence
from orangecontrib.shadow4.widgets.gui.ow_automatic_element import AutomaticElement
from orangecontrib.shadow4.util.shadow4_util import TriggerToolsDecorator

class AccumulatingLoopPoint(AutomaticElement):
    name = "Beam Accumulating Point"
    description = "User Defined: Beam Accumulating Point"
    icon = "icons/beam_accumulating.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 2
    category = "User Defined"
    keywords = ["data", "file", "load", "read"]

    class Inputs:
        shadow_data = Input("Shadow Data", ShadowData, default=True, auto_summary=False)

    class Outputs:
        shadow_data = Output("Shadow Data", ShadowData, default=True, auto_summary=False)
        trigger     = TriggerToolsDecorator.get_trigger_output()

    IMAGE_WIDTH = 878
    IMAGE_HEIGHT = 635

    input_data : ShadowData = None

    want_main_area = 0

    number_of_accumulated_rays = Setting(10000)
    kind_of_accumulation = Setting(0)

    current_number_of_rays = 0
    current_intensity = 0
    current_number_of_total_rays = 0
    current_number_of_lost_rays = 0

    keep_go_rays = Setting(1)

    def __init__(self):
        super().__init__(show_automatic_box=False)
        self.is_automatic_run = True

        self.setFixedWidth(570)
        self.setFixedHeight(380)

        self.controlArea.setFixedWidth(560)

        button_box = gui.widgetBox(self.controlArea, "", addSpace=True, orientation="horizontal")

        self.start_button = gui.button(button_box, self, "Send Beam", callback=self.send_signal)
        self.start_button.setFixedHeight(45)

        button = gui.button(button_box, self, "Reset Accumulation", callback=self.callResetSettings)
        button.setStyleSheet(Styles.button_blue)

        left_box_1 = oasysgui.widgetBox(self.controlArea, "Accumulating Loop Management", addSpace=False, orientation="vertical", height=260)

        gui.comboBox(left_box_1, self, "kind_of_accumulation", label="Accumulated Quantity", labelWidth=350,
                     items=["Number of Good Rays ", "Intensity of Good Rays"],
                     callback=self.set_KindOfAccumulation,
                     sendSelectedValue=False, orientation="horizontal")

        self.left_box_1_1 = oasysgui.widgetBox(left_box_1, "", addSpace=False, orientation="vertical", height=35)
        self.left_box_1_2 = oasysgui.widgetBox(left_box_1, "", addSpace=False, orientation="vertical", height=35)

        oasysgui.lineEdit(self.left_box_1_1, self, "number_of_accumulated_rays", "Number of accumulated good rays\n(before sending signal)", labelWidth=350, valueType=float,
                           orientation="horizontal")

        oasysgui.lineEdit(self.left_box_1_2, self, "number_of_accumulated_rays", "Intenisty of accumulated good rays\n(before sending signal)", labelWidth=350, valueType=float,
                           orientation="horizontal")

        self.set_KindOfAccumulation()

        gui.comboBox(left_box_1, self, "keep_go_rays", label="Remove lost rays from beam", labelWidth=350, items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal")

        gui.separator(left_box_1)

        le = oasysgui.lineEdit(left_box_1, self, "current_number_of_rays", "Current number of good rays", labelWidth=350, valueType=int, orientation="horizontal")
        le.setReadOnly(True)
        le.setStyleSheet(Styles.line_edit_read_only)

        self.le_current_intensity = oasysgui.lineEdit(left_box_1, self, "current_intensity", "Current intensity", labelWidth=350, valueType=float, orientation="horizontal")
        self.le_current_intensity.setReadOnly(True)
        self.le_current_intensity.setStyleSheet(Styles.line_edit_read_only)

        le = oasysgui.lineEdit(left_box_1, self, "current_number_of_lost_rays", "Current number of lost rays", labelWidth=350, valueType=int, orientation="horizontal")
        le.setReadOnly(True)
        le.setStyleSheet("color: darkred; background-color: rgb(243, 240, 160);")

        le = oasysgui.lineEdit(left_box_1, self, "current_number_of_total_rays", "Current number of total rays", labelWidth=350, valueType=int, orientation="horizontal")
        le.setReadOnly(True)
        le.setStyleSheet("color: black; background-color: rgb(243, 240, 160);")

        gui.rubber(self.controlArea)

    def set_KindOfAccumulation(self):
        self.left_box_1_1.setVisible(self.kind_of_accumulation==0)
        self.left_box_1_2.setVisible(self.kind_of_accumulation==1)

    def send_signal(self):
        self.Outputs.shadow_data.send(self.input_data)
        self.Outputs.trigger.send(TriggerIn(interrupt=True))

    def callResetSettings(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the accumulated beam"):
            self.current_number_of_rays = 0
            self.current_intensity = 0.0
            self.current_number_of_lost_rays = 0
            self.current_number_of_total_rays = 0
            self.input_data = None

    @Inputs.shadow_data
    def set_shadow_data(self, input_data: ShadowData):
        if ShadowCongruence.check_empty_data(input_data):
            proceed = True
            beam : S4Beam     = input_data.beam
            footprint: S4Beam = input_data.footprint

            if not ShadowCongruence.check_good_beam(beam):
                if not ConfirmDialog.confirmed(parent=self, message="Beam contains bad values, skip it?"):
                    proceed = False

            if proceed:
                scanning_data = input_data.scanning_data

                go = numpy.where(beam.rays[:, 9] == 1)

                nr_good  = len(beam.rays[go])
                nr_total = len(beam.rays)
                nr_lost  = nr_total - nr_good

                intensity = beam.histo1(1, nolost=1, ref=23)['intensity']

                self.current_number_of_rays       += nr_good
                self.current_intensity            += intensity
                self.current_number_of_lost_rays  += nr_lost
                self.current_number_of_total_rays += nr_total

                self.le_current_intensity.setText("{:10.3f}".format(self.current_intensity))

                if self.keep_go_rays == 1:
                    beam.rays = copy.deepcopy(beam.rays[go])
                    if not footprint is None: footprint.rays = copy.deepcopy(footprint.rays[go])

                if not self.input_data is None:
                    self.input_data = ShadowData.merge_shadow_data(self.input_data, input_data, which_flux=3, which_beamline=0)
                else:
                    beam.rays[:, 11] = numpy.arange(1, len(beam.rays) + 1, 1)  # ray_index
                    if not footprint is None: footprint.rays[:, 11] = numpy.arange(1, len(footprint.rays) + 1, 1)

                    self.input_data = input_data

                self.input_data.scanning_data = scanning_data

                if (self.kind_of_accumulation == 0 and self.current_number_of_rays < self.number_of_accumulated_rays) or \
                   (self.kind_of_accumulation == 1 and self.current_intensity < self.number_of_accumulated_rays):
                    self.Outputs.trigger.send(TriggerIn(new_object=True))
                else:
                    self.send_signal()

                    self.current_number_of_rays       = 0
                    self.current_intensity            = 0.0
                    self.current_number_of_lost_rays  = 0
                    self.current_number_of_total_rays = 0

                    self.input_data = None

add_widget_parameters_to_module(__name__)