try:
    import xraylib as materials_library
except:
    from dabax.dabax_xraylib import DabaxXraylib
    materials_library = DabaxXraylib()

