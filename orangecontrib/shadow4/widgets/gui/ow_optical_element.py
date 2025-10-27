import numpy
import sys

from AnyQt.QtWidgets import QLabel, QSizePolicy
from AnyQt.QtGui import QPixmap
from AnyQt.QtCore import Qt

from orangewidget import gui
from orangewidget.settings import Setting
from orangewidget.widget import Input, Output
from oasys2.widget.widget import OWAction
from oasys2.widget import gui as oasysgui
from oasys2.widget.util.widget_util import EmittingStream
from oasys2.widget.gui import Styles

from syned.widget.widget_decorator import WidgetDecorator
from syned.beamline.element_coordinates import ElementCoordinates
from syned.beamline.beamline import Beamline

from shadow4.tools.logger import set_verbose

from orangecontrib.shadow4.widgets.gui.ow_generic_element import GenericElement
from orangecontrib.shadow4.util.shadow4_objects import ShadowData

from orangecontrib.shadow4.util.shadow4_util import ShadowCongruence, TriggerToolsDecorator
from oasys2.widget.util.widget_objects import TriggerIn

NO_FILE_SPECIFIED = "<specify file name>"
SUBTAB_INNER_BOX_WIDTH = 375

class OWOpticalElement(GenericElement, WidgetDecorator, TriggerToolsDecorator):

    class Inputs:
        shadow_data = Input("Shadow Data", ShadowData, default=True, auto_summary=False)
        trigger     = TriggerToolsDecorator.get_trigger_input()
        syned_data  = WidgetDecorator.syned_input_data(multi_input=True)

    class Outputs:
        shadow_data = Output("Shadow Data", ShadowData, default=True, auto_summary=False)
        trigger     = TriggerToolsDecorator.get_trigger_output()
        syned_data  = Output("Syned Data", Beamline, default=True, auto_summary=False)

    #########################################################
    # Position
    #########################################################
    source_plane_distance           = Setting(1.0)
    image_plane_distance            = Setting(1.0)
    angles_respect_to               = Setting(0)
    incidence_angle_deg             = Setting(88.8)
    incidence_angle_mrad            = Setting(0.0)
    reflection_angle_deg            = Setting(85.0)
    reflection_angle_mrad           = Setting(0.0)
    oe_orientation_angle            = Setting(0)
    oe_orientation_angle_user_value = Setting(0.0)

    def __init__(self, show_automatic_box=True, has_footprint=False, show_tab_advanced_settings=True, show_tab_help=False):
        super().__init__(show_automatic_box=show_automatic_box, has_footprint=has_footprint)

        #
        # main buttons
        #
        self.runaction = OWAction("Run Shadow4/Trace", self)
        self.runaction.triggered.connect(self.run_shadow4)
        self.addAction(self.runaction)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal", width=self.CONTROL_AREA_WIDTH-5)

        button = gui.button(button_box, self, "Run Shadow4/Trace", callback=self.run_shadow4)
        button.setStyleSheet(Styles.button_blue)

        button = gui.button(button_box, self, "Reset Fields", callback=self.call_reset_settings)
        button.setStyleSheet(Styles.button_red)

        #
        # tabs
        #
        self.tabs_control_area = oasysgui.tabWidget(self.controlArea)
        self.tabs_control_area.setFixedHeight(self.TABS_AREA_HEIGHT)
        self.tabs_control_area.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        self.tab_position          = oasysgui.createTabPage(self.tabs_control_area, "Position")           # to be populated
        self.tab_basic_settings    = oasysgui.createTabPage(self.tabs_control_area, "Basic Settings")
        if show_tab_advanced_settings:
            self.tab_advanced_settings = oasysgui.createTabPage(self.tabs_control_area, "Advanced Settings")
        if show_tab_help:
            self.tab_help = oasysgui.createTabPage(self.tabs_control_area, "Help")

        self.tabs_basic_settings   = oasysgui.tabWidget(self.tab_basic_settings)
        basic_setting_subtabs      = self.create_basic_settings_subtabs(self.tabs_basic_settings)

        if show_tab_advanced_settings:
            self.tabs_advanced_settings   = oasysgui.tabWidget(self.tab_advanced_settings)
            advanced_setting_subtabs = self.create_advanced_settings_subtabs(self.tabs_advanced_settings)

        #########################################################
        # Position
        #########################################################
        self.populate_tab_position(self.tab_position)

        #########################################################
        # Basic Settings
        #########################################################

        self.populate_basic_setting_subtabs(basic_setting_subtabs)

        #########################################################
        # Advanced Settings
        #########################################################
        if show_tab_advanced_settings:
            self.populate_advanced_setting_subtabs(advanced_setting_subtabs)

        #########################################################
        # Help
        #########################################################
        if show_tab_help:
            self.tab_help.setStyleSheet("background-color: white;")
            help_box = oasysgui.widgetBox(self.tab_help, "", addSpace=True, orientation="horizontal")

            label = QLabel("")
            label.setAlignment(Qt.AlignCenter | Qt.AlignTop)
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            label.setPixmap(QPixmap(self.help_path).scaledToWidth(self.CONTROL_AREA_WIDTH-20))

            help_box.layout().addWidget(label)

        gui.rubber(self.controlArea)
        gui.rubber(self.mainArea)

    def create_basic_settings_subtabs(self, tabs_basic_settings): return None
    def create_advanced_settings_subtabs(self, tabs_advanced_settings): return None

    def populate_basic_setting_subtabs(self, basic_setting_subtabs): pass
    def populate_advanced_setting_subtabs(self, advanced_setting_subtabs): pass

    def populate_tab_position(self, tab_position):
        self.orientation_box = oasysgui.widgetBox(tab_position, "Optical Element Orientation", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(self.orientation_box, self, "source_plane_distance", "Source Plane Distance [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="source_plane_distance")
        oasysgui.lineEdit(self.orientation_box, self, "image_plane_distance", "Image Plane Distance [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="image_plane_distance")

        gui.comboBox(self.orientation_box, self, "angles_respect_to", label="Angles in [deg] with respect to the",
                     labelWidth=250, items=["Normal", "Surface"], callback=self.set_angles_respect_to,
                     sendSelectedValue=False, orientation="horizontal", tooltip="angles_respect_to")

        self.incidence_angle_deg_le = oasysgui.lineEdit(self.orientation_box, self, "incidence_angle_deg",
                                                        "Incident Angle\nwith respect to the Normal [deg]",
                                                        labelWidth=220, callback=self.calculate_incidence_angle_mrad,
                                                        valueType=float, orientation="horizontal", tooltip="incidence_angle_deg")
        self.incidence_angle_rad_le = oasysgui.lineEdit(self.orientation_box, self, "incidence_angle_mrad",
                                                        "Incident Angle\nwith respect to the surface [mrad]",
                                                        labelWidth=220, callback=self.calculate_incidence_angle_deg,
                                                        valueType=float, orientation="horizontal", tooltip="incidence_angle_mrad")
        self.reflection_angle_deg_le = oasysgui.lineEdit(self.orientation_box, self, "reflection_angle_deg",
                                                         "Reflection Angle\nwith respect to the Normal [deg]",
                                                         labelWidth=220, callback=self.calculate_reflection_angle_mrad,
                                                         valueType=float, orientation="horizontal", tooltip="reflection_angle_deg")
        self.reflection_angle_rad_le = oasysgui.lineEdit(self.orientation_box, self, "reflection_angle_mrad",
                                                         "Reflection Angle\nwith respect to the surface [mrad]",
                                                         labelWidth=220, callback=self.calculate_reflection_angle_deg,
                                                         valueType=float, orientation="horizontal", tooltip="reflection_angle_mrad")

        self.set_angles_respect_to()

        self.calculate_incidence_angle_mrad()
        self.calculate_reflection_angle_mrad()

        gui.comboBox(self.orientation_box, self, "oe_orientation_angle", label="O.E. Orientation Angle [deg]",
                     labelWidth=390,
                     items=[0, 90, 180, 270, "Other value..."],
                     sendSelectedValue=False, orientation="horizontal", callback=self.oe_orientation_angle_user,
                     tooltip="oe_orientation_angle" )
        self.oe_orientation_angle_user_value_le = oasysgui.widgetBox(self.orientation_box, "", addSpace=False,
                                                                         orientation="vertical")
        oasysgui.lineEdit(self.oe_orientation_angle_user_value_le, self, "oe_orientation_angle_user_value",
                          "O.E. Orientation Angle [deg]",
                          labelWidth=220,
                          valueType=float, orientation="horizontal", tooltip="oe_orientation_angle_user_value")

        self.oe_orientation_angle_user()


    #########################################################
    # Position Methods
    #########################################################
    def set_angles_respect_to(self):
        label_1 = self.incidence_angle_deg_le.parent().layout().itemAt(0).widget()
        label_2 = self.reflection_angle_deg_le.parent().layout().itemAt(0).widget()

        if self.angles_respect_to == 0:
            label_1.setText("Incident Angle\nwith respect to the normal [deg]")
            label_2.setText("Reflection Angle\nwith respect to the normal [deg]")
        else:
            label_1.setText("Incident Angle\nwith respect to the surface [deg]")
            label_2.setText("Reflection Angle\nwith respect to the surface [deg]")

        self.calculate_incidence_angle_mrad()
        self.calculate_reflection_angle_mrad()

    def calculate_incidence_angle_mrad(self):
        digits = 7

        if self.angles_respect_to == 0: self.incidence_angle_mrad = numpy.round(numpy.radians(90-self.incidence_angle_deg)*1000, digits)
        else:                           self.incidence_angle_mrad = numpy.round(numpy.radians(self.incidence_angle_deg)*1000, digits)

    def calculate_reflection_angle_mrad(self):
        digits = 7
        if self.angles_respect_to == 0: self.reflection_angle_mrad = numpy.round(numpy.radians(90 - self.reflection_angle_deg)*1000, digits)
        else:                           self.reflection_angle_mrad = numpy.round(numpy.radians(self.reflection_angle_deg)*1000, digits)

    def calculate_incidence_angle_deg(self):
        digits = 10
        if self.angles_respect_to == 0: self.incidence_angle_deg = numpy.round(numpy.degrees(0.5 * numpy.pi - (self.incidence_angle_mrad / 1000)), digits)
        else:                           self.incidence_angle_deg = numpy.round(numpy.degrees(self.incidence_angle_mrad / 1000), digits)

    def calculate_reflection_angle_deg(self):
        digits = 10

        if self.angles_respect_to == 0: self.reflection_angle_deg = numpy.round(numpy.degrees(0.5*numpy.pi-(self.reflection_angle_mrad/1000)), digits)
        else:                           self.reflection_angle_deg = numpy.round(numpy.degrees(self.reflection_angle_mrad/1000), digits)

    def oe_orientation_angle_user(self):
        if self.oe_orientation_angle < 4: self.oe_orientation_angle_user_value_le.setVisible(False)
        else:                             self.oe_orientation_angle_user_value_le.setVisible(True)

    def get_oe_orientation_angle(self):
        if self.oe_orientation_angle == 0:   return 0.0
        elif self.oe_orientation_angle == 1: return 90.0
        elif self.oe_orientation_angle == 2: return 180.0
        elif self.oe_orientation_angle == 3: return 270.0
        elif self.oe_orientation_angle == 4: return self.oe_orientation_angle_user_value

    def get_coordinates_instance(self):
        if self.angles_respect_to == 0:
            angle_radial = numpy.radians(self.incidence_angle_deg)
            angle_radial_out = numpy.radians(self.reflection_angle_deg)
        elif self.angles_respect_to == 1:
            angle_radial = numpy.pi / 2 - self.incidence_angle_mrad * 1e-3
            angle_radial_out = numpy.pi / 2 - self.reflection_angle_mrad * 1e-3

        # angle_radial = numpy.pi / 2 - self.incidence_angle_mrad * 1e-3
        # angle_radial_out = numpy.pi / 2 - self.reflection_angle_mrad * 1e-3

        print(">> normal inc ref [deg]:", numpy.degrees(angle_radial), numpy.degrees(angle_radial_out), self.get_oe_orientation_angle())
        print(">> grazing inc ref [mrad]:", 1e3 * (numpy.pi / 2 - angle_radial), 1e3 * (numpy.pi / 2 - angle_radial_out))
        print(">> o.e. orientation angle [deg]:", self.get_oe_orientation_angle())

        return ElementCoordinates(
                p=self.source_plane_distance,
                q=self.image_plane_distance,
                angle_radial=angle_radial,
                angle_azimuthal=numpy.radians(self.get_oe_orientation_angle()),
                angle_radial_out=angle_radial_out,
                )

    @Inputs.shadow_data
    def set_shadow_data(self, input_data):
        self.not_interactive = self._check_not_interactive_conditions(input_data)

        self._on_receiving_input()

        if ShadowCongruence.check_empty_data(input_data):
            self.input_data = input_data.duplicate()
            if self.is_automatic_run: self.run_shadow4()

    @Inputs.trigger
    def set_trigger_parameters_for_optics(self, trigger):
        super(OWOpticalElement, self).set_trigger_parameters_for_optics(trigger)

    @Inputs.syned_data
    def set_syned_data(self, index, syned_data):
        self.receive_syned_data(syned_data)

    @Inputs.syned_data.insert
    def insert_syned_data(self, index, syned_data):
        self.receive_syned_data(syned_data)

    @Inputs.syned_data.remove
    def remove_syned_data(self, index):
        pass

    def run_shadow4(self, scanning_data: ShadowData.ScanningData = None):
        '''

        :param scanning_data: these data come from a direct loop attached to this oe, the method managing the trigger is sending them.
                              It is not None with a scanning variable or scanning file looper attached. Nested loops are not allowed, so if the
                              input_data attribute contains scanning_data (from a thermal loop, for example), they will be used and the parameter is ignored.
                              Nevertheless, in such a case, the scanning_data parameter, should be None.
        '''


        if self.input_data is None:
            self.prompt_exception(ValueError("No input beam"))
            return
        if not scanning_data: scanning_data = None # For some not yet understood problem, the variable is False by default instead of None.
        if not self.input_data.scanning_data is None: scanning_data = self.input_data.scanning_data # from a loop starting elsewhere

        try:
            set_verbose()
            self.shadow_output.setText("")

            sys.stdout = EmittingStream(textWritten=self._write_stdout)

            beamline = self.input_data.beamline.duplicate()
            element = self.get_beamline_element_instance()
            element.set_optical_element(self.get_optical_element_instance())
            element.set_coordinates(self.get_coordinates_instance())
            element.set_movements(self.get_movements_instance())
            element.set_input_beam(self.input_data.beam)

            print(element.info())

            beamline.append_beamline_element(element)

            #
            # script
            #
            script = beamline.to_python_code()
            script += "\n\n\n# test plot"
            script += "\nif True:"
            script += "\n   from srxraylib.plot.gol import plot_scatter"
            script += "\n   plot_scatter(beam.get_photon_energy_eV(nolost=1), beam.get_column(23, nolost=1), title='(Intensity,Photon Energy)', plot_histograms=0)"
            script += "\n   plot_scatter(1e6 * beam.get_column(1, nolost=1), 1e6 * beam.get_column(3, nolost=1), title='(X,Z) in microns')"
            self.shadow4_script.set_code(script)

            #
            # run
            #
            output_beam, footprint = element.trace_beam()

            self._post_trace_operations(output_beam, footprint, element, beamline)

            self._set_plot_quality()

            self.progressBarInit()

            self._plot_results(output_beam, footprint, progressBarValue=80)
            self._plot_additional_results(output_beam, footprint, element, beamline)

            #
            # send beam and trigger
            #
            output_data = ShadowData(beam=output_beam, beamline=beamline, footprint=footprint)
            output_data.scanning_data = scanning_data

            self.Outputs.shadow_data.send(output_data)
            self.Outputs.syned_data.send(beamline)
            self.Outputs.trigger.send(TriggerIn(new_object=True))

        except Exception as exception:
            try:    self._initialize_tabs()
            except: pass
            self.prompt_exception(exception)
        finally:
            self.progressBarFinished()

    def _post_trace_operations(self, output_beam, footprint, element, beamline): pass
    def _plot_additional_results(self, output_beam, footprint, element, beamline): pass

    def receive_syned_data(self, data): raise Exception("Not yet implemented")

    def get_optical_element_instance(self): raise NotImplementedError()
    def get_beamline_element_instance(self): raise NotImplementedError()
    def get_movements_instance(self): return None

