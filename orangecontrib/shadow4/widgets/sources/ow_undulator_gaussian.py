import numpy

from orangewidget.settings import Setting
from orangewidget import gui as orangegui

from oasys2.widget import gui as oasysgui
from oasys2.widget.util import congruence
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from syned.storage_ring.magnetic_structures.undulator import Undulator

from shadow4.sources.undulator.s4_undulator_gaussian import S4UndulatorGaussian
from shadow4.sources.undulator.s4_undulator_gaussian_light_source import S4UndulatorGaussianLightSource

from orangecontrib.shadow4.widgets.gui.ow_synchrotron_source import OWSynchrotronSource
from orangecontrib.shadow4.widgets.gui.plots import plot_data1D, plot_multi_data1D

class OWUndulatorGaussian(OWSynchrotronSource):
    name = "Undulator Gaussian"
    description = "Shadow Source: Undulator Gaussian"
    icon = "icons/ugaussian.png"
    priority = 5

    undulator_length = Setting(4.0)
    energy           = Setting(15000.0)
    delta_e          = Setting(0)

    plot_undulator_graph = Setting(1)

    # energy spread...
    harmonic_number = Setting(1)
    period_length = Setting(0.020)

    flag_autoset_flux_central_cone = Setting(0)
    flux_central_cone = Setting('1e10')
    plot_npoints = Setting(100)
    plot_Kmin = Setting(0.2)
    plot_Kmax = Setting(2.0)
    plot_max_harmonic_number = Setting(11)



    def __init__(self):
        self.__is_init = True

        super().__init__(show_energy_spread=True)

        tab_bas = oasysgui.createTabPage(self.tabs_control_area, "Undulator")

        #
        box_1 = oasysgui.widgetBox(tab_bas, "Undulator Parameters", addSpace=True, orientation="vertical")
        oasysgui.lineEdit(box_1, self, "undulator_length", "Undulator Length [m]", labelWidth=250, tooltip="undulator_length", valueType=float, orientation="horizontal")
        self.box_energy_spread_local = oasysgui.widgetBox(box_1, orientation="vertical")
        oasysgui.lineEdit(self.box_energy_spread_local, self, "period_length", "ID period [m]", labelWidth=260, tooltip="period_length", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_energy_spread_local, self, "harmonic_number", "Harmonic in use [odd]", labelWidth=250, tooltip="harmonic_number", valueType=int, orientation="horizontal")


        #
        box_2 = oasysgui.widgetBox(tab_bas, "Sampling rays", addSpace=True, orientation="vertical")
        oasysgui.lineEdit(box_2, self, "energy", "Set photon energy [eV]", tooltip="energy", labelWidth=250, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_2, self, "delta_e", "Delta Energy [eV]", tooltip="delta_e", labelWidth=250, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_2, self, "number_of_rays", "Number of Rays", tooltip="number_of_rays", labelWidth=250, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(box_2, self, "seed", "Seed", tooltip="seed", labelWidth=250, valueType=int, orientation="horizontal")

        #
        # advanced settings
        #
        tab_advanced = oasysgui.createTabPage(self.tabs_control_area, "Advanced")
        # arrays
        left_box_11 = oasysgui.widgetBox(tab_advanced, "Flux normalization", addSpace=False, orientation="vertical")

        orangegui.comboBox(left_box_11, self,
                           "flag_autoset_flux_central_cone",
                           label="Auto calculate central cone flux",
                           labelWidth=220,
                           items=["No", "Yes"],
                           callback=self.set_visibility,
                           sendSelectedValue=False,
                           orientation="horizontal")

        self.box_flux_central_cone = oasysgui.widgetBox(left_box_11, orientation="vertical")
        oasysgui.lineEdit(self.box_flux_central_cone, self, "flux_central_cone", "Set flux to [photons/s/0.1%bw]", tooltip="flux_central_cone",
                          labelWidth=250, valueType=str, orientation="horizontal")


        left_box_11 = oasysgui.widgetBox(tab_advanced, "Specific parameters for undulator plots", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(left_box_11, self, "plot_npoints", "Number of energy points", tooltip="plot_npoints",
                          labelWidth=250, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_11, self, "plot_Kmin", "Minimum K", tooltip="plot_Kmin",
                          labelWidth=250, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_11, self, "plot_Kmax", "Maximum K", tooltip="plot_Kmax",
                          labelWidth=250, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_11, self, "plot_max_harmonic_number", "Maximum harmonic number", tooltip="plot_max_harmonic_number",
                          labelWidth=250, valueType=int, orientation="horizontal")


        # undulator plots
        self.add_specific_undulator_plots()

        self.__is_init = False

        self.set_visibility()
        orangegui.rubber(self.controlArea)
        orangegui.rubber(self.mainArea)


    
    def set_TypeOfProperties(self):
        super(OWUndulatorGaussian, self).set_TypeOfProperties()

        if not self.__is_init: self.set_visibility_energy_spread()
    
    def set_visibility_energy_spread(self): # to be filled in the upper class
        self.box_energy_spread_local.setVisible(self.flag_energy_spread == 1)

    def set_visibility(self):
        self.box_flux_central_cone.setVisible(self.flag_autoset_flux_central_cone == 0)
        self.set_visibility_energy_spread()

    def add_specific_undulator_plots(self):
        undulator_plot_tab = oasysgui.widgetBox(self.main_tabs, addToLayout=0, margin=4)

        self.main_tabs.insertTab(1, undulator_plot_tab, "Undulator Plots")

        view_box = oasysgui.widgetBox(undulator_plot_tab, "Plotting Style", addSpace=False, orientation="horizontal")
        view_box_1 = oasysgui.widgetBox(view_box, "", addSpace=False, orientation="vertical", width=350)

        self.undulator_view_type_combo = orangegui.comboBox(view_box_1, self,
                                            "plot_undulator_graph",
                                                          label="Plot Graphs?",
                                                          labelWidth=220,
                                                          items=["No", "Yes"],
                                                          callback=self.refresh_specific_plots,
                                                          sendSelectedValue=False,
                                                          orientation="horizontal")

        self.undulator_tab = []
        self.undulator_tabs = oasysgui.tabWidget(undulator_plot_tab)

        current_tab = self.undulator_tabs.currentIndex()

        size = len(self.undulator_tab)
        indexes = range(0, size)
        for index in indexes:
            self.undulator_tabs.removeTab(size-1-index)

        self.undulator_tab = [
            orangegui.createTabPage(self.undulator_tabs, "Flux spectrum"),
            orangegui.createTabPage(self.undulator_tabs, "Spectral Power"),
            orangegui.createTabPage(self.undulator_tabs, "photon beam sizes"),
            orangegui.createTabPage(self.undulator_tabs, "photon beam divergences"),
        ]

        self.undulator_plot_canvas = [None, None, None, None]

        for tab in self.undulator_tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

        self.undulator_tabs.setCurrentIndex(current_tab)

    def plot_undulator_item1D(self, undulator_plot_slot_index, x, y, title="", xtitle="", ytitle="", symbol='.'):
        self.undulator_tab[undulator_plot_slot_index].layout().removeItem(self.undulator_tab[undulator_plot_slot_index].layout().itemAt(0))
        plot_widget_id = plot_data1D(x.copy(), y.copy(), title=title, xtitle=xtitle, ytitle=ytitle, symbol=symbol)
        self.undulator_tab[undulator_plot_slot_index].layout().addWidget(plot_widget_id)

    def plot_undulator_multi_data1D(self, undulator_plot_slot_index, x, y, title="", xtitle="", ytitle="", ytitles=[""], symbol='.'):
        self.undulator_tab[undulator_plot_slot_index].layout().removeItem(self.undulator_tab[undulator_plot_slot_index].layout().itemAt(0))
        plot_widget_id = plot_multi_data1D(x, y, title=title, xtitle=xtitle, ytitle=ytitle, ytitles=ytitles, flag_common_abscissas=0) #, symbol=symbol)
        self.undulator_tab[undulator_plot_slot_index].layout().addWidget(plot_widget_id)

    def refresh_specific_plots(self):
        if self.light_source is None: return

        if self.plot_undulator_graph == 0:
            for undulator_plot_slot_index in range(len(self.undulator_plot_canvas)):
                current_item = self.undulator_tab[undulator_plot_slot_index].layout().itemAt(0)
                self.undulator_tab[undulator_plot_slot_index].layout().removeItem(current_item)
                plot_widget_id = oasysgui.QLabel() # TODO: is there a better way to clean this??????????????????????
                self.undulator_tab[undulator_plot_slot_index].layout().addWidget(plot_widget_id)
        else:
            # spectra
            e, f, w = self.light_source.calculate_spectrum()
            self.plot_undulator_item1D(0, e, f,
                                  title="Undulator spectrum", xtitle="Photon energy [eV]", ytitle=r"Photons/s/0.1%bw")

            self.plot_undulator_item1D(1, e, w,
                                  title="Undulator spectral power",
                                  xtitle="Photon energy [eV]", ytitle="Spectral power [W/eV]")

            # size and divergence
            Energies, SizeH, SizeV, DivergenceH, DivergenceV, Labels = \
            self.light_source.get_size_and_divergence_vs_photon_energy(self.plot_Kmin, self.plot_Kmax,
                                                                      max_harmonic_number=self.plot_max_harmonic_number)

            Energies2 = numpy.concatenate((Energies, Energies))
            Sizes = numpy.concatenate((SizeH, SizeV))
            Divergences = numpy.concatenate((DivergenceH, DivergenceV))
            Labels2 = ["H " + item for item in Labels] + ["V " + item for item in Labels]

            self.plot_undulator_multi_data1D(2, Energies2, 1e6 * Sizes,
                                  title="Undulator size", xtitle="Photon energy [eV]", ytitle=r"Size (Sigma) [um]",
                                  ytitles=Labels2)

            self.plot_undulator_multi_data1D(3, Energies2, 1e6 * Divergences,
                                  title="Undulator divergence", xtitle="Photon energy [eV]", ytitle=r"Divergence angle (Sigma) [urad]",
                                  ytitles=Labels2)

    def check_magnetic_structure(self):
        self.energy = congruence.checkPositiveNumber(self.energy, "Energy")
        self.delta_e = congruence.checkPositiveNumber(self.delta_e, "Delta Energy")
        self.undulator_length = congruence.checkPositiveNumber(self.undulator_length, "Undulator Length")


    def build_light_source(self, electron_beam, flag_emittance):
        sourceundulator = S4UndulatorGaussian(
            period_length=self.period_length,  # syned Undulator parameter
            number_of_periods=self.undulator_length / self.period_length,  # syned Undulator parameter
            photon_energy=self.energy,
            delta_e=self.delta_e,
            ng_e=self.plot_npoints,  # Photon energy scan number of points
            flag_emittance=flag_emittance,  # when sampling rays: Use emittance (0=No, 1=Yes)
            flag_energy_spread=self.flag_energy_spread,
            harmonic_number=self.harmonic_number,
            flag_autoset_flux_central_cone=self.flag_autoset_flux_central_cone,
            flux_central_cone=float(self.flux_central_cone),
        )

        # S4UndulatorLightSource
        try:    name = self.getNode().title
        except: name = "Undulator gaussian"

        lightsource = S4UndulatorGaussianLightSource(name=name,
                                             electron_beam=electron_beam,
                                             magnetic_structure=sourceundulator,
                                             nrays=self.number_of_rays,
                                             seed=self.seed)

        print("\n\n***** S4UndulatorLightSource info: ", lightsource.info())

        return lightsource

    def populate_fields_from_magnetic_structure(self, magnetic_structure, electron_beam):
        if isinstance(magnetic_structure, Undulator):
            self.energy           = round(magnetic_structure.resonance_energy(electron_beam.gamma()))
            self.delta_e          = 0.0
            self.undulator_length = magnetic_structure.length()
            self.period_length    = magnetic_structure.period_length()
            self.plot_Kmax        = magnetic_structure.K_vertical()


add_widget_parameters_to_module(__name__)
