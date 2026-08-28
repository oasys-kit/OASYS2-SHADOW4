import os

from orangewidget import gui
from orangewidget.settings import Setting

from oasys2.widget import gui as oasysgui

from orangecontrib.shadow4.widgets.gui.ow_abstract_lens import OWAbstractLens
from orangecontrib.shadow4.widgets.gui.ow_optical_element_with_surface_shape import \
    ShowSurfaceErrorDataFileDialog, ShowImageErrorDataFileDialog
import orangecanvas.resources as resources
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from shadow4.beamline.optical_elements.refractors.s4_lens import S4Lens, S4LensElement

from dabax.dabax_xraylib import DabaxXraylib
from dabax.dabax_files import dabax_f1f2_files, dabax_crosssec_files

class OWLens(OWAbstractLens):
    name = "Refractive Lens"
    description = "Shadow Refractive Lens"
    icon = "icons/lens.png"
    priority = 2.1

    help_path = os.path.join(resources.package_dirname("orangecontrib.shadow4.widgets.gui"), "misc", "lens_help.png")

    flag_add_mesh_surface_entrance = Setting(0)
    flag_add_mesh_surface_exit     = Setting(0)
    mesh_surface_entrance_h5file   = Setting("<none>.hdf5")
    mesh_surface_exit_h5file       = Setting("<none>.hdf5")

    def __init__(self):
        super().__init__()

    # ----------------------------------------------------
    # Advanced Settings / Modified Surface

    def create_advanced_settings_subtabs(self, tabs_advanced_settings):
        subtab_modified_surface = oasysgui.createTabPage(tabs_advanced_settings, "Modified Surface")

        return [subtab_modified_surface] + super().create_advanced_settings_subtabs(tabs_advanced_settings)

    def populate_advanced_setting_subtabs(self, advanced_setting_subtabs):
        self.populate_tab_modified_surface(advanced_setting_subtabs[0])

        super().populate_advanced_setting_subtabs(advanced_setting_subtabs[1:])

    def populate_tab_modified_surface(self, subtab_modified_surface):
        box = oasysgui.widgetBox(subtab_modified_surface, "Modified Surface Parameters", addSpace=True, orientation="vertical")

        # ---- Entrance interface -------------------------------------------------
        gui.comboBox(box, self, "flag_add_mesh_surface_entrance", tooltip="flag_add_mesh_surface_entrance",
                     label="Add mesh to Entrance interface", labelWidth=250,
                     items=["No", "Yes"], callback=self.modified_surface_tab_visibility,
                     sendSelectedValue=False, orientation="horizontal")

        self.mod_surf_entrance_box_1 = oasysgui.widgetBox(box, "", addSpace=False, orientation="horizontal")

        self.le_mesh_surface_entrance_h5file = oasysgui.lineEdit(self.mod_surf_entrance_box_1, self, "mesh_surface_entrance_h5file",
                                                                  "File", tooltip="mesh_surface_entrance_h5file", labelWidth=40,
                                                                  valueType=str, orientation="horizontal")

        gui.button(self.mod_surf_entrance_box_1, self, "...", callback=self.select_mesh_surface_entrance_file_name, width=30)
        gui.button(self.mod_surf_entrance_box_1, self, "View Surf", callback=self.view_mesh_surface_entrance_surface, width=65,
                   tooltip="Render data in surface mode [slow]")
        gui.button(self.mod_surf_entrance_box_1, self, "View Img", callback=self.view_mesh_surface_entrance_image, width=65,
                   tooltip="Render data in image mode [slow]")

        gui.separator(box, height=10)

        # ---- Exit interface -------------------------------------------------
        gui.comboBox(box, self, "flag_add_mesh_surface_exit", tooltip="flag_add_mesh_surface_exit",
                     label="Add mesh to Exit interface", labelWidth=250,
                     items=["No", "Yes"], callback=self.modified_surface_tab_visibility,
                     sendSelectedValue=False, orientation="horizontal")

        self.mod_surf_exit_box_1 = oasysgui.widgetBox(box, "", addSpace=False, orientation="horizontal")

        self.le_mesh_surface_exit_h5file = oasysgui.lineEdit(self.mod_surf_exit_box_1, self, "mesh_surface_exit_h5file",
                                                              "File", tooltip="mesh_surface_exit_h5file", labelWidth=40,
                                                              valueType=str, orientation="horizontal")

        gui.button(self.mod_surf_exit_box_1, self, "...", callback=self.select_mesh_surface_exit_file_name, width=30)
        gui.button(self.mod_surf_exit_box_1, self, "View Surf", callback=self.view_mesh_surface_exit_surface, width=65,
                   tooltip="Render data in surface mode [slow]")
        gui.button(self.mod_surf_exit_box_1, self, "View Img", callback=self.view_mesh_surface_exit_image, width=65,
                   tooltip="Render data in image mode [slow]")

        self.modified_surface_tab_visibility()

    def modified_surface_tab_visibility(self):
        self.mod_surf_entrance_box_1.setVisible(self.flag_add_mesh_surface_entrance == 1)
        self.mod_surf_exit_box_1.setVisible(self.flag_add_mesh_surface_exit == 1)

    def select_mesh_surface_entrance_file_name(self):
        self.le_mesh_surface_entrance_h5file.setText(
            oasysgui.selectFileFromDialog(self, self.mesh_surface_entrance_h5file, "Select Entrance Interface Mesh File",
                                          file_extension_filter="Data Files (*.h5 *.hdf5)"))

    def select_mesh_surface_exit_file_name(self):
        self.le_mesh_surface_exit_h5file.setText(
            oasysgui.selectFileFromDialog(self, self.mesh_surface_exit_h5file, "Select Exit Interface Mesh File",
                                          file_extension_filter="Data Files (*.h5 *.hdf5)"))

    def view_mesh_surface_entrance_surface(self):
        try:
            dialog = ShowSurfaceErrorDataFileDialog(parent=self, file_name=self.mesh_surface_entrance_h5file)
            dialog.show()
        except Exception as exception:
            self.prompt_exception(exception)

    def view_mesh_surface_entrance_image(self):
        try:
            dialog = ShowImageErrorDataFileDialog(parent=self, file_name=self.mesh_surface_entrance_h5file)
            dialog.show()
        except Exception as exception:
            self.prompt_exception(exception)

    def view_mesh_surface_exit_surface(self):
        try:
            dialog = ShowSurfaceErrorDataFileDialog(parent=self, file_name=self.mesh_surface_exit_h5file)
            dialog.show()
        except Exception as exception:
            self.prompt_exception(exception)

    def view_mesh_surface_exit_image(self):
        try:
            dialog = ShowImageErrorDataFileDialog(parent=self, file_name=self.mesh_surface_exit_h5file)
            dialog.show()
        except Exception as exception:
            self.prompt_exception(exception)

    # ----------------------------------------------------
    # from OpticalElement

    def get_optical_element_instance(self):
        try:    name = self.getNode().title
        except: name = "Refractive Lens"

        um_to_si = 1e-6

        boundary_shape = self.get_lens_boundary_shape()

        if self.is_cylinder == 1:
            cylinder_angle = self.cylinder_angle + 1
        else:
            cylinder_angle = 0


        if self.ri_calculation_mode == 3:
            dabax = DabaxXraylib(
                file_f1f2="%s" % dabax_f1f2_files()[self.DABAX_F1F2_FILE_INDEX],
                file_CrossSec="%s" % dabax_crosssec_files()[self.DABAX_CROSSSEC_FILE_INDEX],
            )
        else:
            dabax = None

        return S4Lens(name=name,
                      boundary_shape=boundary_shape,
                      material=self.material,
                      density=self.density,
                      thickness=self.interthickness*um_to_si,
                      surface_shape=self.surface_shape,
                      convex_to_the_beam=self.convex_to_the_beam,
                      cylinder_angle=cylinder_angle,
                      ri_calculation_mode=self.ri_calculation_mode,
                      prerefl_file=self.prerefl_file,
                      refraction_index=self.refraction_index,
                      attenuation_coefficient=self.attenuation_coefficient,
                      radius=self.radius*um_to_si,
                      conic_coefficients1=None, # TODO: add conic coefficient shape to the GUI
                      conic_coefficients2=None,  # TODO: add conic coefficient shape to the GUI
                      dabax=dabax,
                      flag_add_mesh_surface_entrance=self.flag_add_mesh_surface_entrance,
                      flag_add_mesh_surface_exit=self.flag_add_mesh_surface_exit,
                      mesh_surface_entrance_h5file=self.mesh_surface_entrance_h5file,
                      mesh_surface_exit_h5file=self.mesh_surface_exit_h5file,
                      )

    def get_beamline_element_instance(self):
        return S4LensElement()

