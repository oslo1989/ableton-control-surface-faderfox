from __future__ import annotations

import logging
from typing import Any, TypeVar

import Live
from ableton.v2.base import const, depends, inject
from ableton.v2.control_surface import MIDI_CC_TYPE, MIDI_NOTE_TYPE, ControlSurface
from ableton.v2.control_surface.components import MixerComponent, SessionRingComponent, TransportComponent
from ableton.v2.control_surface.elements import ButtonElement, EncoderElement
from Live.Song import Song
from Live.Track import Track

from FaderFoxOslo1989Surface.skin_default import default_skin

MIDI_MAX_VALUE = 127

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("FaderFoxOslo1989Surface")

T = TypeVar("T", bound=object)

QUARTER = 0.25
HALF = 0.5
THREE_QUARTERS = 0.75
FIRST_BEAT = 1
SECOND_BEAT = 2
THIRD_BEAT = 3


def numbers(base: int, base_midi_channel: int, num_tracks: int) -> list[tuple[int, int, int]]:
    return [(index, base_midi_channel + (index // 8), base + (index % 8)) for index in range(num_tracks)]


def index_of(ls: list[T], obj: T) -> int:
    for idx, el in enumerate(ls):
        if el == obj:
            return idx
    return -1


class TrackSelectEncoder(EncoderElement):
    def __init__(
        self,
        song: Song,
        midi_type: int,
        midi_channel: int,
        midi_identifier: int,
        **k: dict[str, Any],
    ) -> None:
        super().__init__(
            midi_type,
            midi_channel,
            midi_identifier,
            Live.MidiMap.MapMode.relative_smooth_two_compliment,
            **k,
        )
        self.song = song
        self.song.view.add_selected_track_listener(self.on_selected_track_changed)
        self.on_selected_track_changed()

    def on_selected_track_changed(self) -> None:
        idx = index_of(self.song.tracks, self.song.view.selected_track)
        logger.info(f"on_selected_track_changed: {idx}")
        if idx == -1:
            # this means we have selected a track that is not in the list of tracks,
            # but a return track or master track
            return
        self.send_value(idx + 1)

    def script_wants_forwarding(self) -> bool:
        return True

    def receive_value(self, value: int) -> None:
        logger.info(f"receive_value: {value}")
        sel_idx = index_of(self.song.tracks, self.song.view.selected_track)
        if sel_idx == -1:
            # this means we have selected a track that is not in the list of tracks,
            # but a return track or master track
            self.song.view.selected_track = self.song.tracks[-1]
            return
        inc = 0
        if value == MIDI_MAX_VALUE and sel_idx > 0:
            inc = -1
        elif value == 1 and sel_idx < len(self.song.tracks) - 1:
            inc = 1
        self.song.view.selected_track = self.song.tracks[sel_idx + inc]

    def disconnect(self) -> None:
        self.song.view.remove_selected_track_listener(self.on_selected_track_changed)


@depends(skin=None)
def create_button(channel: int, identifier: int, **k: dict[str, Any]) -> ButtonElement:
    return ButtonElement(True, MIDI_NOTE_TYPE, channel, identifier, **k)  # noqa: FBT003


def create_encoder(channel: int, identifier: int) -> EncoderElement:
    return EncoderElement(MIDI_CC_TYPE, channel, identifier, Live.MidiMap.MapMode.absolute)


def button_base(base_channel: int, base_identifier: int, num_tracks: int) -> list[ButtonElement]:
    return [
        create_button(channel, identifier)
        for (index, channel, identifier) in numbers(base_identifier, base_channel, num_tracks)
    ]


def encoder_base(base_channel: int, base_identifier: int, num_tracks: int) -> list[EncoderElement]:
    return [
        create_encoder(channel, identifier)
        for (index, channel, identifier) in numbers(base_identifier, base_channel, num_tracks)
    ]


def send_row_base(base_channel: int, base_identifiers: list[int], num_tracks: int) -> list[list[EncoderElement]]:
    send_rows = [encoder_base(base_channel, i, num_tracks) for i in base_identifiers]
    send_row_pairs = []
    for i in range(num_tracks):
        pairs = []
        for t in range(len(base_identifiers)):
            pairs.append(send_rows[t][i])
        send_row_pairs.append(pairs)
    return send_row_pairs


class FaderFoxMixerComponent(MixerComponent):
    def __init__(self, parameter_encoders: list[EncoderElement], *a: list[Any], **k: dict[str, Any]) -> None:
        super().__init__(*a, **k)
        self._parameter_encoders = parameter_encoders
        self._reassign_tracks()

    def _reassign_tracks(self) -> None:
        super()._reassign_tracks()
        for s in range(len(self._channel_strips)):
            track: Track = self._channel_strips[s].track
            if track.devices:
                device = track.devices[0]
                if device.parameters and len(device.parameters) > 1:  # noqa:SIM102
                    # just a small workaround since this method is also called
                    # when the mixer is created and the _parameter_encoders are not yet set
                    # since they are created in the constructor
                    if hasattr(self, "_parameter_encoders"):
                        self._parameter_encoders[s].connect_to(device.parameters[1])


class FaderFoxSurface(ControlSurface):
    def __init__(self, c_instance: ControlSurface) -> None:
        super().__init__(c_instance)
        self.c_instance = c_instance
        self._num_tracks = 11
        self._num_scenes = 1

        self._sixteenth_beat = 1
        self._quarter_beat = 1
        self._whole_beat = 1
        self._last_song_time = -1.0
        self.song.add_current_song_time_listener(self._song_time_changed)

        with self.component_guard():
            with inject(skin=const(default_skin)).everywhere():
                self._controls = [
                    TrackSelectEncoder(self.song, MIDI_CC_TYPE, 12, 59),
                    *[create_encoder(13, i) for i in [27, 19, 11, 3]],
                ]
                self._session_ring = SessionRingComponent(
                    num_tracks=self._num_tracks,
                    num_scenes=self._num_scenes,
                )
                self._mixer = FaderFoxMixerComponent(
                    encoder_base(12, 8, self._num_tracks),
                    tracks_provider=self._session_ring,
                )
                self._transport = TransportComponent()
                self._mixer.master_strip().set_volume_control(create_encoder(13, 43))
                self._mixer.master_strip().set_pan_control(create_encoder(13, 35))

                self._mixer.set_volume_controls(encoder_base(12, 40, self._num_tracks))
                self._mixer.set_pan_controls(encoder_base(12, 32, self._num_tracks))
                send_row_bases = send_row_base(12, [16, 24], self._num_tracks)
                for t in range(self._num_tracks):
                    self._mixer.channel_strip(t).set_send_controls(send_row_bases[t])

                self._mixer.set_mute_buttons(button_base(12, 104, self._num_tracks))
                self._play_button = create_button(13, 107)
                self._transport.play_button.set_control_element(self._play_button)
                for rt in range(len(self.song.return_tracks)):
                    self._controls[rt + 1].connect_to(self.song.return_tracks[rt].mixer_device.volume)

            self.song.view.add_selected_track_listener(self._on_selected_track_changed)
            self.song.add_tracks_listener(self._on_selected_track_changed)
        if self.song.view.selected_track not in self.song.tracks:
            self.song.view.selected_track = self.song.tracks[0]
        self._on_selected_track_changed()

    def _on_selected_track_changed(self) -> None:
        sel_idx = index_of(self.song.tracks, self.song.view.selected_track)
        if sel_idx == -1:
            # this means we have selected a track that is not in the list of tracks,
            # but a return track or master track
            return
        if sel_idx >= self._session_ring.track_offset + self._num_tracks:
            # if the selected track is greater than the track offset + the number of tracks,
            # set the track offset to the selected track - the number of tracks + 1
            self._session_ring.track_offset = sel_idx - self._num_tracks + 1
        elif sel_idx <= self._session_ring.track_offset:
            # if the track inex is less than the track offset, set the track offset to the selected track
            self._session_ring.track_offset = sel_idx
        elif self._session_ring.track_offset + self._num_tracks > len(self.song.tracks):
            # cant do negative track offset
            self._session_ring.track_offset = max(len(self.song.tracks) - self._num_tracks, 0)
        self.song.view.selected_track = self.song.tracks[sel_idx]

    def _song_time_changed(self) -> None:
        if (self.song.current_song_time < self._last_song_time) or (
            int(self.song.current_song_time) > int(self._last_song_time)
        ):
            self._quarter_beat = int(self.song.current_song_time) % 4 + 1
            if self._quarter_beat == 1:
                self._whole_beat = int(self.song.current_song_time / 4) + 1
                self._trigger_whole_beat_listeners()
            self._sixteenth_beat = 1
            self._trigger_quarter_beat_listeners()
            self._trigger_sixteenth_beat_listeners()
        if self.song.current_song_time > QUARTER and self._sixteenth_beat == FIRST_BEAT:
            self._sixteenth_beat = 2
            self._trigger_sixteenth_beat_listeners()
        elif self.song.current_song_time > HALF and self._sixteenth_beat == SECOND_BEAT:
            self._sixteenth_beat = 3
            self._trigger_sixteenth_beat_listeners()
        elif self.song.current_song_time > THREE_QUARTERS and self._sixteenth_beat == THIRD_BEAT:
            self._sixteenth_beat = 4
            self._trigger_sixteenth_beat_listeners()

        self._last_song_time = self.song.current_song_time

    def _trigger_sixteenth_beat_listeners(self) -> None:
        pass

    def _trigger_quarter_beat_listeners(self) -> None:
        self._play_button.send_value(127)
        self.schedule_message(2, lambda: self._play_button.send_value(0))

    def _trigger_whole_beat_listeners(self) -> None:
        pass

    def disconnect(self) -> None:
        self.song.view.remove_selected_track_listener(self._on_selected_track_changed)
        self.song.remove_tracks_listener(self._on_selected_track_changed)
        self._transport.disconnect()
        self._mixer.disconnect()
        self._session_ring.disconnect()
        self._mixer.disconnect()
        for c in self._controls:
            c.disconnect()
        super().disconnect()
