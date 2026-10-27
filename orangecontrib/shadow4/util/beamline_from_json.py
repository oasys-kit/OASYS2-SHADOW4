"""
Populate an OASYS2 canvas with the widgets of a SHADOW4 beamline saved in a (syned) json file
(S4Beamline.to_json()).

Prototype: geometrical source, and mirrors with plane or spherical (cylindrical) surface.

For each supported object, a function fills the settings of the corresponding widget from the shadow4 object
(the inverse of the get_lightsource() / get_optical_element_instance() / get_coordinates_instance() /
get_movements_instance() methods of the widget). The widget, after being populated, rebuilds an object equivalent
to the original one.

Usage (from the Shadow4 menu, or from a script running in OASYS2):

    from orangecontrib.shadow4.util.beamline_from_json import load_beamline, build_canvas
    beamline = load_beamline("beamline.json")
    warnings = build_canvas(canvas_main_window.current_document(), canvas_main_window.widget_registry, beamline)

Notes:
    - spherical surfaces are set in the widget with the external definition of the surface (radius), which gives
      the same surface (the json files of previous versions of shadow4 contain only the radius);
    - the movements of the elements are read from the json files written by recent versions of shadow4;
    - files referenced by the elements (e.g., reflectivity files) must exist in the current machine.
"""
import numpy

from shadow4.tools.json_tools import load_from_json_file

from shadow4.sources.source_geometrical.source_geometrical import SourceGeometrical
from shadow4.beamline.optical_elements.mirrors.s4_plane_mirror import S4PlaneMirror
from shadow4.beamline.optical_elements.mirrors.s4_sphere_mirror import S4SphereMirror

from syned.beamline.shape import Rectangle, Ellipse, SphericalCylinder

# shadow4 class name -> qualified name of the OASYS2 widget
WIDGETS = {
    "SourceGeometrical"     : "orangecontrib.shadow4.widgets.sources.ow_geometrical.OWGeometrical",
    "S4PlaneMirrorElement"  : "orangecontrib.shadow4.widgets.optics.ow_mirror.OWMirror",
    "S4SphereMirrorElement" : "orangecontrib.shadow4.widgets.optics.ow_mirror.OWMirror",
}

def load_beamline(file_name):
    """Returns the S4Beamline stored in a json file."""
    return load_from_json_file(file_name)

#
# helpers
#
def _refresh(widget, method_names):
    """Calls the widget methods that update the visibility of the GUI after the settings are changed."""
    for name in method_names:
        method = getattr(widget, name, None)
        if method is None: continue
        try:
            method()
        except Exception:
            pass

def _orientation_index(angle_azimuthal_rad):
    """Index of the oe_orientation_angle combo (0, 90, 180, 270 deg or user value) and the user value (deg)."""
    angle = numpy.degrees(angle_azimuthal_rad) % 360.0
    for index, value in enumerate([0.0, 90.0, 180.0, 270.0]):
        if numpy.isclose(angle, value, atol=1e-9) or numpy.isclose(angle, value + 360.0, atol=1e-9):
            return index, 0.0
    return 4, angle

