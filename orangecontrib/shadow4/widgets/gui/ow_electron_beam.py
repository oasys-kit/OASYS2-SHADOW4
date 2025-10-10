from PyQt5.QtGui import QPalette, QColor, QFont

from orangewidget import gui
from orangewidget.settings import Setting

from oasys2.widget import gui as oasysgui
from oasys2.widget.util import congruence
from oasys2.widget.widget import OWAction
from oasys2.widget.gui import ConfirmDialog

from orangecontrib.shadow4.widgets.gui.ow_generic_element import GenericElement

from shadow4.sources.s4_electron_beam import S4ElectronBeam

class OWElectronBeam(GenericElement):

    syned_file_name = Setting("Select *.json file")

    electron_energy_in_GeV = Setting(1.9)
    electron_energy_spread = Setting(0.000)
    ring_current           = Setting(0.4)

    moment_xx           = Setting(0.0)
    moment_xxp          = Setting(0.0)
    moment_xpxp         = Setting(0.0)
    moment_yy           = Setting(0.0)
    moment_yyp          = Setting(0.0)
    moment_ypyp         = Setting(0.0)

    electron_beam_size_h       = Setting(39e-6)
    electron_beam_divergence_h = Setting(31e-6)
    electron_beam_size_v       = Setting(39.2e-6)
    electron_beam_divergence_v = Setting(39.2e-6)

    electron_beam_emittance_h = Setting(0.0)
    electron_beam_emittance_v = Setting(0.0)
    electron_beam_beta_h      = Setting(0.0)
    electron_beam_beta_v      = Setting(0.0)
    electron_beam_alpha_h     = Setting(0.0)
    electron_beam_alpha_v     = Setting(0.0)
    electron_beam_eta_h       = Setting(0.0)
    electron_beam_eta_v       = Setting(0.0)
    electron_beam_etap_h      = Setting(0.0)
    electron_beam_etap_v      = Setting(0.0)

    type_of_properties = Setting(1)
    flag_energy_spread = Setting(0)

    def __init__(self, show_energy_spread=False):
        super().__init__(show_automatic_box=False, has_footprint=False)

        self.runaction = OWAction("Run Shadow4/Source", self)
        self.runaction.triggered.connect(self.run_shadow4)
        self.addAction(self.runaction)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Run shadow4/source", callback=self.run_shadow4)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        button = gui.button(button_box, self, "Reset Fields", callback=self.call_reset_settings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(150)


        self.tabs_control_area = oasysgui.tabWidget(self.controlArea)
        self.tabs_control_area.setFixedHeight(self.TABS_AREA_HEIGHT)
        self.tabs_control_area.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        self.tab_electron_beam = oasysgui.createTabPage(self.tabs_control_area, "Electron Beam Setting")

        self.electron_beam_box = oasysgui.widgetBox(self.tab_electron_beam, "Electron Beam/Machine Parameters", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.electron_beam_box, self, "electron_energy_in_GeV", "Energy [GeV]",  tooltip="electron_energy_in_GeV", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.electron_beam_box, self, "ring_current", "Ring Current [A]",        tooltip="ring_current",           labelWidth=260, valueType=float, orientation="horizontal")

        if show_energy_spread:
            gui.comboBox(self.electron_beam_box, self, "flag_energy_spread", tooltip="flag_energy_spread", label="Energy Spread", labelWidth=350,
                     items=["No (zero)", "Yes"],
                     callback=self.set_TypeOfProperties,
                     sendSelectedValue=False, orientation="horizontal")
        else:
            self.flag_energy_spread = 0
        self.box_energy_spread = oasysgui.widgetBox(self.electron_beam_box, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.box_energy_spread, self, "electron_energy_spread", "Energy Spread DE/E", tooltip="electron_energy_spread", labelWidth=260, valueType=float, orientation="horizontal")


        gui.comboBox(self.electron_beam_box, self, "type_of_properties", tooltip="type_of_properties", label="Electron Beam Properties", labelWidth=350,
                     items=["From 2nd Moments", "From Size/Divergence", "From Twiss parameters","Zero emittance"],
                     callback=self.set_TypeOfProperties,
                     sendSelectedValue=False, orientation="horizontal")

        self.left_box_2_1 = oasysgui.widgetBox(self.electron_beam_box, "", addSpace=False, orientation="vertical", height=150)

        oasysgui.lineEdit(self.left_box_2_1, self, "moment_xx",   "<x x>   [m^2]",   tooltip="moment_xx",   labelWidth=160, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_xxp",  "<x x'>  [m.rad]", tooltip="moment_xxp",  labelWidth=160, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_xpxp", "<x' x'> [rad^2]", tooltip="moment_xpxp", labelWidth=160, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_yy",   "<y y>   [m^2]",   tooltip="moment_yy",   labelWidth=160, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_yyp",  "<y y'>  [m.rad]", tooltip="moment_yyp",  labelWidth=160, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_ypyp", "<y' y'> [rad^2]", tooltip="moment_ypyp", labelWidth=160, valueType=float, orientation="horizontal")


        self.left_box_2_2 = oasysgui.widgetBox(self.electron_beam_box, "", addSpace=False, orientation="vertical", height=150)

        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_size_h",       "Horizontal Beam Size \u03c3x [m]",          tooltip="electron_beam_size_h", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_size_v",       "Vertical Beam Size \u03c3y [m]",            tooltip="electron_beam_size_v",  labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_divergence_h", "Horizontal Beam Divergence \u03c3'x [rad]", tooltip="electron_beam_divergence_h", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_divergence_v", "Vertical Beam Divergence \u03c3'y [rad]",   tooltip="electron_beam_divergence_v", labelWidth=260, valueType=float, orientation="horizontal")

        self.left_box_2_3 = oasysgui.widgetBox(self.electron_beam_box, "", addSpace=False, orientation="horizontal",height=150)
        self.left_box_2_3_l = oasysgui.widgetBox(self.left_box_2_3, "", addSpace=False, orientation="vertical")
        self.left_box_2_3_r = oasysgui.widgetBox(self.left_box_2_3, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.left_box_2_3_l, self, "electron_beam_emittance_h", "\u03B5x [m.rad]",tooltip="electron_beam_emittance_h",labelWidth=75, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_3_l, self, "electron_beam_alpha_h",     "\u03B1x",        tooltip="electron_beam_alpha_h",    labelWidth=75, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_3_l, self, "electron_beam_beta_h",      "\u03B2x [m]",    tooltip="electron_beam_beta_h",     labelWidth=75, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_3_l, self, "electron_beam_eta_h",       "\u03B7x",        tooltip="electron_beam_eta_h",      labelWidth=75, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_3_l, self, "electron_beam_etap_h",      "\u03B7'x",       tooltip="electron_beam_etap_h",     labelWidth=75, valueType=float, orientation="horizontal")


        oasysgui.lineEdit(self.left_box_2_3_r, self, "electron_beam_emittance_v", "\u03B5y [m.rad]",tooltip="electron_beam_emittance_v",labelWidth=75, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_3_r, self, "electron_beam_alpha_v",     "\u03B1y",        tooltip="electron_beam_alpha_v",    labelWidth=75,valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_3_r, self, "electron_beam_beta_v",      "\u03B2y [m]",    tooltip="electron_beam_beta_v",     labelWidth=75, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_3_r, self, "electron_beam_eta_v",       "\u03B7y",        tooltip="electron_beam_eta_v",      labelWidth=75, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_3_r, self, "electron_beam_etap_v",      "\u03B7'y",       tooltip="electron_beam_etap_v",     labelWidth=75, valueType=float, orientation="horizontal")

        self.set_TypeOfProperties()

        gui.rubber(self.controlArea)

    def set_TypeOfProperties(self):
        self.left_box_2_1.setVisible(self.type_of_properties == 0)
        self.left_box_2_2.setVisible(self.type_of_properties == 1)
        self.left_box_2_3.setVisible(self.type_of_properties == 2)
        self.box_energy_spread.setVisible(self.flag_energy_spread == 1)
        self.set_visibility_energy_spread()

    def set_visibility_energy_spread(self): # to be filled in the upper class
        pass

    def check_data(self):
        congruence.checkStrictlyPositiveNumber(self.electron_energy_in_GeV , "Energy")
        congruence.checkStrictlyPositiveNumber(self.electron_energy_spread, "Energy Spread")
        congruence.checkStrictlyPositiveNumber(self.ring_current, "Ring Current")

        if self.type_of_properties == 0:
            congruence.checkPositiveNumber(self.moment_xx   , "Moment xx")
            congruence.checkPositiveNumber(self.moment_xpxp , "Moment xpxp")
            congruence.checkPositiveNumber(self.moment_yy   , "Moment yy")
            congruence.checkPositiveNumber(self.moment_ypyp , "Moment ypyp")
        elif self.type_of_properties == 1:
            congruence.checkPositiveNumber(self.electron_beam_size_h       , "Horizontal Beam Size")
            congruence.checkPositiveNumber(self.electron_beam_divergence_h , "Horizontal Beam Divergence")
            congruence.checkPositiveNumber(self.electron_beam_size_v       , "Vertical Beam Size")
            congruence.checkPositiveNumber(self.electron_beam_divergence_v , "Vertical Beam Divergence")
        elif self.type_of_properties == 2:
            congruence.checkPositiveNumber(self.electron_beam_emittance_h, "Horizontal Beam Emittance")
            congruence.checkPositiveNumber(self.electron_beam_emittance_v, "Vertical Beam Emittance")
            congruence.checkNumber(self.electron_beam_alpha_h, "Horizontal Beam Alpha")
            congruence.checkNumber(self.electron_beam_alpha_v, "Vertical Beam Alpha")
            congruence.checkNumber(self.electron_beam_beta_h, "Horizontal Beam Beta")
            congruence.checkNumber(self.electron_beam_beta_v, "Vertical Beam Beta")
            congruence.checkNumber(self.electron_beam_eta_h, "Horizontal Beam Dispersion Eta")
            congruence.checkNumber(self.electron_beam_eta_v, "Vertical Beam Dispersion Eta")
            congruence.checkNumber(self.electron_beam_etap_h, "Horizontal Beam Dispersion Eta'")
            congruence.checkNumber(self.electron_beam_etap_v, "Vertical Beam Dispersion Eta'")

            def check_contraints(emittance, alpha, beta, eta, etap, direction):
                S4ElectronBeam._set_twiss(energy_spread=self.electron_energy_spread,
                                          emittance=emittance,
                                          alpha=alpha,
                                          beta=beta,
                                          eta=eta,
                                          etap=etap,
                                          check_consistency=True,
                                          direction=direction)
            check_contraints(self.electron_beam_emittance_h, self.electron_beam_alpha_h, self.electron_beam_beta_h, self.electron_beam_eta_h, self.electron_beam_etap_h, "Horizontal")
            check_contraints(self.electron_beam_emittance_v, self.electron_beam_alpha_v, self.electron_beam_beta_v, self.electron_beam_eta_v, self.electron_beam_etap_v, "Vertical")

        self.check_magnetic_structure()


    def run_shadow4(self):
        raise Exception("To be defined in the superclass")

    def check_twiss_change(self, electron_beam: S4ElectronBeam):
        return self.electron_beam_eta_h != electron_beam._dispersion_x or \
               self.electron_beam_eta_v != electron_beam._dispersion_y or \
               self.electron_beam_etap_h != electron_beam._dispersionp_x or \
               self.electron_beam_etap_v != electron_beam._dispersionp_y

    def get_electron_beam(self):
        electron_beam = S4ElectronBeam(energy_in_GeV=self.electron_energy_in_GeV,
                                     energy_spread=self.electron_energy_spread,
                                     current=self.ring_current)

        if self.type_of_properties == 0:
            electron_beam.set_moments_all(moment_xx=self.moment_xx,
                                          moment_xxp=self.moment_xxp,
                                          moment_xpxp=self.moment_xpxp,
                                          moment_yy=self.moment_yy,
                                          moment_yyp=self.moment_yyp,
                                          moment_ypyp=self.moment_ypyp)
        elif self.type_of_properties == 1:
            electron_beam.set_sigmas_all(sigma_x=self.electron_beam_size_h,
                                         sigma_y=self.electron_beam_size_v,
                                         sigma_xp=self.electron_beam_divergence_h,
                                         sigma_yp=self.electron_beam_divergence_v)
        elif self.type_of_properties == 2:
            electron_beam.set_twiss_all(self.electron_beam_emittance_h,
                                        self.electron_beam_alpha_h,
                                        self.electron_beam_beta_h,
                                        self.electron_beam_eta_h,
                                        self.electron_beam_etap_h,
                                        self.electron_beam_emittance_v,
                                        self.electron_beam_alpha_v,
                                        self.electron_beam_beta_v,
                                        self.electron_beam_eta_v,
                                        self.electron_beam_etap_v)
        elif self.type_of_properties == 3:
            electron_beam.set_moments_all(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        proceed = True
        if self.type_of_properties in [0, 1] and self.check_twiss_change(electron_beam):
            if not ConfirmDialog.confirmed(parent=self, message="This operation will set \u03B7, \u03B7' to zero and recompute the twiss parameters, proceed?"):
                proceed = False
                self.type_of_properties = 2
                self.set_TypeOfProperties()

        if proceed: # modify input form with the results of the calculations
            self.moment_xx              = round(electron_beam._moment_xx,   16)
            self.moment_xxp             = round(electron_beam._moment_xxp,  16)
            self.moment_xpxp            = round(electron_beam._moment_xpxp, 16)
            self.moment_yy              = round(electron_beam._moment_yy,   16)
            self.moment_yyp             = round(electron_beam._moment_yyp,  16)
            self.moment_ypyp            = round(electron_beam._moment_ypyp, 16)
            self.electron_beam_eta_h    = electron_beam._dispersion_x
            self.electron_beam_eta_v    = electron_beam._dispersion_y
            self.electron_beam_etap_h   = electron_beam._dispersionp_x
            self.electron_beam_etap_v   = electron_beam._dispersionp_y

            # calculated parameters from second moments
            x, xp, y, yp = electron_beam.get_sigmas_all()

            self.electron_beam_size_h       = round(x, 10)
            self.electron_beam_size_v       = round(y, 10)
            self.electron_beam_divergence_h = round(xp, 10)
            self.electron_beam_divergence_v = round(yp, 10)

            ex, ax, bx, ey, ay, by = electron_beam.get_twiss_all()

            self.electron_beam_emittance_h = round(ex, 16)
            self.electron_beam_emittance_v = round(ey, 16)
            self.electron_beam_alpha_h     = round(ax, 6)
            self.electron_beam_alpha_v     = round(ay, 6)
            self.electron_beam_beta_h      = round(bx, 6)
            self.electron_beam_beta_v      = round(by, 6)

            return electron_beam
        else:
            return None

    def populate_fields_from_electron_beam(self, electron_beam):
        self.electron_energy_in_GeV = electron_beam.energy()
        self.electron_energy_spread = electron_beam._energy_spread
        self.ring_current           = electron_beam.current()

        self.moment_xx              = round(electron_beam._moment_xx,   16)
        self.moment_xxp             = round(electron_beam._moment_xxp,  16)
        self.moment_xpxp            = round(electron_beam._moment_xpxp, 16)
        self.moment_yy              = round(electron_beam._moment_yy,   16)
        self.moment_yyp             = round(electron_beam._moment_yyp,  16)
        self.moment_ypyp            = round(electron_beam._moment_ypyp, 16)
        self.electron_beam_eta_h    = electron_beam._dispersion_x
        self.electron_beam_eta_v    = electron_beam._dispersion_y
        self.electron_beam_etap_h   = electron_beam._dispersionp_x
        self.electron_beam_etap_v   = electron_beam._dispersionp_y

        # calculated parameters from second moments
        x, xp, y, yp = electron_beam.get_sigmas_all()

        self.electron_beam_size_h       = round(x, 10)
        self.electron_beam_size_v       = round(y, 10)
        self.electron_beam_divergence_h = round(xp, 10)
        self.electron_beam_divergence_v = round(yp, 10)

        ex, ax, bx, ey, ay, by = electron_beam.get_twiss_all()

        self.electron_beam_emittance_h = round(ex, 16)
        self.electron_beam_emittance_v = round(ey, 16)
        self.electron_beam_alpha_h     = round(ax, 6)
        self.electron_beam_alpha_v     = round(ay, 6)
        self.electron_beam_beta_h      = round(bx, 6)
        self.electron_beam_beta_v      = round(by, 6)
