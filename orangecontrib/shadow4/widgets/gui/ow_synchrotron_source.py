import sys
import time

from orangewidget.widget import Output
from orangewidget.settings import Setting

from oasys2.widget.util.widget_util import EmittingStream
from oasys2.widget.util import congruence

from syned.widget.widget_decorator import WidgetDecorator
from syned.beamline.beamline import Beamline

from orangecontrib.shadow4.widgets.gui.ow_electron_beam import OWElectronBeam
from orangecontrib.shadow4.util.shadow4_objects import ShadowData
from orangecontrib.shadow4.util.shadow4_util import TriggerToolsDecorator, TriggerIn

from shadow4.tools.logger import set_verbose
from shadow4.beamline.s4_beamline import S4Beamline

class OWSynchrotronSource(OWElectronBeam, WidgetDecorator, TriggerToolsDecorator):
    class Inputs:
        trigger     = TriggerToolsDecorator.get_trigger_input()
        syned_data  = WidgetDecorator.syned_input_data(multi_input=True)

    class Outputs:
        shadow_data = Output("Shadow Data", ShadowData, default=True, auto_summary=False)
        trigger     = TriggerToolsDecorator.get_trigger_output()

    # sampling rays
    number_of_rays = Setting(500)
    seed           = Setting(5676561)

    light_source = None

    def __init__(self, show_energy_spread=False):
        super().__init__(show_energy_spread=show_energy_spread)

    @Inputs.trigger
    def set_trigger_parameters_for_sources(self, trigger):
        super(OWSynchrotronSource, self).set_trigger_parameters_for_sources(trigger)

    @Inputs.syned_data
    def set_syned_data(self, index, syned_data):
        self.receive_syned_data(syned_data)

    @Inputs.syned_data.insert
    def insert_syned_data(self, index, syned_data):
        self.receive_syned_data(syned_data)

    @Inputs.syned_data.remove
    def remove_syned_data(self, index):
        pass

    def receive_syned_data(self, data):
        if data is not None:
            if isinstance(data, Beamline):
                light_source = data.get_light_source()
                if light_source is not None:
                    electron_beam      = light_source.get_electron_beam()
                    magnetic_structure = light_source.get_magnetic_structure()

                    if electron_beam is not None:      self.populate_fields_from_electron_beam(electron_beam) # from OWElectronBeam
                    if magnetic_structure is not None: self.populate_fields_from_magnetic_structure(magnetic_structure, electron_beam)

                    self.type_of_properties = 2 if self._check_dispersion_presence() else 1
                    self.set_TypeOfProperties()
                else:
                    raise ValueError("Syned data not correct: light source not present")
            else:
                raise ValueError("Syned data not correct: it must be Beamline()")

    def check_data(self):
        self.number_of_rays = congruence.checkPositiveNumber(self.number_of_rays, "Number of rays")
        self.seed           = congruence.checkPositiveNumber(self.seed, "Seed")

        self.check_electron_beam() # from OWElectronBeam
        self.check_magnetic_structure()

    def get_light_source(self):
        electron_beam = self.get_electron_beam() # from OWElectronBeam

        if not electron_beam is None: # None if user canceled operation

            if self.type_of_properties == 3: flag_emittance = 0
            else:                            flag_emittance = 1

            return self.build_light_source(electron_beam, flag_emittance)
        else:
            return None

    def run_shadow4(self, scanning_data: ShadowData.ScanningData = None):
        try:
            if not scanning_data: scanning_data = None

            self.check_data()

            light_source = self.get_light_source()

            if not light_source is None: # None if user has canceled the operation
                self.light_source = None
                set_verbose()
                self.shadow_output.setText("")
                sys.stdout = EmittingStream(textWritten=self._write_stdout)

                self._set_plot_quality()

                self.progressBarInit()

                #
                # script
                #
                script = light_source.to_python_code()
                script += "\n\n# test plot\nfrom srxraylib.plot.gol import plot_scatter"
                script += "\nrays = beam.get_rays()"
                script += "\nplot_scatter(1e6 * rays[:, 0], 1e6 * rays[:, 2], title='(X,Z) in microns')"
                self.shadow4_script.set_code(script)
                self.progressBarSet(5)

                # run shadow4
                t00 = time.time()
                print("\n\n***** S4LightSource info: ", light_source.info())
                print("***** starting calculation...")
                output_beam = light_source.get_beam()
                t11 = time.time() - t00
                print("***** time for %d rays: %f s, %f min, " % (self.number_of_rays, t11, t11 / 60))

                self.light_source = light_source

                #
                # plots
                #
                self._plot_results(output_beam, None, progressBarValue=80)
                self.refresh_specific_plots()


                #
                # send beam and trigger
                #
                output_data = ShadowData(beam=output_beam,
                                         number_of_rays=self.number_of_rays,
                                         beamline=S4Beamline(light_source=light_source))
                output_data.scanning_data = scanning_data

                self.Outputs.shadow_data.send(output_data)
                self.Outputs.trigger.send(TriggerIn(new_object=True))
        except Exception as exception:
            try:    self._initialize_tabs()
            except: pass
            self.prompt_exception(exception)
        finally:
            self.progressBarFinished()

    def build_light_source(self, electron_beam, flag_emittance): raise NotImplementedError
    def populate_fields_from_magnetic_structure(self, magnetic_structure, electron_beam): raise NotImplementedError
    def check_magnetic_structure(self): raise NotImplementedError
    def refresh_specific_plots(self): raise NotImplementedError
