import os, sys
import numpy
from urllib.error import HTTPError


from AnyQt.QtWidgets import QLabel, QMessageBox, QSizePolicy
from AnyQt.QtGui import QTextCursor, QPixmap
from AnyQt.QtCore import Qt

import orangecanvas.resources as resources
from orangewidget import gui
from orangewidget.settings import Setting
from orangewidget.widget import Output

from oasys2.widget.widget import OWWidget, OWAction
from oasys2.widget import gui as oasysgui
from oasys2.widget.util import congruence
from oasys2.widget.util.widget_util import EmittingStream
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from orangecontrib.shadow4.util.shadow4_objects import BraggPreProcessorData
from orangecontrib.shadow4.util.python_script import PythonScript
from orangecontrib.shadow4.widgets.gui.plots import plot_data1D, plot_multi_data1D


from dabax.dabax_xraylib import DabaxXraylib
from dabax.dabax_files import dabax_f0_files, dabax_f1f2_files

from crystalpy.diffraction.GeometryType import BraggDiffraction
from crystalpy.diffraction.DiffractionSetupShadowPreprocessorV2 import DiffractionSetupShadowPreprocessorV2
from crystalpy.diffraction.Diffraction import Diffraction
from crystalpy.util.ComplexAmplitudePhotonBunch import ComplexAmplitudePhotonBunch
from crystalpy.util.ComplexAmplitudePhoton import ComplexAmplitudePhoton
from crystalpy.util.Vector import Vector
from crystalpy.util.Photon import Photon


from shadow4.physical_models.bragg.bragg import create_bragg_preprocessor_file_v2

XRAYLIB_AVAILABLE = True

try: import xraylib
except: XRAYLIB_AVAILABLE = False