#
# sources
#
def populate_geometrical_source(widget, source):
    """Sets the settings of an OWGeometrical widget from a SourceGeometrical. Returns a list of warnings."""
    warnings = []
    widget.number_of_rays = int(source.get_nrays())
    widget.seed           = int(source.get_seed())

    # spatial type: 0=point, 1=rectangle, 2=ellipse, 3=Gaussian
    widget.spatial_type = int(source._fsour)
    if source._fsour in (1, 2):
        if source._fsour == 1:
            widget.rect_width, widget.rect_height = source._wxsou, source._wzsou
        else:
            widget.ell_semiaxis_x, widget.ell_semiaxis_z = 0.5 * source._wxsou, 0.5 * source._wzsou
    elif source._fsour == 3:
        widget.gauss_sigma_x, widget.gauss_sigma_z = source._sigmax, source._sigmaz

    # depth: 0=off, 1=uniform, 2=Gaussian (both values in _wysou)
    widget.depth = int(source._fsource_depth or 0)
    if widget.depth == 1:   widget.source_depth_y = source._wysou
    elif widget.depth == 2: widget.sigma_y = source._wysou

    # angular distribution. shadow4: 1=flat (collimated if all zero), 2=uniform, 3=Gaussian, 4=cone
    # widget: 0=flat, 1=uniform, 2=Gaussian, 3=cone, 4=collimated
    if source._fdist in (1, 2):
        if source._fdist == 1 and source._hdiv1 == 0 and source._hdiv2 == 0 and source._vdiv1 == 0 and source._vdiv2 == 0:
            widget.angular_distribution = 4
        else:
            widget.angular_distribution = 0 if source._fdist == 1 else 1
            widget.horizontal_div_x_minus = -source._hdiv1
            widget.horizontal_div_x_plus  =  source._hdiv2
            widget.vertical_div_z_minus   = -source._vdiv1
            widget.vertical_div_z_plus    =  source._vdiv2
    elif source._fdist == 3:
        widget.angular_distribution = 2
        widget.horizontal_sigma_x, widget.vertical_sigma_z = source._sigdix, source._sigdiz
    elif source._fdist == 4:
        widget.angular_distribution = 3
        widget.cone_external_half_aperture = source._cone_max
        widget.cone_internal_half_aperture = source._cone_min

    # photon energy: shadow4 _f_color 1..6 -> widget 0..5
    widget.units = int(getattr(source, "_f_phot", 0) or 0)
    f_color = int(source._f_color)
    widget.photon_energy_distribution = f_color - 1
    ph = numpy.atleast_1d(source._ph) if source._ph is not None else numpy.array([])
    if f_color == 1:
        widget.single_line_value = float(ph[0])
    elif f_color in (2, 4):
        if ph.size > 10:
            warnings.append("Source: only the first 10 photon energy lines are used (%d given)" % ph.size)
        widget.number_of_lines = min(ph.size, 10) - 1
        weights = numpy.atleast_1d(source._rl) if (f_color == 4 and source._rl is not None) else numpy.zeros(ph.size)
        for i in range(min(ph.size, 10)):
            setattr(widget, "line_value_%d" % (i + 1), float(ph[i]))
            setattr(widget, "line_int_%d" % (i + 1), float(weights[i]))
    elif f_color == 3:
        widget.uniform_minimum, widget.uniform_maximum = float(ph[0]), float(ph[1])
    elif f_color == 5:
        widget.gaussian_central_value, widget.gaussian_sigma = float(ph[0]), float(ph[1])
    elif f_color == 6:
        file_name = "spectrum_%s.dat" % source.get_name().replace(" ", "_")
        numpy.savetxt(file_name, numpy.column_stack((source._ph_spectrum_abscissas, source._ph_spectrum_ordinates)))
        widget.user_defined_file = file_name
        warnings.append("Source: user-defined spectrum written to file %s" % file_name)

    # polarization
    widget.polarization_degree = float(source._pol_deg)
    widget.phase_diff          = float(numpy.degrees(source._pol_angle))
    widget.coherent_beam       = int(source._f_foher or 0)

    _refresh(widget, ["set_SpatialType", "set_Depth", "set_AngularDistribution", "set_AngularDistributionLimits",
                      "set_PhotonEnergyDistribution", "set_NumberOfLines", "set_OptimizeSource"])
    return warnings

#
# optical elements
#
def _populate_coordinates_and_movements(widget, element):
    coordinates = element.get_coordinates()
    widget.source_plane_distance = float(coordinates.p())
    widget.image_plane_distance  = float(coordinates.q())
    widget.angles_respect_to     = 0           # angles from the normal, in deg
    widget.incidence_angle_deg   = float(numpy.degrees(coordinates.angle_radial()))
    widget.reflection_angle_deg  = float(numpy.degrees(coordinates.angle_radial_out()))
    widget.calculate_incidence_angle_mrad()
    widget.calculate_reflection_angle_mrad()
    widget.oe_orientation_angle, widget.oe_orientation_angle_user_value = _orientation_index(coordinates.angle_azimuthal())

    movements = element.get_movements()
    if movements is None or not movements.f_move:
        widget.oe_movement = 0
    else:
        widget.oe_movement = 1
        widget.oe_movement_angle_um = 2  # rad
        widget.oe_movement_offset_x, widget.oe_movement_offset_y, widget.oe_movement_offset_z = \
            movements.offset_x, movements.offset_y, movements.offset_z
        widget.oe_movement_rotation_x, widget.oe_movement_rotation_y, widget.oe_movement_rotation_z = \
            movements.rotation_x, movements.rotation_y, movements.rotation_z

