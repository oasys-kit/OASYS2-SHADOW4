from numba.core.types import NoneType
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from orangecontrib.shadow4.widgets.tools.ow_plot_xy import _PlotXY
from shadow4.beam.s4_beam import S4Beam


class PlotXYFootprint(_PlotXY):
    name = "Plot XY Footprint"
    description = "Display Data Tools: Plot XY Footprint"
    icon = "icons/footprint.png"
    priority = 1.2

    def __init__(self):
        super().__init__(allow_retrace=False)

    def get_beam_to_plot(self, return_str=False):
        if return_str: return "footprint"
        else:
            if isinstance(self.input_data.footprint, S4Beam): return self.input_data.footprint
            elif isinstance(self.input_data.footprint, list): return self.input_data.footprint[0]
            elif isinstance(self.input_data.footprint, type(None)): raise ValueError("No footprint available")
            else: raise ValueError("Input data must be of type S4Beam, list or None")

add_widget_parameters_to_module(__name__)

'''if __name__ == "__main__":
    import sys
    from AnyQt.QtWidgets import QApplication, QMessageBox
    from orangecontrib.shadow4.util.shadow4_objects import ShadowData


    def get_beamline():
        import numpy as np
        from dabax.dabax_xraylib import DabaxXraylib
        from shadow4.beamline.s4_beamline import S4Beamline

        beamline = S4Beamline()

        #
        #
        #
        from shadow4.sources.source_geometrical.source_geometrical import SourceGeometrical
        light_source = SourceGeometrical(name='Geometrical Source', nrays=5000, seed=5676561)
        light_source.set_spatial_type_point()
        light_source.set_depth_distribution_off()
        light_source.set_angular_distribution_uniform(hdiv1=-5e-09, hdiv2=5e-09, vdiv1=-5e-09, vdiv2=5e-09)
        light_source.set_energy_distribution_uniform(value_min=41000, value_max=49000, unit='eV')
        light_source.set_polarization(polarization_degree=1, phase_diff=0, coherent_beam=0)
        beam = light_source.get_beam()

        beamline.set_light_source(light_source)

        # test plot
        if 0:
            from srxraylib.plot.gol import plot_scatter
            plot_scatter(beam.get_photon_energy_eV(nolost=1), beam.get_column(23, nolost=1),
                         title='(Intensity,Photon Energy)', plot_histograms=0)
            plot_scatter(1e6 * beam.get_column(1, nolost=1), 1e6 * beam.get_column(3, nolost=1),
                         title='(X,Z) in microns')
        return beam, None, beamline
        ###############################


    beam, footprint, beamline = get_beamline()

    app = QApplication(sys.argv)
    w = PlotXYFootprint()
    w.set_shadow_data(ShadowData(beam=beam, footprint=footprint, number_of_rays=0, beamline=beamline))
    w.show()
    app.exec()'''

