import sys

from orangewidget import gui
from orangewidget.settings import Setting
from orangewidget.widget import Input, Output

from oasys2.widget import gui as oasysgui
from oasys2.widget.widget import OWAction
from oasys2.widget.util.widget_util import EmittingStream
from oasys2.widget.gui import Styles
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module
from oasys2.widget.util.widget_objects import TriggerIn

from orangecontrib.shadow4.widgets.gui.ow_generic_element import GenericElement
from orangecontrib.shadow4.util.shadow4_util import TriggerToolsDecorator

from syned.widget.widget_decorator import WidgetDecorator

from shadow4.beamline.optical_elements.ideal_elements.s4_beam_movement import S4BeamMovement, S4BeamMovementElement
from shadow4.tools.logger import set_verbose

from orangecontrib.shadow4.util.shadow4_objects import ShadowData
from orangecontrib.shadow4.util.shadow4_util import ShadowCongruence

class OWBeamMovement(GenericElement, WidgetDecorator, TriggerToolsDecorator):
    name = "Beam movements"
    description = "Shadow Beam Movement"
    icon = "icons/beam_movement.png"
    priority = 10.1

    class Inputs:
        shadow_data = Input("Shadow Data", ShadowData, default=True, auto_summary=False)
        trigger     = TriggerToolsDecorator.get_trigger_input()
        syned_data  = WidgetDecorator.syned_input_data(multi_input=True)

    class Outputs:
        shadow_data = Output("Shadow Data", ShadowData, default=True, auto_summary=False)
        trigger = TriggerToolsDecorator.get_trigger_output()

    #########################################################
    # Position
    #########################################################
    apply_flag = Setting(1)
    translation_x  = Setting(0.0)
    translation_y  = Setting(0.0)
    translation_z  = Setting(0.0)
    rotation_x     = Setting(0.0)
    rotation_y     = Setting(0.0)
    rotation_z     = Setting(0.0)

    input_data = None
    beamline = None


    def __init__(self):
        super().__init__(show_automatic_box=True, has_footprint=False)

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


        self.tab_movement = oasysgui.createTabPage(self.tabs_control_area, "Movement")           # to be populated

        #
        # populate tabs with widgets
        #

        #########################################################
        # Position
        #########################################################
        self.populate_tab_movement()

        self.update_panels()
        #
        #
        #

        gui.rubber(self.controlArea)
        gui.rubber(self.mainArea)

    def resetSettings(self):
        self.translation_x = 0.0
        self.translation_y = 0.0
        self.translation_z = 0.0
        self.rotation_x = 0.0
        self.rotation_y = 0.0
        self.rotation_z = 0.0


    def populate_tab_movement(self):

        gui.comboBox(self.tab_movement, self, "apply_flag", label="Apply movements",
                     labelWidth=250, items=["Off", "On"], callback=self.update_panels,
                     sendSelectedValue=False, orientation="horizontal", tooltip="angles_respect_to")


        self.translation_box = oasysgui.widgetBox(self.tab_movement, "Translation", addSpace=True, orientation="vertical")
        self.rotation_box = oasysgui.widgetBox(self.tab_movement, "Rotation", addSpace=True, orientation="vertical")


        oasysgui.lineEdit(self.translation_box, self, "translation_x", "Translation along X [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="translation_x")
        oasysgui.lineEdit(self.translation_box, self, "translation_y", "Translation along Y [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="translation_y")
        oasysgui.lineEdit(self.translation_box, self, "translation_z", "Translation along Z [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="translation_z")

        oasysgui.lineEdit(self.rotation_box, self, "rotation_x", "1) Rotation along X [rad]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="rotation_x")
        oasysgui.lineEdit(self.rotation_box, self, "rotation_y", "2) Rotation along Y [rad]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="rotation_y")
        oasysgui.lineEdit(self.rotation_box, self, "rotation_z", "3) Rotation along Z [rad]", labelWidth=260,
                          valueType=float, orientation="horizontal", tooltip="rotation_z")


    def update_panels(self):

        if self.apply_flag:
            self.translation_box.setVisible(True)
            self.rotation_box.setVisible(True)
        else:
            self.translation_box.setVisible(False)
            self.rotation_box.setVisible(False)


    def get_oe_instance(self):
        return S4BeamMovement(
            apply_flag = self.apply_flag,
            translation_x = self.translation_x,
            translation_y = self.translation_y,
            translation_z = self.translation_z,
            rotation_x = self.rotation_x,
            rotation_y = self.rotation_y,
            rotation_z = self.rotation_z,
        )

    def get_element_instance(self):
        optical_element = S4BeamMovementElement()
        optical_element.set_optical_element(self.get_oe_instance())
        optical_element.set_input_beam(self.input_data.beam)
        return optical_element

    @Inputs.trigger
    def set_trigger_parameters_for_optics(self, trigger):
        super(OWBeamMovement, self).set_trigger_parameters_for_optics(trigger)

    @Inputs.shadow_data
    def set_shadow_data(self, input_data):
        self.not_interactive = self._check_not_interactive_conditions(input_data)

        self._on_receiving_input()

        if ShadowCongruence.check_empty_data(input_data):
            self.input_data = input_data.duplicate()
            if self.is_automatic_run: self.run_shadow4()

    @Inputs.syned_data
    def set_syned_data(self, index, syned_data):
        self.receive_syned_data(syned_data)

    @Inputs.syned_data.insert
    def insert_syned_data(self, index, syned_data):
        self.receive_syned_data(syned_data)

    @Inputs.syned_data.remove
    def remove_syned_data(self, index):
        pass

    def receive_syned_data(self, data): raise Exception("Not yet implemented")

    def run_shadow4(self):
        if self.input_data is None:
            self.prompt_exception(ValueError("No input beam"))
            return

        try:
            self.progressBarInit()
            set_verbose()
            self.shadow_output.setText("")

            sys.stdout = EmittingStream(textWritten=self._write_stdout)

            element = self.get_element_instance()
            print(element.info())

            output_beam, _ = element.trace_beam()

            beamline = self.input_data.beamline.duplicate()
            beamline.append_beamline_element(element)

            self._set_plot_quality()

            self._plot_results(output_beam, None, progressBarValue=80)

            self.progressBarFinished()

            #
            # script
            #
            script = beamline.to_python_code()
            script += "\n\n\n# test plot"
            script += "\nif True:"
            script += "\n   from srxraylib.plot.gol import plot_scatter"
            script += "\n   # plot_scatter(beam.get_photon_energy_eV(nolost=1), beam.get_column(23, nolost=1), title='(Intensity,Photon Energy)', plot_histograms=0)"
            script += "\n   plot_scatter(1e6 * beam.get_column(1, nolost=1), 1e6 * beam.get_column(3, nolost=1), title='(X,Z) in microns')"
            self.shadow4_script.set_code(script)

            #
            # send beam
            #
            self.Outputs.shadow_data.send(ShadowData(beam=output_beam, beamline=beamline))
            self.Outputs.trigger.send(TriggerIn(new_object=True))

        except Exception as exception:
            try:    self._initialize_tabs()
            except: pass
            self.prompt_exception(exception)


add_widget_parameters_to_module(__name__)

'''
if __name__ == "__main__":
    from shadow4.beamline.s4_beamline import S4Beamline
    def get_test_beam():
        # electron beam
        from shadow4.sources.s4_electron_beam import S4ElectronBeam
        electron_beam = S4ElectronBeam(energy_in_GeV=6, energy_spread=0.001, current=0.2)
        electron_beam.set_sigmas_all(sigma_x=3.01836e-05, sigma_y=3.63641e-06, sigma_xp=4.36821e-06,
                                     sigma_yp=1.37498e-06)

        # magnetic structure
        from shadow4.sources.undulator.s4_undulator_gaussian import S4UndulatorGaussian
        source = S4UndulatorGaussian(
            period_length=0.0164,  # syned Undulator parameter (length in m)
            number_of_periods=121.951,  # syned Undulator parameter
            photon_energy=11270,  # Photon energy (in eV)
            delta_e=0.0,  # Photon energy width (in eV)
            ng_e=100,  # Photon energy scan number of points
            flag_emittance=1,  # when sampling rays: Use emittance (0=No, 1=Yes)
            flag_energy_spread=0,  # when sampling rays: Use e- energy spread (0=No, 1=Yes)
            harmonic_number=1,  # harmonic number
            flag_autoset_flux_central_cone=0,  # value to set the flux peak
            flux_central_cone=10000000000.0,  # value to set the flux peak
        )

        # light source
        from shadow4.sources.undulator.s4_undulator_gaussian_light_source import S4UndulatorGaussianLightSource
        light_source = S4UndulatorGaussianLightSource(name='GaussianUndulator', electron_beam=electron_beam,
                                                      magnetic_structure=source, nrays=5000, seed=5676561)
        beam = light_source.get_beam()

        return ShadowData(beam=beam, beamline=S4Beamline(light_source=light_source))

    from AnyQt.QtWidgets import QApplication
    a = QApplication(sys.argv)
    ow = OWBeamMovement()
    ow.set_shadow_data(get_test_beam())
    ow.show()
    a.exec()
    ow.saveSettings()
'''