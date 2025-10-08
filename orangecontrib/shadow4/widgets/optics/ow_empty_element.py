from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from shadow4.beamline.optical_elements.ideal_elements.s4_empty import S4Empty, S4EmptyElement

from orangecontrib.shadow4.widgets.gui.ow_optical_element import OWOpticalElement

class OWEmptyElement(OWOpticalElement):
    name        = "Empty Element"
    description = "Shadow Empty Element"
    icon        = "icons/empty_element.png"

    priority = 1.4

    def __init__(self): super().__init__(has_footprint=False)
    def get_optical_element_instance(self): return S4Empty(name=self.getNode().title)
    def get_beamline_element_instance(self): return S4EmptyElement()

add_widget_parameters_to_module(__name__)