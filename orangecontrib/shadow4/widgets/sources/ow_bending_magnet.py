import numpy

from orangewidget.settings import Setting
from orangewidget import gui as orangegui

from oasys2.widget import gui as oasysgui
from oasys2.widget.util import congruence
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from syned.storage_ring.magnetic_structures.bending_magnet import BendingMagnet

from shadow4.sources.bending_magnet.s4_bending_magnet import S4BendingMagnet
from shadow4.sources.bending_magnet.s4_bending_magnet_light_source import S4BendingMagnetLightSource

from orangecontrib.shadow4.widgets.gui.ow_synchrotron_source import OWSynchrotronSource
from orangecontrib.shadow4.widgets.gui.plots import plot_data1D

class OWBendingMagnet(OWSynchrotronSource):
    name = "Bending Magnet"
    description = "Shadow Source: Bending Magnet"
    icon = "icons/bending_magnet.png"
    priority = 3

    magnetic_field         = Setting(-1.26754)
    divergence             = Setting(69e-3)
    emin                   = Setting(1000.0)  # Photon energy scan from energy (in eV)
    emax                   = Setting(1000.1)  # Photon energy scan to energy (in eV)
    ng_e                   = Setting(100)     # Photon energy scan number of points

    plot_bm_graph = 1

    def __init__(self):
        super().__init__()

        tab_bas = oasysgui.createTabPage(self.tabs_control_area, "Bending Magnet")

        #
        box_1 = oasysgui.widgetBox(tab_bas, "Bending Magnet Parameters", addSpace=True, orientation="vertical")
        oasysgui.lineEdit(box_1, self, "emin", "Minimum Energy [eV]", tooltip="emin", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_1, self, "emax", "Maximum Energy [eV]", tooltip="emax", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_1, self, "magnetic_field", "Magnetic Field [T]", tooltip="magnetic_field", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_1, self, "divergence", "Horizontal divergence (arc of radius) [rads]", tooltip="divergence", labelWidth=260, valueType=float, orientation="horizontal")

        box_2 = oasysgui.widgetBox(tab_bas, "Sampling rays", addSpace=True, orientation="vertical")
        oasysgui.lineEdit(box_2, self, "number_of_rays", "Number of Rays", tooltip="Number of Rays", labelWidth=250, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(box_2, self, "seed", "Seed", tooltip="Seed (0=clock)", labelWidth=250, valueType=int, orientation="horizontal")


        # bm adv settings
        tab_advanced = oasysgui.createTabPage(self.tabs_control_area, "Advanced")

        box_3 = oasysgui.widgetBox(tab_advanced, "Advanced settings", addSpace=True, orientation="vertical")
        oasysgui.lineEdit(box_3, self, "ng_e", "Spectrum number of points", tooltip="ng_e", labelWidth=250, valueType=int, orientation="horizontal")

        self.add_specific_bm_plots()

        orangegui.rubber(self.controlArea)
        orangegui.rubber(self.mainArea)

    def add_specific_bm_plots(self):
        bm_plot_tab = oasysgui.widgetBox(self.main_tabs, addToLayout=0, margin=4)

        self.main_tabs.insertTab(1, bm_plot_tab, "BM Plots")

        view_box = oasysgui.widgetBox(bm_plot_tab, "Plotting Style", addSpace=False, orientation="horizontal")
        view_box_1 = oasysgui.widgetBox(view_box, "", addSpace=False, orientation="vertical", width=350)

        self.bm_view_type_combo = orangegui.comboBox(view_box_1, self,
                                            "plot_bm_graph",
                                                          label="Plot Graphs?",
                                                          labelWidth=220,
                                                          items=["No", "Yes"],
                                                          callback=self.refresh_specific_plots,
                                                          sendSelectedValue=False,
                                                          orientation="horizontal")

        self.bm_tab = []
        self.bm_tabs = oasysgui.tabWidget(bm_plot_tab)

        current_tab = self.bm_tabs.currentIndex()

        size = len(self.bm_tab)
        indexes = range(0, size)
        for index in indexes:
            self.bm_tabs.removeTab(size-1-index)

        self.bm_tab = [
            orangegui.createTabPage(self.bm_tabs, "BM Spectrum"),
            orangegui.createTabPage(self.bm_tabs, "BM Spectral power")
        ]

        for tab in self.bm_tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

        self.bm_plot_canvas = [None, None]

        self.bm_tabs.setCurrentIndex(current_tab)

    def refresh_specific_plots(self):
        if self.plot_bm_graph == 0:
            for bm_plot_slot_index in range(6):
                current_item = self.bm_tab[bm_plot_slot_index].layout().itemAt(0)
                self.bm_tab[bm_plot_slot_index].layout().removeItem(current_item)
                plot_widget_id = oasysgui.QLabel() # TODO: is there a better way to clean this??????????????????????
                self.bm_tab[bm_plot_slot_index].layout().addWidget(plot_widget_id)
        else:
            if self.light_source is None: return

            e, f, w = self.light_source.calculate_spectrum()

            self.plot_widget_item(e, f, 0,
                                  title="BM spectrum (current = %5.1f)"%self.ring_current,
                                  xtitle="Photon energy [eV]",ytitle=r"Photons/s/0.1%bw")

            self.plot_widget_item(e, w, 1,
                                  title="BM spectrum (current = %5.1f)"%self.ring_current,
                                  xtitle="Photon energy [eV]",ytitle="Spectral power [W/eV]")

    def plot_widget_item(self,x,y,bm_plot_slot_index,title="",xtitle="",ytitle=""):
        self.bm_tab[bm_plot_slot_index].layout().removeItem(self.bm_tab[bm_plot_slot_index].layout().itemAt(0))
        plot_widget_id = plot_data1D(x.copy(),y.copy(),title=title,xtitle=xtitle,ytitle=ytitle,symbol='.')
        self.bm_tab[bm_plot_slot_index].layout().addWidget(plot_widget_id)

    def check_magnetic_structure(self):
        congruence.checkNumber(self.magnetic_field, "Magnetic Field")
        congruence.checkStrictlyPositiveNumber(self.divergence, "Divergence")

    def build_light_source(self, electron_beam, flag_emittance):
        magnetic_radius = numpy.abs(S4BendingMagnet.calculate_magnetic_radius(self.magnetic_field, electron_beam.energy()))
        length          = numpy.abs(self.divergence * magnetic_radius)

        print(">>> calculated magnetic_radius = S4BendingMagnet.calculate_magnetic_radius(%f, %f) = %f" %\
              (self.magnetic_field, electron_beam.energy(), magnetic_radius))

        print(">>> calculated BM length = divergence * magnetic_radius = %f " % length)

        bm = S4BendingMagnet(magnetic_radius,
                             self.magnetic_field,
                             length,
                             emin=self.emin,  # Photon energy scan from energy (in eV)
                             emax=self.emax,  # Photon energy scan to energy (in eV)
                             ng_e=self.ng_e,  # Photon energy scan number of points
                             flag_emittance=flag_emittance,  # when sampling rays: Use emittance (0=No, 1=Yes)
                             )

        print("\n\n***** BM info: ", bm.info())

        # S4UndulatorLightSource
        try:    name = self.getNode().title
        except: name = "Bending Magnet"

        light_source = S4BendingMagnetLightSource(name=name,
                                                  electron_beam=electron_beam,
                                                  magnetic_structure=bm,
                                                  nrays=self.number_of_rays,
                                                  seed=self.seed)

        print("\n\n***** S4BendingMagnetLightSource info: ", light_source.info())

        return light_source

    def populate_fields_from_magnetic_structure(self, magnetic_structure, electron_beam):
        if isinstance(magnetic_structure, BendingMagnet):
            self.magnetic_field = magnetic_structure.magnetic_field()
            self.divergence     = magnetic_structure.horizontal_divergence()

add_widget_parameters_to_module(__name__)