class OWBragg(OWWidget):
    name = "Bragg (crystals)"
    id = "Bragg"
    description = "Calculation of crystal diffraction profile"
    icon = "icons/bragg.png"
    author = "create_widget.py"
    maintainer_email = "srio@esrf.eu"
    priority = 20
    category = ""
    keywords = ["oasys", "bragg"]

    class Outputs:
        preprocessor_data = Output("Bragg PreProcessor Data", BraggPreProcessorData, default=True, auto_summary=False)

    want_main_area = True

    DESCRIPTOR = Setting(0)
    H_MILLER_INDEX = Setting(1)
    K_MILLER_INDEX = Setting(1)
    L_MILLER_INDEX = Setting(1)
    TEMPERATURE_FACTOR = Setting(1.0)
    E_MIN = Setting(5000.0)
    E_MAX = Setting(15000.0)
    E_STEP = Setting(100.0)
    SHADOW_FILE = Setting("bragg.dat")

    PREPROCESSOR_FILE_VERSION = Setting(1)
    DESCRIPTOR_XRAYLIB = Setting(0)
    DESCRIPTOR_DABAX = Setting(0)
    DESCRIPTOR_XRAYSERVER = Setting(129)

    DABAX_F1F2_FILE_INDEX = Setting(0)
    DABAX_F0_FILE_INDEX = Setting(0)

    IMAGE_WIDTH  = 860
    IMAGE_HEIGHT = 545

    MAX_WIDTH          = 1320
    MAX_HEIGHT         = 720
    CONTROL_AREA_WIDTH = 405
    TABS_AREA_HEIGHT   = 615

    #
    # Plots
    #
    plot_flag = Setting(0)
    scan_e_n = Setting(100)
    scan_e_delta = Setting(10.0)

    scan_a_n = Setting(100)
    scan_a_delta = Setting(100)
    scan_e0 = Setting(10000.0)

    usage_path = os.path.join(resources.package_dirname("orangecontrib.shadow4.widgets.gui"), "misc", "bragg_usage.png")

    bragg_dict = None

    #crystalpy (plots)
    calculation_method = 1         # 0=Zachariasen, 1=Guigay
    calculation_strategy_flag = 2  # 0=mpmath 1=numpy 2=numpy-truncated

    def __init__(self):
        super().__init__()

        self.populate_crystal_lists()

        self.runaction = OWAction("Compute", self)
        self.runaction.triggered.connect(self.compute)
        self.addAction(self.runaction)

        self.setFixedWidth(self.MAX_WIDTH)
        self.setFixedHeight(self.MAX_HEIGHT)

        gui.separator(self.controlArea)

        box0 = oasysgui.widgetBox(self.controlArea, "",orientation="horizontal")
        button = gui.button(box0, self, "Compute", callback=self.compute)
        button.setFixedHeight(35)

        gui.separator(self.controlArea)

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        tab_bas = oasysgui.createTabPage(tabs_setting, "Crystal Settings")
        self.populate_crystal_settings(tab_bas)

        tab_input_advanced = oasysgui.createTabPage(tabs_setting, "Advanced")
        self.populate_tab_advanced(tab_input_advanced)

        tab_input_plot = oasysgui.createTabPage(tabs_setting, "Plots")
        self.populate_tab_plots(tab_input_plot)

        tab_usa = oasysgui.createTabPage(tabs_setting, "Use of the Widget")
        self.populate_tab_use_of_widget(tab_usa)

        #
        # main tabs
        #
        self.main_tabs = oasysgui.tabWidget(self.mainArea)
        tab_out = oasysgui.createTabPage(self.main_tabs, "Output")
        self.shadow_output = oasysgui.textArea()
        self.plot_tab = oasysgui.createTabPage(self.main_tabs, "Plots (optional scan)")

        out_box = oasysgui.widgetBox(tab_out, "System Output", orientation="horizontal", height=400)
        out_box.layout().addWidget(self.shadow_output)

        # script tab
        script_tab = oasysgui.createTabPage(self.main_tabs, "Script")
        self.shadow4_script = PythonScript()
        self.shadow4_script.code_area.setFixedHeight(400)

        script_box = gui.widgetBox(script_tab, "Python script", orientation="horizontal")
        script_box.layout().addWidget(self.shadow4_script)


        self.process_showers()

        gui.rubber(self.controlArea)

    def populate_crystal_lists(self):
        dx1 = DabaxXraylib(file_Crystals="Crystals.dat",
                           file_f0=dabax_f1f2_files()[self.DABAX_F0_FILE_INDEX],
                           file_f1f2=dabax_f1f2_files()[self.DABAX_F1F2_FILE_INDEX],
                           )
        try: list1 = dx1.Crystal_GetCrystalsList()
        except HTTPError as e: # Anti-bot policies can block this call
            if "UserAgentBlocked" in str(e): list1 = {}
            else: raise e
        self.crystals_dabax = list1

        dx2 = DabaxXraylib(file_Crystals="Crystals_xrayserver.dat",
                           file_f0=dabax_f1f2_files()[self.DABAX_F0_FILE_INDEX],
                           file_f1f2=dabax_f1f2_files()[self.DABAX_F1F2_FILE_INDEX],
                           )
        try: list2 = dx2.Crystal_GetCrystalsList()
        except HTTPError as e: # Anti-bot policies can block this call
            if "UserAgentBlocked" in str(e): list2 = {}
            else: raise e
        self.crystals_xrayserver = list2

        if XRAYLIB_AVAILABLE:
            list3 = xraylib.Crystal_GetCrystalsList()
        else:
            list3 = []
        self.crystals_xraylib = list3


    def populate_tab_use_of_widget(self, tab_usa):
        tab_usa.setStyleSheet("background-color: white;")
        usage_box = oasysgui.widgetBox(tab_usa, "", orientation="horizontal")
        label = QLabel("")
        label.setAlignment(Qt.AlignCenter)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        label.setPixmap(QPixmap(self.usage_path))
        usage_box.layout().addWidget(label)

    def populate_tab_advanced(self, tab_dabax):
        # calculation
        box1 = gui.widgetBox(tab_dabax, "Calculation flags")
        gui.comboBox(box1, self, "calculation_method",
                     label="calculation method",
                     items=["Zachariasen", "Guigay"],
                     orientation="horizontal")
        gui.comboBox(box1, self, "calculation_strategy_flag",
                     label="evaluation library",
                     items=["mpmath", "numpy", "numpy-truncated"],
                     orientation="horizontal")

        # xraylib/dabax
        # widget index xx
        self.dabax_box = gui.widgetBox(tab_dabax)

        box1 = gui.widgetBox(self.dabax_box, "DABAX Material library")

        gui.comboBox(box1, self, "DABAX_F0_FILE_INDEX",
                     label="dabax f0 file",
                     items=dabax_f0_files(),
                     orientation="horizontal")

        gui.comboBox(box1, self, "DABAX_F1F2_FILE_INDEX",
                     label="dabax f1f2 file",
                     items=dabax_f1f2_files(),
                     orientation="horizontal")

    def populate_tab_plots(self, tab_plots):
        box = gui.widgetBox(tab_plots, "Optional scan plots", orientation="vertical")

        gui.comboBox(box, self, "plot_flag", tooltip="plot_flag",
                     label="Scan plot",
                     items=['No', 'energy-scan', 'grazing angle-scan'],
                     orientation="horizontal", labelWidth=270, callback=self.do_plots)

        self.box_plots = gui.widgetBox(tab_plots, "Optional scan plots", orientation="vertical")

        self.box_plot_e = oasysgui.widgetBox(self.box_plots, "", orientation="horizontal")
        oasysgui.lineEdit(self.box_plot_e, self, "scan_e_delta", label="delta [eV]", tooltip="scan_e_delta",
                          valueType=float, labelWidth=100, orientation="horizontal",
                          callback=self.do_plots)
        oasysgui.lineEdit(self.box_plot_e, self, "scan_e_n", label="points", tooltip="scan_e_n",
                          valueType=int, labelWidth=50, orientation="horizontal",
                          callback=self.do_plots)

        self.box_plot_a = oasysgui.widgetBox(self.box_plots, "", orientation="horizontal")
        oasysgui.lineEdit(self.box_plot_a, self, "scan_a_delta", label="delta [urad]", tooltip="scan_a_delta",
                          valueType=float, labelWidth=100, orientation="horizontal",
                          callback=self.do_plots)
        oasysgui.lineEdit(self.box_plot_a, self, "scan_a_n", label="points", tooltip="scan_a_n",
                          valueType=int, labelWidth=50, orientation="horizontal",
                          callback=self.do_plots)

        self.box_plot_e0 = oasysgui.widgetBox(self.box_plots, "", orientation="horizontal")
        oasysgui.lineEdit(self.box_plot_e0, self, "scan_e0", label="Center energy E0 [eV]", tooltip="scan_e0",
                          valueType=float, labelWidth=200, orientation="horizontal",
                          callback=self.do_plots)

    def populate_crystal_settings(self, tab_bas):
        #
        # basic settings
        #
        idx = -1

        box = oasysgui.widgetBox(tab_bas, "Crystal Parameters", orientation="vertical")

        # widget index -0.1
        idx += 1
        gui.comboBox(box, self, "PREPROCESSOR_FILE_VERSION", tooltip="PREPROCESSOR_FILE_VERSION",
                     label=self.unitLabels()[idx],
                     items=[
                         "xraylib " + ("**NOT AVAILABLE**" if not XRAYLIB_AVAILABLE else ""),
                         "DABAX (default list)",
                         "DABAX (XRayServer list)",
                     ],
                     sendSelectedValue=False,
                     orientation="horizontal", labelWidth=350,
                     callback=self.set_visibility)
        self.show_at(self.unitFlags()[idx], box)

        # widget index 0.1
        idx += 1
        box1 = oasysgui.widgetBox(box, "", orientation="vertical")
        gui.comboBox(box1, self, "DESCRIPTOR_XRAYLIB", tooltip="DESCRIPTOR_XRAYLIB",
                     label=self.unitLabels()[idx],
                     items=self.crystals_xraylib, sendSelectedValue=False,
                     orientation="horizontal", labelWidth=350)
        self.show_at(self.unitFlags()[idx], box1)


        # widget index 0.2
        idx += 1
        box2 = oasysgui.widgetBox(box, "", orientation="vertical")
        gui.comboBox(box2, self, "DESCRIPTOR_DABAX", tooltip="DESCRIPTOR_DABAX",
                     label=self.unitLabels()[idx],
                     items=self.crystals_dabax, sendSelectedValue=False,
                     orientation="horizontal", labelWidth=350)
        self.show_at(self.unitFlags()[idx], box2)

        # widget index 0.3
        idx += 1
        box3 = oasysgui.widgetBox(box, "", orientation="vertical")
        gui.comboBox(box3, self, "DESCRIPTOR_XRAYSERVER", tooltip="DESCRIPTOR_XRAYSERVER",
                     label=self.unitLabels()[idx],
                     items=self.crystals_xrayserver, sendSelectedValue=False,
                     orientation="horizontal", labelWidth=350)
        self.show_at(self.unitFlags()[idx], box3)

        # widget index 1
        idx += 1
        box_miller = oasysgui.widgetBox(box, "", orientation="horizontal")
        oasysgui.lineEdit(box_miller, self, "H_MILLER_INDEX", tooltip="H_MILLER_INDEX",
                          label="Miller Indices [h k l]",
                          valueType=int, labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box_miller)

        # widget index 2
        idx += 1
        oasysgui.lineEdit(box_miller, self, "K_MILLER_INDEX", tooltip="K_MILLER_INDEX",
                          valueType=int)
        self.show_at(self.unitFlags()[idx], box)

        # widget index 3
        idx += 1
        oasysgui.lineEdit(box_miller, self, "L_MILLER_INDEX", tooltip="L_MILLER_INDEX",
                          valueType=int, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        gui.separator(box)

        # widget index 4
        idx += 1
        oasysgui.lineEdit(box, self, "TEMPERATURE_FACTOR", tooltip="TEMPERATURE_FACTOR",
                          label=self.unitLabels()[idx],
                          valueType=float, labelWidth=200, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        # widget index 5
        idx += 1
        oasysgui.lineEdit(box, self, "E_MIN", tooltip="E_MIN",
                          label=self.unitLabels()[idx],
                          valueType=float, labelWidth=200, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        # widget index 6
        idx += 1
        oasysgui.lineEdit(box, self, "E_MAX", tooltip="E_MAX",
                          label=self.unitLabels()[idx],
                          valueType=float, labelWidth=200, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        # widget index 7
        idx += 1
        oasysgui.lineEdit(box, self, "E_STEP", tooltip="E_STEP",
                          label=self.unitLabels()[idx],
                          valueType=float, labelWidth=200, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        # widget index 8
        idx += 1
        box_2 = oasysgui.widgetBox(box, "", orientation="horizontal")

        self.le_SHADOW_FILE = oasysgui.lineEdit(box_2, self, "SHADOW_FILE", tooltip="SHADOW_FILE",
                                                label=self.unitLabels()[idx], labelWidth=180,
                                                orientation="horizontal")

        gui.button(box_2, self, "...", callback=self.selectFile)

        self.show_at(self.unitFlags()[idx], box)

    def unitLabels(self):
         return ['Materials library','Crystal descriptor [xraylib]','Crystal descriptor [DABAX]','Crystal descriptor [XRayServer]','H miller index','K miller index','L miller index','Temperature factor','Minimum energy [eV]','Maximum energy [eV]','Energy step [eV]','File name (for SHADOW)']

    def unitFlags(self):
         return ['True','self.PREPROCESSOR_FILE_VERSION == 0','self.PREPROCESSOR_FILE_VERSION == 1','self.PREPROCESSOR_FILE_VERSION == 2','True','True','True','True','True','True','True','True']

    def selectFile(self):
        self.le_SHADOW_FILE.setText(oasysgui.selectFileFromDialog(self, self.SHADOW_FILE, "Select Output File"))

    def set_visibility(self):
        if self.PREPROCESSOR_FILE_VERSION == 0:
            self.dabax_box.setVisible(False)
        else:
            self.dabax_box.setVisible(True)

        self.box_plots.setVisible(self.plot_flag > 0)
        if self.plot_flag == 1:
            self.box_plot_e.setVisible(True)
            self.box_plot_a.setVisible(False)
            self.box_plot_e0.setVisible(True)
        elif self.plot_flag == 2:
            self.box_plot_e.setVisible(False)
            self.box_plot_a.setVisible(True)
            self.box_plot_e0.setVisible(True)

    def compute(self):
        try:
            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            self.checkFields()

            if self.PREPROCESSOR_FILE_VERSION == 0:
                descriptor=self.crystals_dabax[self.DESCRIPTOR_DABAX]
                material_constants_library = xraylib
                script_0 = "import xraylib\n"
                script_0 += "from shadow4.physical_models.bragg.bragg import create_bragg_preprocessor_file_v2\n"
                script_0 += "material_constants_library=xraylib\n"
            elif self.PREPROCESSOR_FILE_VERSION == 1:
                descriptor=self.crystals_dabax[self.DESCRIPTOR_DABAX]
                material_constants_library = DabaxXraylib(file_Crystals="Crystals.dat",
                                                          file_f0=dabax_f1f2_files()[self.DABAX_F0_FILE_INDEX],
                                                          file_f1f2=dabax_f1f2_files()[self.DABAX_F1F2_FILE_INDEX],
                                                          )
                script_0 = "from dabax.dabax_xraylib import DabaxXraylib\n"
                script_0 += "from shadow4.physical_models.bragg.bragg import create_bragg_preprocessor_file_v2\n"
                script_0 += "material_constants_library=DabaxXraylib(file_Crystals='Crystals.dat', file_f0='%s', file_f1f2='%s')\n" % \
                            (dabax_f0_files()[self.DABAX_F0_FILE_INDEX], dabax_f1f2_files()[self.DABAX_F1F2_FILE_INDEX])
            elif self.PREPROCESSOR_FILE_VERSION == 2:
                descriptor = self.crystals_xrayserver[self.DESCRIPTOR_XRAYSERVER]
                material_constants_library = DabaxXraylib(file_Crystals="Crystals_xrayserver.dat",
                                                          file_f0=dabax_f1f2_files()[self.DABAX_F0_FILE_INDEX],
                                                          file_f1f2=dabax_f1f2_files()[self.DABAX_F1F2_FILE_INDEX],
                                                          )
                script_0 = "from dabax.dabax_xraylib import DabaxXraylib\n"
                script_0 += "from shadow4.physical_models.bragg.bragg import create_bragg_preprocessor_file_v2\n"
                script_0 += "material_constants_library=DabaxXraylib(file_Crystals='Crystals_xrayserver.dat', file_f0='%s', file_f1f2='%s')\n" % \
                            (dabax_f0_files()[self.DABAX_F0_FILE_INDEX], dabax_f1f2_files()[self.DABAX_F1F2_FILE_INDEX])

            self.bragg_dict = create_bragg_preprocessor_file_v2(interactive=False,
                                              DESCRIPTOR=descriptor,
                                              H_MILLER_INDEX=self.H_MILLER_INDEX,
                                              K_MILLER_INDEX=self.K_MILLER_INDEX,
                                              L_MILLER_INDEX=self.L_MILLER_INDEX,
                                              TEMPERATURE_FACTOR=self.TEMPERATURE_FACTOR,
                                              E_MIN=self.E_MIN,
                                              E_MAX=self.E_MAX,
                                              E_STEP=self.E_STEP,
                                              SHADOW_FILE=congruence.checkFileName(self.SHADOW_FILE),
                                              material_constants_library=material_constants_library,
                                              )

            self.Outputs.preprocessor_data.send(BraggPreProcessorData(bragg_data_file=self.SHADOW_FILE))
            script_plot = self.do_plots()

            # script
            dict = {
            "script_0"           : script_0,
            "descriptor"         : descriptor,
            "H_MILLER_INDEX"     : self.H_MILLER_INDEX,
            "K_MILLER_INDEX"     : self.K_MILLER_INDEX,
            "L_MILLER_INDEX"     : self.L_MILLER_INDEX,
            "TEMPERATURE_FACTOR" : self.TEMPERATURE_FACTOR,
            "E_MIN"              : self.E_MIN,
            "E_MAX"              : self.E_MAX,
            "E_STEP"             : self.E_STEP,
            "SHADOW_FILE"        : self.SHADOW_FILE,
            "plot_flag"          : self.plot_flag,
            "scan_e_n"           : self.scan_e_n,
            "scan_e_delta"       : self.scan_e_delta,
            "scan_a_n"           : self.scan_a_n,
            "scan_a_delta"       : self.scan_a_delta,
            "scan_e0"            : self.scan_e0,
            "calculation_method" : self.calculation_method,
            "calculation_strategy_flag" : self.calculation_strategy_flag,
            }

            script = (self.get_script_template() + script_plot).format_map(dict)
            self.shadow4_script.set_code(script)

        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)
            if self.IS_DEVELOP: raise exception

    def get_script_template(self):
        return """# script to create the bragg preprocessor file (for crystals)
{script_0}

bragg_dict = create_bragg_preprocessor_file_v2(interactive=False,
                DESCRIPTOR='{descriptor}',
                H_MILLER_INDEX={H_MILLER_INDEX},
                K_MILLER_INDEX={K_MILLER_INDEX},
                L_MILLER_INDEX={L_MILLER_INDEX},
                TEMPERATURE_FACTOR={TEMPERATURE_FACTOR},
                E_MIN={E_MIN},
                E_MAX={E_MAX},
                E_STEP={E_STEP},
                SHADOW_FILE='{SHADOW_FILE}',
                material_constants_library=material_constants_library,
                )
"""

    def checkFields(self):
        self.H_MILLER_INDEX = congruence.checkNumber(self.H_MILLER_INDEX, "H miller index")
        self.K_MILLER_INDEX = congruence.checkNumber(self.K_MILLER_INDEX, "K miller index")
        self.L_MILLER_INDEX = congruence.checkNumber(self.L_MILLER_INDEX, "L miller index")
        self.TEMPERATURE_FACTOR = congruence.checkNumber(self.TEMPERATURE_FACTOR, "Temperature factor")
        self.E_MIN  = congruence.checkPositiveNumber(self.E_MIN , "Minimum energy")
        self.E_MAX  = congruence.checkStrictlyPositiveNumber(self.E_MAX , "Maximum Energy")
        self.E_STEP = congruence.checkStrictlyPositiveNumber(self.E_STEP, "Energy step")
        congruence.checkLessOrEqualThan(self.E_MIN, self.E_MAX, "From Energy", "To Energy")
        congruence.checkDir(self.SHADOW_FILE)

    def do_plots(self):

        script_plots = ""

        if self.plot_flag > 0:
            #
            #
            #
            print("\nCreating a diffraction setup (shadow preprocessor file V2)...")
            diffraction_setup = DiffractionSetupShadowPreprocessorV2(geometry_type=BraggDiffraction(),
                                                 crystal_name="",  # string
                                                 thickness=1e-2,  # meters
                                                 miller_h=self.H_MILLER_INDEX,          # int
                                                 miller_k=self.K_MILLER_INDEX,          # int
                                                 miller_l=self.L_MILLER_INDEX,          # int
                                                 asymmetry_angle=0.0,  # radians
                                                 azimuthal_angle=0.0,
                                                 preprocessor_file=self.SHADOW_FILE)

            script_plots += """#
# plot (optional)
#
import numpy
from crystalpy.diffraction.GeometryType import BraggDiffraction
from crystalpy.diffraction.DiffractionSetupShadowPreprocessorV2 import DiffractionSetupShadowPreprocessorV2
from crystalpy.diffraction.Diffraction import Diffraction
from crystalpy.util.ComplexAmplitudePhotonBunch import ComplexAmplitudePhotonBunch
from crystalpy.util.ComplexAmplitudePhoton import ComplexAmplitudePhoton
from crystalpy.util.Vector import Vector
from crystalpy.util.Photon import Photon

print("Creating a diffraction setup (shadow preprocessor file V2)...")
diffraction_setup = DiffractionSetupShadowPreprocessorV2(geometry_type=BraggDiffraction(),
                         crystal_name="",  # string
                         thickness=1e-2,  # meters
                         miller_h={H_MILLER_INDEX},          # int
                         miller_k={K_MILLER_INDEX},          # int
                         miller_l={L_MILLER_INDEX},          # int
                         asymmetry_angle=0.0,  # radians
                         azimuthal_angle=0.0,
                         preprocessor_file='{SHADOW_FILE}',
                         )
                         
"""

        self.set_visibility()
        if self.bragg_dict is None: self.compute()
        self.plot_tab.layout().removeItem(self.plot_tab.layout().itemAt(0))

        if self.plot_flag == 0:
            plot_widget_id = plot_data1D([0], [0], xtitle="", ytitle="")
        elif self.plot_flag == 1:
            #
            e_from, e_to = self.scan_e0 - 0.5 * self.scan_e_delta, self.scan_e0 + 0.5 * self.scan_e_delta
            energies = numpy.linspace(e_from, e_to, self.scan_e_n)
            scan = numpy.zeros_like(energies, dtype=float)
            intensityS = numpy.zeros_like(scan, dtype=float)
            intensityP = numpy.zeros_like(scan, dtype=float)
            bragg_angle = diffraction_setup.angleBragg(self.scan_e0)
            print("Bragg angle for E=%f eV is %f deg" % (self.scan_e0, bragg_angle * 180.0 / numpy.pi))
            for i, energy in enumerate(energies):
                # calculate the components of the unitary vector of the incident photon scan. Diffraction plane is YZ
                direction_vector = Vector(0.0, numpy.cos(bragg_angle), - numpy.abs(numpy.sin(bragg_angle)))
                photon = Photon(energy_in_ev=energy, direction_vector=direction_vector)
                coeffs_r = Diffraction.calculateDiffractedComplexAmplitudes(diffraction_setup, photon,
                            is_thick=1, calculation_method=self.calculation_method, calculation_strategy_flag=self.calculation_strategy_flag)
                intensityS[i] = (numpy.abs(coeffs_r["S"]) ** 2).item()
                intensityP[i] = (numpy.abs(coeffs_r["P"]) ** 2).item()
            #

            plot_widget_id = plot_multi_data1D(energies - self.scan_e0, [intensityS, intensityP], xtitle="Photon energy E-E0 [eV]",
                                ytitle="Reflectivity", ytitles=['S-polarized','P-polarized'])

            script_plots += """
#
scan_e0, scan_e_delta = {scan_e0}, {scan_e_delta}
energies = numpy.linspace(scan_e0 - 0.5 * scan_e_delta, scan_e0 + 0.5 * scan_e_delta, {scan_e_n})
scan = numpy.zeros_like(energies, dtype=float)
intensityS = numpy.zeros_like(scan, dtype=float)
intensityP = numpy.zeros_like(scan, dtype=float)
bragg_angle = diffraction_setup.angleBragg(scan_e0)
print("Bragg angle for E=%f eV is %f deg" % (scan_e0, bragg_angle * 180.0 / numpy.pi))
for i, energy in enumerate(energies):
    # calculate the components of the unitary vector of the incident photon scan. Diffraction plane is YZ
    direction_vector = Vector(0.0, numpy.cos(bragg_angle), - numpy.abs(numpy.sin(bragg_angle)))
    photon = Photon(energy_in_ev=energy, direction_vector=direction_vector)
    coeffs_r = Diffraction.calculateDiffractedComplexAmplitudes(diffraction_setup,
                photon, is_thick=1,
                calculation_method={calculation_method}, # 0=Zachariasen, 1=Guigay
                calculation_strategy_flag={calculation_strategy_flag}, # 0=mpmath, 1=numpy, 2=numpy-truncated
                )
    intensityS[i] = numpy.abs(coeffs_r["S"]) ** 2
    intensityP[i] = numpy.abs(coeffs_r["P"]) ** 2
#
from srxraylib.plot.gol import plot
plot(energies - scan_e0, intensityS, energies - scan_e0, intensityP, title="E0 = %.3f eV" % scan_e0, xtitle="Photon energy E-E0 [eV]", ytitle="Reflectivity", legend=['S-polarized','P-polarized'])
"""
        elif self.plot_flag == 2:
            #
            angle_deviation_min = -0.5 * self.scan_a_delta * 1e-6  # radians
            angle_deviation_max = 0.5 * self.scan_a_delta * 1e-6  # radians
            angle_deviation_points = self.scan_a_n
            angle_step = (angle_deviation_max - angle_deviation_min) / angle_deviation_points
            bragg_angle = diffraction_setup.angleBragg(self.scan_e0)
            print("Bragg angle for E=%f eV is %f deg" % (self.scan_e0, bragg_angle * 180.0 / numpy.pi))
            deviations = numpy.zeros(angle_deviation_points)
            bunch_in = ComplexAmplitudePhotonBunch()
            K0 = diffraction_setup.vectorK0(self.scan_e0)
            K0unitary = K0.getNormalizedVector()
            for ia in range(angle_deviation_points):
                deviation = angle_deviation_min + ia * angle_step
                # minus sign in angle is to perform cw rotation when deviation increses
                Vin = K0unitary.rotateAroundAxis(Vector(1, 0, 0), -deviation)
                photon = ComplexAmplitudePhoton(energy_in_ev=self.scan_e0, direction_vector=Vin)
                bunch_in.addPhoton(photon)
                deviations[ia] = angle_deviation_min + ia * angle_step

            coeffs = Diffraction.calculateDiffractedComplexAmplitudes(diffraction_setup, bunch_in,
                        is_thick=1, calculation_method=self.calculation_method, calculation_strategy_flag=self.calculation_strategy_flag)
            intensityS = numpy.abs(coeffs["S"]) ** 2
            intensityP = numpy.abs(coeffs["P"]) ** 2
            #

            plot_widget_id = plot_multi_data1D(1e6 * numpy.array(deviations),
                                        [numpy.array(intensityS, dtype=float), numpy.array(intensityP, dtype=float)],
                                        xtitle="theta - theta_B [urad]", ytitle="Reflectivity-S",
                                        ytitles=['S-polarized','P-polarized'])

            script_plots += """
#
angle_deviation_min = -0.5 * {scan_a_delta} * 1e-6  # radians
angle_deviation_max = 0.5 * {scan_a_delta} * 1e-6  # radians
angle_deviation_points = {scan_a_n}
angle_step = (angle_deviation_max - angle_deviation_min) / angle_deviation_points
bragg_angle = diffraction_setup.angleBragg({scan_e0})
print("Bragg angle for E=%f eV is %f deg" % ({scan_e0}, bragg_angle * 180.0 / numpy.pi))
deviations = numpy.zeros(angle_deviation_points)
bunch_in = ComplexAmplitudePhotonBunch()
K0 = diffraction_setup.vectorK0({scan_e0})
K0unitary = K0.getNormalizedVector()
for ia in range(angle_deviation_points):
    deviation = angle_deviation_min + ia * angle_step
    # minus sign in angle is to perform cw rotation when deviation increses
    Vin = K0unitary.rotateAroundAxis(Vector(1, 0, 0), -deviation)
    photon = ComplexAmplitudePhoton(energy_in_ev={scan_e0}, direction_vector=Vin)
    bunch_in.addPhoton(photon)
    deviations[ia] = angle_deviation_min + ia * angle_step

coeffs = Diffraction.calculateDiffractedComplexAmplitudes(diffraction_setup,
            bunch_in, is_thick=1,
            calculation_method={calculation_method}, # 0=Zachariasen, 1=Guigay
            calculation_strategy_flag={calculation_strategy_flag}, # 0=mpmath, 1=numpy, 2=numpy-truncated
            )
intensityS = numpy.abs(coeffs["S"]) ** 2
intensityP = numpy.abs(coeffs["P"]) ** 2
#
from srxraylib.plot.gol import plot
plot(1e6 * numpy.array(deviations), intensityS, 1e6 * numpy.array(deviations), intensityP, xtitle="theta - theta_B [urad]", ytitle="Reflectivity", legend=['S-polarized','P-polarized'])
"""




        self.plot_tab.layout().addWidget(plot_widget_id)

        return script_plots

    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

add_widget_parameters_to_module(__name__)

if __name__ == "__main__":
    import sys
    from AnyQt.QtWidgets import QApplication
    a = QApplication(sys.argv)
    ow = OWBragg()
    ow.show()
    a.exec()
    ow.saveSettings()
