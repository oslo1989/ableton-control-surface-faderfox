from ableton.v2.control_surface import Skin
from ableton.v2.control_surface.elements import Color, SysexRGBColor


# this seems to be necessasry to get the skin to load,
# which is is some ableton feature that I don't understand fully.
# it is probably related to color mapping and controllers / surfaces
# that have pads that can display colors.
class Colors:
    class DefaultButton:
        On = Color(127)
        Off = Color(0)
        Disabled = Color(0)

    class Transport:
        PlayOn = Color(127)
        PlayOff = Color(0)
        StopOn = Color(127)
        StopOff = Color(0)

    class Session:
        ClipStopped = SysexRGBColor((31, 31, 0))
        ClipStarted = SysexRGBColor((0, 31, 0))
        ClipRecording = SysexRGBColor((31, 0, 0))
        ClipTriggeredPlay = SysexRGBColor((0, 31, 0))
        ClipTriggeredRecord = SysexRGBColor((31, 0, 0))
        ClipEmpty = SysexRGBColor((0, 0, 0))
        StopClip = Color(0)
        StopClipTriggered = Color(0)
        StopClipDisabled = Color(0)
        StoppedClip = Color(0)

    class Automation:
        On = Color(127)
        Off = Color(0)

    class View:
        Session = Color(0)
        Arranger = Color(127)

    class Mixer:
        MuteOn = Color(127)
        MuteOff = Color(0)
        SoloOn = Color(127)
        SoloOff = Color(0)
        ArmOn = Color(127)
        ArmOff = Color(0)
        MonitorIn = Color(127)
        MonitorAuto = Color(127)
        MonitorOff = Color(0)

        ClipStopped = Color(127)
        ClipStarted = Color(63)
        ClipEmpty = Color(0)

        StopOn = Color(127)
        StopOff = Color(0)

        CrossfadeA = Color(0)
        CrossfadeB = Color(127)
        CrossfadeOff = Color(64)


default_skin = Skin(Colors)
