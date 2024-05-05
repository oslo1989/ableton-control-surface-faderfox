from ableton.v2.control_surface import ControlSurface


def create_instance(c_instance: ControlSurface) -> ControlSurface:
    from .control_surface import FaderFoxSurface

    return FaderFoxSurface(c_instance)