add_widget_parameters_to_module(__name__)

if __name__ == "__main__":
    from shadow4.beamline.s4_beamline import S4Beamline
    import sys
    from orangecontrib.shadow4.util.shadow4_objects import ShadowData, PreReflPreProcessorData, VlsPgmPreProcessorData

    def get_test_beam():
        # electron beam
        from syned.storage_ring.light_source import ElectronBeam
        electron_beam = ElectronBeam(energy_in_GeV=6, energy_spread=0.001, current=0.2)
        electron_beam.set_sigmas_all(sigma_x=3.01836e-05, sigma_y=3.63641e-06, sigma_xp=4.36821e-06,
                                     sigma_yp=1.37498e-06)

        # Gaussian undulator
        from shadow4.sources.undulator.s4_undulator_gaussian import S4UndulatorGaussian
        sourceundulator = S4UndulatorGaussian(
            period_length=0.0159999,
            number_of_periods=100,
            photon_energy=2700.136,
            delta_e=0.0,
            flag_emittance=1,  # Use emittance (0=No, 1=Yes)
        )
        sourceundulator.set_energy_monochromatic(2700.14)

        from shadow4.sources.undulator.s4_undulator_gaussian_light_source import S4UndulatorGaussianLightSource
        light_source = S4UndulatorGaussianLightSource(name='GaussianUndulator', electron_beam=electron_beam,
                                              magnetic_structure=sourceundulator, nrays=5000, seed=5676561)

        beam = light_source.get_beam()

        return ShadowData(beam=beam, beamline=S4Beamline(light_source=light_source))

    from AnyQt.QtWidgets import QApplication
    a = QApplication(sys.argv)
    ow = OWLens()
    ow.set_shadow_data(get_test_beam())

    ow.show()
    a.exec()
    ow.saveSettings()

