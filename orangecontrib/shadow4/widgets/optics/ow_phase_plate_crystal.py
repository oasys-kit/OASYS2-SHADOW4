import numpy

from orangewidget import gui
from orangewidget.settings import Setting
from oasys2.widget import gui as oasysgui
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from dabax.dabax_xraylib import DabaxXraylib
from dabax.dabax_files import dabax_f0_files, dabax_f1f2_files

from shadow4.beamline.optical_elements.phase_plate_crystals.s4_plane_phase_plate_crystal import \
    S4PlanePhasePlateCrystal, S4PlanePhasePlateCrystalElement

from orangecontrib.shadow4.widgets.optics.ow_crystal import _OWCrystal


class OWPhasePlateCrystal(_OWCrystal):
    """
    Phase plate crystal: transmitted (forward-diffracted) beam of a plane perfect crystal plate in Bragg geometry,
    usually detuned a few Darwin half widths from the Bragg angle (x-ray phase retarder).
    """
    name = "Phase Plate Crystal"
    description = "Shadow Phase Plate Crystal (Bragg transmitted beam)"
    icon = "icons/phase_plate_crystal.png"

    priority = 1.305

    # defaults: Si 220 plate, 50 um, 10 keV, detuned by -3 Darwin half widths (quarter-wave plate, Hirano et al. 1993)
    user_defined_h = Setting(2)
    user_defined_k = Setting(2)
    user_defined_l = Setting(0)
    photon_energy = Setting(10000.0)
    thickness = Setting(50e-6)

    crystal_detuning = Setting(2)
    detune_angle_urad = Setting(0.0)
    detune_half_darwin_widths = Setting(-3.0)

    def __init__(self):
        # keep the phase plate icon and title (do not switch them with the surface shape: only plane plates)
        super(OWPhasePlateCrystal, self).__init__(switch_icons=False)
        # only plane plates
        self.surface_shape_type = 0
        self.surface_shape_type_combo.setEnabled(False)
        self.surface_shape_tab_visibility()

    def get_oe_type(self):
        return "crystal", "Phase Plate Crystal"

    def populate_tab_crystal_diffraction(self, subtab_crystal_diffraction):
        super(OWPhasePlateCrystal, self).populate_tab_crystal_diffraction(subtab_crystal_diffraction)

        gui.separator(self.autosetting_box, height=10)

        gui.comboBox(self.autosetting_box, self, "crystal_detuning", tooltip="crystal_detuning",
                     label="Detuning from Bragg angle", labelWidth=200,
                     items=["No", "Angle", "Darwin half widths"],
                     callback=self.set_detuning, sendSelectedValue=False, orientation="horizontal")

        self.detuning_box_1 = oasysgui.widgetBox(self.autosetting_box, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.detuning_box_1, self, "detune_angle_urad", "Detuning angle [μrad]",
                          tooltip="detune_angle_urad", labelWidth=260, valueType=float, orientation="horizontal")

        self.detuning_box_2 = oasysgui.widgetBox(self.autosetting_box, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.detuning_box_2, self, "detune_half_darwin_widths", "Detuning [Darwin half widths]",
                          tooltip="detune_half_darwin_widths", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_detuning()

    def populate_box_efields_management(self, subtab_crystal_diffraction):
        pass # the transmitted beam is always calculated with the Jones calculus

    def populate_tab_crystal_geometry(self, subtab_crystal_geometry):
        self.asymmetric_cut_box = oasysgui.widgetBox(subtab_crystal_geometry, "", addSpace=False, orientation="vertical",
                                                     height=110)

        gui.comboBox(self.asymmetric_cut_box, self, "asymmetric_cut", tooltip="asymmetric_cut", label="Asymmetric cut",
                     labelWidth=355, items=["No", "Yes"], callback=self.crystal_geometry_tab_visibility,
                     sendSelectedValue=False, orientation="horizontal")

        self.asymmetric_cut_box_1 = oasysgui.widgetBox(self.asymmetric_cut_box, "", addSpace=False, orientation="vertical")
        self.asymmetric_cut_box_1_empty = oasysgui.widgetBox(self.asymmetric_cut_box, "", addSpace=False,
                                                             orientation="vertical")

        oasysgui.lineEdit(self.asymmetric_cut_box_1, self, "planes_angle", "Planes angle [deg]",
                          tooltip="planes_angle", labelWidth=260, valueType=float, orientation="horizontal")

        oasysgui.lineEdit(subtab_crystal_geometry, self, "thickness", "Crystal thickness [m]", tooltip="thickness",
                          valueType=float, labelWidth=260, orientation="horizontal")

        self.crystal_geometry_tab_visibility()

    def crystal_geometry_tab_visibility(self):
        self.set_asymmetric_cut()

    def set_detuning(self):
        self.detuning_box_1.setVisible(self.crystal_detuning == 1)
        self.detuning_box_2.setVisible(self.crystal_detuning == 2)

    #########################################################
    # S4 objects
    #########################################################

    def get_optical_element_instance(self):
        if self.surface_shape_type != 0:
            raise ValueError("Phase plate crystal: only plane surface is implemented.")
        if self.modified_surface:
            raise ValueError("Phase plate crystal: modified surface not implemented.")

        try:    name = self.getNode().title
        except: name = "Phase Plate Crystal"

        if self.diffraction_calculation == 1:
            dabax = DabaxXraylib(file_f0="%s" % dabax_f0_files()[self.DABAX_F0_FILE_INDEX],
                                 file_f1f2="%s" % dabax_f1f2_files()[self.DABAX_F1F2_FILE_INDEX],
                                 )
        else:
            dabax = None

        return S4PlanePhasePlateCrystal(
            name=name,
            boundary_shape=self.get_boundary_shape(),
            material=self.CRYSTALS[self.user_defined_crystal],
            miller_index_h=self.user_defined_h,
            miller_index_k=self.user_defined_k,
            miller_index_l=self.user_defined_l,
            asymmetry_angle=0.0 if not self.asymmetric_cut else numpy.radians(self.planes_angle),
            thickness=self.thickness,
            f_central=self.crystal_auto_setting,
            f_phot_cent=self.units_in_use,
            phot_cent=(self.photon_energy if (self.units_in_use == 0) else self.photon_wavelength),
            f_detune=self.crystal_detuning if self.crystal_auto_setting else 0,
            detune_angle=1e-6 * self.detune_angle_urad,
            detune_half_darwin_widths=self.detune_half_darwin_widths,
            file_refl=self.file_crystal_parameters,
            f_bragg_a=True if self.asymmetric_cut else False,
            material_constants_library_flag=self.diffraction_calculation,
            dabax=dabax,
        )

    def get_beamline_element_instance(self):
        return S4PlanePhasePlateCrystalElement()


add_widget_parameters_to_module(__name__)

if __name__ == "__main__":
    import sys
    from shadow4.beamline.s4_beamline import S4Beamline

    def get_test_beam():
        from shadow4.sources.source_geometrical.source_geometrical import SourceGeometrical
        light_source = SourceGeometrical(name='SourceGeometrical', nrays=5000, seed=5676561)
        light_source.set_spatial_type_point()
        light_source.set_angular_distribution_flat(hdiv1=0.0, hdiv2=0.0, vdiv1=0.0, vdiv2=0.0)
        light_source.set_energy_distribution_singleline(10000.0, unit='eV')
        light_source.set_polarization(polarization_degree=1.0, phase_diff=0.0, coherent_beam=1)
        beam = light_source.get_beam()
        from orangecontrib.shadow4.util.shadow4_objects import ShadowData
        return ShadowData(beam=beam, beamline=S4Beamline(light_source=light_source))

    from AnyQt.QtWidgets import QApplication
    a = QApplication(sys.argv)
    ow = OWPhasePlateCrystal()
    ow.set_shadow_data(get_test_beam())
    ow.show()
    a.exec()
    ow.saveSettings()