def _populate_boundary_shape(widget, boundary_shape):
    if boundary_shape is None:
        widget.is_infinite = 1
        return []
    widget.is_infinite = 0
    if isinstance(boundary_shape, Rectangle):
        widget.oe_shape = 0
    elif isinstance(boundary_shape, Ellipse):
        widget.oe_shape = 1
    else:
        widget.is_infinite = 1
        return ["boundary shape %s not supported: set to infinite" % type(boundary_shape).__name__]
    x_left, x_right, y_bottom, y_top = boundary_shape.get_boundaries()
    widget.dim_x_minus, widget.dim_x_plus, widget.dim_y_minus, widget.dim_y_plus = -x_left, x_right, -y_bottom, y_top
    return []

def _populate_mirror_reflectivity(widget, mirror):
    warnings = []
    widget.reflectivity_flag   = int(mirror._f_reflec)
    widget.reflectivity_source = int(mirror._f_refl)
    widget.file_refl           = mirror._file_refl if mirror._file_refl is not None else ""
    n = complex(mirror._refraction_index)
    widget.refraction_index_delta = 1.0 - n.real
    widget.refraction_index_beta  = n.imag
    widget.coating_material  = mirror._coating if mirror._coating else ""
    widget.coating_density   = float(mirror._coating_density)
    widget.coating_roughness = float(mirror._coating_roughness)
    if widget.reflectivity_flag == 1 and widget.reflectivity_source == 6 and mirror._dabax is not None:
        from dabax.dabax_files import dabax_f1f2_files
        try:
            widget.DABAX_F1F2_FILE_INDEX = dabax_f1f2_files().index(mirror._dabax.get_file_f1f2())
        except Exception:
            warnings.append("mirror %s: DABAX f1f2 file not found, using the default" % mirror.get_name())
    return warnings

def populate_mirror(widget, element):
    """Sets the settings of an OWMirror widget from a shadow4 mirror element. Returns a list of warnings."""
    mirror = element.get_optical_element()
    warnings = []
    _populate_coordinates_and_movements(widget, element)
    warnings += _populate_boundary_shape(widget, mirror.get_boundary_shape())
    warnings += _populate_mirror_reflectivity(widget, mirror)
    widget.modified_surface = 0

    if isinstance(mirror, S4PlaneMirror):
        widget.surface_shape_type = 0
    elif isinstance(mirror, S4SphereMirror):
        shape = mirror.get_surface_shape()
        widget.surface_shape_type       = 1
        widget.surface_shape_parameters = 1   # external: the radius is stored in the json
        widget.spherical_radius         = float(shape.get_radius())
        widget.surface_curvature        = int(not shape.get_convexity())   # widget: convexity = not(surface_curvature)
        if isinstance(shape, SphericalCylinder):
            widget.is_cylinder          = 1
            widget.cylinder_orientation = int(shape.get_cylinder_direction())
        else:
            widget.is_cylinder          = 0
    else:
        raise NotImplementedError("mirror type %s not yet supported" % type(mirror).__name__)

    _refresh(widget, ["set_angles_respect_to", "oe_orientation_angle_user", "surface_shape_tab_visibility",
                      "dimensions_tab_visibility", "oe_movement_tab_visibility", "modified_surface_tab_visibility",
                      "reflectivity_tab_visibility"])
    return warnings

POPULATE = {
    "SourceGeometrical"     : populate_geometrical_source,
    "S4PlaneMirrorElement"  : populate_mirror,
    "S4SphereMirrorElement" : populate_mirror,
}

#
# canvas
#
def build_canvas(document, widget_registry, beamline, x0=50.0, y0=150.0, dx=150.0):
    """
    Creates in the canvas document (SchemeEditWidget) the widgets of the shadow4 beamline, with their settings,
    linked by the "Shadow Data" channels. Returns the list of warnings (unsupported elements are skipped).
    """
    warnings = []
    objects = [("source", beamline.get_light_source())] + \
              [("element %d" % (i + 1), beamline.get_beamline_element_at(i)) for i in range(beamline.get_beamline_elements_number())]

    previous_node = None
    x = x0
    for label, obj in objects:
        class_name = type(obj).__name__
        if class_name not in WIDGETS:
            warnings.append("%s: %s not supported, skipped" % (label, class_name))
            continue
        name = obj.get_name() if hasattr(obj, "get_name") else obj.get_optical_element().get_name()
        node = document.createNewNode(widget_registry.widget(WIDGETS[class_name]), title=name, position=(x, y0))
        widget = document.scheme().widget_for_node(node)
        warnings += ["%s (%s): %s" % (label, name, w) for w in POPULATE[class_name](widget, obj)]
        if previous_node is not None:
            from orangecanvas.scheme.link import SchemeLink
            document.addLink(SchemeLink(previous_node, "Shadow Data", node, "Shadow Data"))
        previous_node = node
        x += dx
    return warnings
