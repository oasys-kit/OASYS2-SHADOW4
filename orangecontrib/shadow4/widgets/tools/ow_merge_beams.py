import sys, numpy


from AnyQt.QtWidgets import QMessageBox

from oasys2.widget.gui import Styles
from orangewidget import gui
from orangewidget.settings import Setting
from orangewidget.widget import Input, Output

from oasys2.widget import gui as oasysgui
from oasys2.widget.util import congruence
from oasys2.widget.widget import OWWidget, OWAction
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from orangecontrib.shadow4.util.shadow4_objects import ShadowData
from orangecontrib.shadow4.util.shadow4_util import ShadowCongruence


class MergeBeams(OWWidget):

    name = "Merge Shadow4 Beam"
    description = "Tools: Merge Shadow4 Beam"
    icon = "icons/merge.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 8
    category = "Tools"
    keywords = ["data", "file", "load", "read"]
    
    class Inputs:
        shadow_data_1  = Input("Input Shadow Data # 1" , ShadowData, default=True, auto_summary=False)
        shadow_data_2  = Input("Input Shadow Data # 2" , ShadowData, default=True, auto_summary=False)
        shadow_data_3  = Input("Input Shadow Data # 3" , ShadowData, default=True, auto_summary=False)
        shadow_data_4  = Input("Input Shadow Data # 4" , ShadowData, default=True, auto_summary=False)
        shadow_data_5  = Input("Input Shadow Data # 5" , ShadowData, default=True, auto_summary=False)
        shadow_data_6  = Input("Input Shadow Data # 6" , ShadowData, default=True, auto_summary=False)
        shadow_data_7  = Input("Input Shadow Data # 7" , ShadowData, default=True, auto_summary=False)
        shadow_data_8  = Input("Input Shadow Data # 8" , ShadowData, default=True, auto_summary=False)
        shadow_data_9  = Input("Input Shadow Data # 9" , ShadowData, default=True, auto_summary=False)
        shadow_data_10 = Input("Input Shadow Data # 10", ShadowData, default=True, auto_summary=False)
    
    class Outputs:
        shadow_data = Output("Shadow Data", ShadowData, default=True, auto_summary=False)

    want_main_area=0
    want_control_area = 1

    input_data_1  = None
    input_data_2  = None
    input_data_3  = None
    input_data_4  = None
    input_data_5  = None
    input_data_6  = None
    input_data_7  = None
    input_data_8  = None
    input_data_9  = None
    input_data_10 = None

    use_weights = Setting(0)

    weight_input_data_1=Setting(0.0)
    weight_input_data_2=Setting(0.0)
    weight_input_data_3=Setting(0.0)
    weight_input_data_4=Setting(0.0)
    weight_input_data_5=Setting(0.0)
    weight_input_data_6=Setting(0.0)
    weight_input_data_7=Setting(0.0)
    weight_input_data_8=Setting(0.0)
    weight_input_data_9=Setting(0.0)
    weight_input_data_10=Setting(0.0)

    def __init__(self, show_automatic_box=True):
        super().__init__()

        self.runaction = OWAction("Merge Shadow4 Data", self)
        self.runaction.triggered.connect(self.merge_data)
        self.addAction(self.runaction)

        self.setFixedWidth(470)
        self.setFixedHeight(470)

        gen_box = gui.widgetBox(self.controlArea, "Merge Shadow4 Data", addSpace=True, orientation="vertical")

        button_box = oasysgui.widgetBox(gen_box, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Merge Data and Send", callback=self.merge_data)
        button.setStyleSheet(Styles.button_blue)

        weight_box = oasysgui.widgetBox(gen_box, "Relative Weights", addSpace=False, orientation="vertical")

        gui.comboBox(weight_box, self, "use_weights", label="Use Relative Weights?", labelWidth=350,
                     items=["No", "Yes"],
                     callback=self.set_UseWeights, sendSelectedValue=False, orientation="horizontal")

        gui.separator(weight_box, height=10)

        self.le_weight_input_data_1 = oasysgui.lineEdit(weight_box, self, "weight_input_data_1", "Input Beam 1 weight",
                                                    labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_data_2 = oasysgui.lineEdit(weight_box, self, "weight_input_data_2", "Input Beam 2 weight",
                                                    labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_data_3 = oasysgui.lineEdit(weight_box, self, "weight_input_data_3", "Input Beam 3 weight",
                                                    labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_data_4 = oasysgui.lineEdit(weight_box, self, "weight_input_data_4", "Input Beam 4 weight",
                                                    labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_data_5 = oasysgui.lineEdit(weight_box, self, "weight_input_data_5", "Input Beam 5 weight",
                                                    labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_data_6 = oasysgui.lineEdit(weight_box, self, "weight_input_data_6", "Input Beam 6 weight",
                                                    labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_data_7 = oasysgui.lineEdit(weight_box, self, "weight_input_data_7", "Input Beam 7 weight",
                                                    labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_data_8 = oasysgui.lineEdit(weight_box, self, "weight_input_data_8", "Input Beam 8 weight",
                                                    labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_data_9 = oasysgui.lineEdit(weight_box, self, "weight_input_data_9", "Input Beam 9 weight",
                                                    labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_data_10 = oasysgui.lineEdit(weight_box, self, "weight_input_data_10", "Input Beam 10 weight",
                                                    labelWidth=300, valueType=float, orientation="horizontal")


        self.le_weight_input_data_1.setEnabled(False)
        self.le_weight_input_data_2.setEnabled(False)
        self.le_weight_input_data_3.setEnabled(False)
        self.le_weight_input_data_4.setEnabled(False)
        self.le_weight_input_data_5.setEnabled(False)
        self.le_weight_input_data_6.setEnabled(False)
        self.le_weight_input_data_7.setEnabled(False)
        self.le_weight_input_data_8.setEnabled(False)
        self.le_weight_input_data_9.setEnabled(False)
        self.le_weight_input_data_10.setEnabled(False)

    @Inputs.shadow_data_1
    def set_shadow_data1(self, shadow_data: ShadowData):
        self.le_weight_input_data_1.setEnabled(False)
        self.input_data_1 = None

        if ShadowCongruence.check_empty_data(shadow_data):
            if ShadowCongruence.check_good_beam(shadow_data.beam):
                self.input_data_1 = shadow_data
                if self.use_weights==1: self.le_weight_input_data_1.setEnabled(True)
            else:
                QMessageBox.critical(self, "Error", "Data #1 not displayable: No good rays or bad content", QMessageBox.Ok)

    @Inputs.shadow_data_2
    def set_shadow_data2(self, shadow_data: ShadowData):
        self.le_weight_input_data_2.setEnabled(False)
        self.input_data_2 = None

        if ShadowCongruence.check_empty_data(shadow_data):
            if ShadowCongruence.check_good_beam(shadow_data.beam):
                self.input_data_2 = shadow_data
                if self.use_weights==1: self.le_weight_input_data_2.setEnabled(True)
            else:
                QMessageBox.critical(self, "Error", "Data #2 not displayable: No good rays or bad content", QMessageBox.Ok)

    @Inputs.shadow_data_3
    def set_shadow_data3(self, shadow_data: ShadowData):
        self.le_weight_input_data_3.setEnabled(False)
        self.input_data_3 = None

        if ShadowCongruence.check_empty_data(shadow_data):
            if ShadowCongruence.check_good_beam(shadow_data.beam):
                self.input_data_3  = shadow_data
                if self.use_weights==1: self.le_weight_input_data_3.setEnabled(True)
            else:
                QMessageBox.critical(self, "Error", "Data #3 not displayable: No good rays or bad content", QMessageBox.Ok)

    @Inputs.shadow_data_4
    def set_shadow_data4(self, shadow_data: ShadowData):
        self.le_weight_input_data_4.setEnabled(False)
        self.input_data_4 = None

        if ShadowCongruence.check_empty_data(shadow_data):
            if ShadowCongruence.check_good_beam(shadow_data.beam):
                self.input_data_4 = shadow_data
                if self.use_weights==1: self.le_weight_input_data_4.setEnabled(True)
            else:
                QMessageBox.critical(self, "Error", "Data #4 not displayable: No good rays or bad content", QMessageBox.Ok)

    @Inputs.shadow_data_5
    def set_shadow_data5(self, shadow_data: ShadowData):
        self.le_weight_input_data_5.setEnabled(False)
        self.input_data_5 = None

        if ShadowCongruence.check_empty_data(shadow_data):
            if ShadowCongruence.check_good_beam(shadow_data.beam):
                self.input_data_5 = shadow_data
                if self.use_weights==1: self.le_weight_input_data_5.setEnabled(True)
            else:
                QMessageBox.critical(self, "Error", "Data #5 not displayable: No good rays or bad content", QMessageBox.Ok)

    @Inputs.shadow_data_6
    def set_shadow_data6(self, shadow_data: ShadowData):
        self.le_weight_input_data_6.setEnabled(False)
        self.input_data_6 = None

        if ShadowCongruence.check_empty_data(shadow_data):
            if ShadowCongruence.check_good_beam(shadow_data.beam):
                self.input_data_6 = shadow_data
                if self.use_weights==1: self.le_weight_input_data_6.setEnabled(True)
            else:
                QMessageBox.critical(self, "Error", "Data #6 not displayable: No good rays or bad content", QMessageBox.Ok)

    @Inputs.shadow_data_7
    def set_shadow_data7(self, shadow_data: ShadowData):
        self.le_weight_input_data_7.setEnabled(False)
        self.input_data_7 = None

        if ShadowCongruence.check_empty_data(shadow_data):
            if ShadowCongruence.check_good_beam(shadow_data.beam):
                self.input_data_7 = shadow_data
                if self.use_weights==1: self.le_weight_input_data_7.setEnabled(True)
            else:
                QMessageBox.critical(self, "Error", "Data #7 not displayable: No good rays or bad content", QMessageBox.Ok)

    @Inputs.shadow_data_8
    def set_shadow_data8(self, shadow_data: ShadowData):
        self.le_weight_input_data_8.setEnabled(False)
        self.input_data_8 = None

        if ShadowCongruence.check_empty_data(shadow_data):
            if ShadowCongruence.check_good_beam(shadow_data.beam):
                self.input_data_8 = shadow_data
                if self.use_weights==1: self.le_weight_input_data_8.setEnabled(True)
            else:
                QMessageBox.critical(self, "Error", "Data #8 not displayable: No good rays or bad content", QMessageBox.Ok)

    @Inputs.shadow_data_9
    def set_shadow_data9(self, shadow_data: ShadowData):
        self.le_weight_input_data_9.setEnabled(False)
        self.input_data_9 = None

        if ShadowCongruence.check_empty_data(shadow_data):
            if ShadowCongruence.check_good_beam(shadow_data.beam):
                self.input_data_9 = shadow_data
                if self.use_weights==1: self.le_weight_input_data_9.setEnabled(True)
            else:
                QMessageBox.critical(self, "Error", "Data #9 not displayable: No good rays or bad content", QMessageBox.Ok)

    @Inputs.shadow_data_10
    def set_shadow_data10(self, shadow_data: ShadowData):
        self.le_weight_input_data_10.setEnabled(False)
        self.input_data_10 = None

        if ShadowCongruence.check_empty_data(shadow_data):
            if ShadowCongruence.check_good_beam(shadow_data.beam):
                self.input_data_10 = shadow_data
                if self.use_weights==1: self.le_weight_input_data_10.setEnabled(True)
            else:
                QMessageBox.critical(self, "Error", "Data #10 not displayable: No good rays or bad content", QMessageBox.Ok)

    def merge_data(self):
        try:
            merged_data = None

            for index in range(1, 11):
                current_data : ShadowData = getattr(self, "input_data" + str(index))
                if not current_data is None:
                    current_data = current_data.duplicate()

                    if self.use_weights == 1:
                        weight = getattr(self, "weight_input_data" + str(index))
                        if not (0.0 <= weight <= 1): raise ValueError(f"Weight #{index} is not in [0, 1]")

                        electric_field_factor = numpy.sqrt(weight)

                        current_data.beam.rays[:, 6]  *= electric_field_factor
                        current_data.beam.rays[:, 7]  *= electric_field_factor
                        current_data.beam.rays[:, 8]  *= electric_field_factor
                        current_data.beam.rays[:, 15] *= electric_field_factor
                        current_data.beam.rays[:, 16] *= electric_field_factor
                        current_data.beam.rays[:, 17] *= electric_field_factor

                        if not current_data.footprint is None:
                            current_data.footprint.rays[:, 6]  *= electric_field_factor
                            current_data.footprint.rays[:, 7]  *= electric_field_factor
                            current_data.footprint.rays[:, 8]  *= electric_field_factor
                            current_data.footprint.rays[:, 15] *= electric_field_factor
                            current_data.footprint.rays[:, 16] *= electric_field_factor
                            current_data.footprint.rays[:, 17] *= electric_field_factor

                    if    merged_data is None: merged_data = current_data
                    else: merged_data = ShadowData.merge_shadow_data(merged_data, current_data, which_flux=3, which_beamline=0)

            self.Outputs.shadow_data.send(merged_data)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e), QMessageBox.Ok)

            if self.IS_DEVELOP: raise e

    def set_UseWeights(self):
        self.le_weight_input_data_1.setEnabled( self.use_weights == 1 and not  self.input_data_1 is None)
        self.le_weight_input_data_2.setEnabled( self.use_weights == 1 and not  self.input_data_2 is None)
        self.le_weight_input_data_3.setEnabled( self.use_weights == 1 and not  self.input_data_3 is None)
        self.le_weight_input_data_4.setEnabled( self.use_weights == 1 and not  self.input_data_4 is None)
        self.le_weight_input_data_5.setEnabled( self.use_weights == 1 and not  self.input_data_5 is None)
        self.le_weight_input_data_6.setEnabled( self.use_weights == 1 and not  self.input_data_6 is None)
        self.le_weight_input_data_7.setEnabled( self.use_weights == 1 and not  self.input_data_7 is None)
        self.le_weight_input_data_8.setEnabled( self.use_weights == 1 and not  self.input_data_8 is None)
        self.le_weight_input_data_9.setEnabled( self.use_weights == 1 and not  self.input_data_9 is None)
        self.le_weight_input_data_10.setEnabled(self.use_weights == 1 and not  self.input_data_10 is None)


add_widget_parameters_to_module(__name__)
