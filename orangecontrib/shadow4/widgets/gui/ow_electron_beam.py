from AnyQt.QtWidgets import QMessageBox

from orangewidget import gui
from orangewidget.settings import Setting

from oasys2.widget import gui as oasysgui
from oasys2.widget.util import congruence
from oasys2.widget.widget import OWAction
from oasys2.widget.gui import ConfirmDialog, Styles

from orangecontrib.shadow4.widgets.gui.ow_generic_element import GenericElement

from shadow4.sources.s4_electron_beam import S4ElectronBeam

class OWElectronBeam(GenericElement):
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

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal", width=self.CONTROL_AREA_WIDTH-5)

        button = gui.button(button_box, self, "Run Shadow4/Source", callback=self.run_shadow4)
        button.setStyleSheet(Styles.button_blue)

        button = gui.button(button_box, self, "Reset Fields", callback=self.call_reset_settings)
        button.setStyleSheet(Styles.button_red)

        self.tabs_control_area = oasysgui.tabWidget(self.controlArea)
        self.tabs_control_area.setFixedHeight(self.TABS_AREA_HEIGHT)
        self.tabs_control_area.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        self.tab_electron_beam = oasysgui.createTabPage(self.tabs_control_area, "Electron Beam")

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

        self.left_box_2_1 = oasysgui.widgetBox(self.electron_beam_box, "", addSpace=False, orientation="vertical", height=190)

        oasysgui.lineEdit(self.left_box_2_1, self, "moment_xx",   "<x x>   [m^2]",   tooltip="moment_xx",   labelWidth=160, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_xxp",  "<x x'>  [m.rad]", tooltip="moment_xxp",  labelWidth=160, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_xpxp", "<x' x'> [rad^2]", tooltip="moment_xpxp", labelWidth=160, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_yy",   "<y y>   [m^2]",   tooltip="moment_yy",   labelWidth=160, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_yyp",  "<y y'>  [m.rad]", tooltip="moment_yyp",  labelWidth=160, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_ypyp", "<y' y'> [rad^2]", tooltip="moment_ypyp", labelWidth=160, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        lbl = oasysgui.widgetLabel(self.left_box_2_1, "Note: 2nd Moments do not include dispersion")
        lbl.setStyleSheet("color: darkblue; font-weight: bold;")

        self.left_box_2_2 = oasysgui.widgetBox(self.electron_beam_box, "", addSpace=False, orientation="vertical", height=190)

        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_size_h",       "Horizontal Beam Size \u03c3x [m]",          tooltip="electron_beam_size_h",       labelWidth=260, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_size_v",       "Vertical Beam Size \u03c3y [m]",            tooltip="electron_beam_size_v",       labelWidth=260, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_divergence_h", "Horizontal Beam Divergence \u03c3'x [rad]", tooltip="electron_beam_divergence_h", labelWidth=260, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_divergence_v", "Vertical Beam Divergence \u03c3'y [rad]",   tooltip="electron_beam_divergence_v", labelWidth=260, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        lbl = oasysgui.widgetLabel(self.left_box_2_2, "Note: Size/Divergence do not include dispersion")
        lbl.setStyleSheet("color: darkblue; font-weight: bold;")

        self.left_box_2_3 = oasysgui.widgetBox(self.electron_beam_box, "", addSpace=False, orientation="horizontal",height=190)
        self.left_box_2_3_l = oasysgui.widgetBox(self.left_box_2_3, "", addSpace=False, orientation="vertical")
        self.left_box_2_3_r = oasysgui.widgetBox(self.left_box_2_3, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.left_box_2_3_l, self, "electron_beam_emittance_h", "\u03B5x [m.rad]",tooltip="electron_beam_emittance_h",labelWidth=75, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_3_l, self, "electron_beam_alpha_h",     "\u03B1x",        tooltip="electron_beam_alpha_h",    labelWidth=75, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_3_l, self, "electron_beam_beta_h",      "\u03B2x [m]",    tooltip="electron_beam_beta_h",     labelWidth=75, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_3_l, self, "electron_beam_eta_h",       "\u03B7x",        tooltip="electron_beam_eta_h",      labelWidth=75, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_3_l, self, "electron_beam_etap_h",      "\u03B7'x",       tooltip="electron_beam_etap_h",     labelWidth=75, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_3_r, self, "electron_beam_emittance_v", "\u03B5y [m.rad]",tooltip="electron_beam_emittance_v",labelWidth=75, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_3_r, self, "electron_beam_alpha_v",     "\u03B1y",        tooltip="electron_beam_alpha_v",    labelWidth=75, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_3_r, self, "electron_beam_beta_v",      "\u03B2y [m]",    tooltip="electron_beam_beta_v",     labelWidth=75, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_3_r, self, "electron_beam_eta_v",       "\u03B7y",        tooltip="electron_beam_eta_v",      labelWidth=75, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_3_r, self, "electron_beam_etap_v",      "\u03B7'y",       tooltip="electron_beam_etap_v",     labelWidth=75, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)

        self.left_box_2_4   = oasysgui.widgetBox(self.electron_beam_box, "", addSpace=False, orientation="horizontal",height=190)

        self.set_TypeOfProperties()

        gui.rubber(self.controlArea)

    def set_TypeOfProperties(self):
        self.left_box_2_1.setVisible(self.type_of_properties == 0)
        self.left_box_2_2.setVisible(self.type_of_properties == 1)
        self.left_box_2_3.setVisible(self.type_of_properties == 2)
        self.left_box_2_4.setVisible(self.type_of_properties == 3)
        self.box_energy_spread.setVisible(self.flag_energy_spread == 1)

    def check_electron_beam(self):
        congruence.checkStrictlyPositiveNumber(self.electron_energy_in_GeV, "Energy")
        if self.flag_energy_spread == 1: congruence.checkStrictlyPositiveNumber(self.electron_energy_spread, "Energy Spread")
        congruence.checkStrictlyPositiveNumber(self.ring_current, "Ring Current")

        if self.type_of_properties == 0:
            congruence.checkPositiveNumber(self.moment_xx, "Moment xx")
            congruence.checkPositiveNumber(self.moment_xpxp, "Moment xpxp")
            congruence.checkPositiveNumber(self.moment_yy, "Moment yy")
            congruence.checkPositiveNumber(self.moment_ypyp, "Moment ypyp")
        elif self.type_of_properties == 1:
            congruence.checkPositiveNumber(self.electron_beam_size_h, "Horizontal Beam Size")
            congruence.checkPositiveNumber(self.electron_beam_divergence_h, "Horizontal Beam Divergence")
            congruence.checkPositiveNumber(self.electron_beam_size_v, "Vertical Beam Size")
            congruence.checkPositiveNumber(self.electron_beam_divergence_v, "Vertical Beam Divergence")
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


    def _check_dispersion_presence(self):
        return self.electron_beam_eta_h != 0.0 or \
               self.electron_beam_eta_v != 0.0 or \
               self.electron_beam_etap_h != 0.0 or \
               self.electron_beam_etap_v != 0.0

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
                                        self.electron_beam_emittance_v,
                                        self.electron_beam_alpha_v,
                                        self.electron_beam_beta_v)
            electron_beam.set_dispersion_all(self.electron_beam_eta_h,
                                             self.electron_beam_etap_h,
                                             self.electron_beam_eta_v,
                                             self.electron_beam_etap_v)
        elif self.type_of_properties == 3:
            electron_beam.set_moments_all(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        if self._check_dispersion_reset(): # modify input form with the results of the calculations
            self.populate_fields_from_electron_beam(electron_beam)

            return electron_beam
        else:
            return None

    def populate_fields_from_electron_beam(self, electron_beam):
        self.electron_energy_in_GeV = electron_beam.energy()
        self.electron_energy_spread = electron_beam._energy_spread
        self.ring_current           = electron_beam.current()

        moment_xx,\
        moment_xxp,\
        moment_xpxp,\
        moment_yy,\
        moment_yyp,\
        moment_ypyp = electron_beam.get_moments_all(dispersion=False)

        self.moment_xx              = round(moment_xx,   16)
        self.moment_xxp             = round(moment_xxp,  16)
        self.moment_xpxp            = round(moment_xpxp, 16)
        self.moment_yy              = round(moment_yy,   16)
        self.moment_yyp             = round(moment_yyp,  16)
        self.moment_ypyp            = round(moment_ypyp, 16)

        x, xp, y, yp                 = electron_beam.get_sigmas_all(dispersion=False)
        ex, ax, bx, ey, ay, by,      = electron_beam.get_twiss_all()
        eta_x, etap_x, eta_y, etap_y = electron_beam.get_dispersion_all()

        self.electron_beam_size_h       = round(x, 10)
        self.electron_beam_size_v       = round(y, 10)
        self.electron_beam_divergence_h = round(xp, 10)
        self.electron_beam_divergence_v = round(yp, 10)
        self.electron_beam_emittance_h  = round(ex, 16)
        self.electron_beam_emittance_v  = round(ey, 16)
        self.electron_beam_alpha_h      = round(ax, 6)
        self.electron_beam_alpha_v      = round(ay, 6)
        self.electron_beam_beta_h       = round(bx, 6)
        self.electron_beam_beta_v       = round(by, 6)
        self.electron_beam_eta_h        = round(eta_x, 8)
        self.electron_beam_eta_v        = round(eta_y, 8)
        self.electron_beam_etap_h       = round(etap_x, 8)
        self.electron_beam_etap_v       = round(etap_y, 8)

    def run_shadow4(self, scanning_data = None): raise NotImplementedError

    def _check_dispersion_reset(self):
        proceed = True
        if self.type_of_properties in [0, 1, 3] and self._check_dispersion_presence():
            if not ConfirmDialog.confirmed(parent=self, message="Dispersion parameters \u03B7, \u03B7' will be reset to zero, proceed?"):
                proceed = False
                self.type_of_properties = 2
                self.set_TypeOfProperties()
        return proceed

    def _electron_beam_modified(self):
        try:
            self.check_electron_beam()
            if self._check_dispersion_reset():
                self.populate_fields_from_electron_beam(self.get_electron_beam())
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e.args[0]), QMessageBox.Ok)
            if self.IS_DEVELOP: raise e