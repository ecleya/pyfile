import os
import pycountry
import subprocess
from fractions import Fraction
from pyfileinfo.file import File
from xml.etree import ElementTree


class Medium(File):
    def __init__(self, file_path):
        File.__init__(self, file_path)

        self._video_tracks = None
        self._audio_tracks = None
        self._subtitle_tracks = None
        self._duration = None
        self._mean_volume = None

        mediainfo_path = _which('mediainfo')
        cmd = [mediainfo_path, '--Output=XML', '-f', self.path]
        out, _ = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        self._xml_root = ElementTree.fromstring(out.decode('utf8', errors='ignore'))

    @staticmethod
    def from_path(file_path):
        if os.path.isdir(file_path):
            return None

        try:
            medium = Medium(file_path)
            if len(medium.video_tracks) > 0 or len(medium.audio_tracks) > 0:
                return medium

            return None
        except:
            return None

    @staticmethod
    def is_valid(path):
        if os.path.isdir(path):
            return False

        try:
            medium = Medium(path)
        except:
            return False

        return len(medium.video_tracks) > 0 or len(medium.audio_tracks) > 0

    @property
    def xml_root(self):
        return self._xml_root

    @property
    def title(self):
        return self.xml_root.find('File').find('track').find('Title').text

    @property
    def album(self):
        return self.xml_root.find('File').find('track').find('Album').text

    @property
    def album_performer(self):
        if self.xml_root.find('File').find('track').find('Album_Performer') is None:
            return None

        return self.xml_root.find('File').find('track').find('Album_Performer').text

    @property
    def performer(self):
        return self.xml_root.find('File').find('track').find('Performer').text

    @property
    def track_name(self):
        return self.xml_root.find('File').find('track').find('Track_name').text

    @property
    def track_name_position(self):
        return self.xml_root.find('File').find('track').find('Track_name_Position').text

    @property
    def part_position(self):
        return self.xml_root.find('File').find('track').find('Part_Position').text

    @property
    def video_tracks(self):
        if self._video_tracks is None:
            tracks = [track for track in self.xml_root.find('File').findall('track')]
            self._video_tracks = [_VideoTrack(element) for element in tracks
                                  if element.attrib['type'] == 'Video']

        return self._video_tracks

    @property
    def audio_tracks(self):
        if self._audio_tracks is None:
            tracks = [track for track in self.xml_root.find('File').findall('track')]
            self._audio_tracks = [_AudioTrack(element) for element in tracks
                                  if element.attrib['type'] == 'Audio']

        return self._audio_tracks

    @property
    def subtitle_tracks(self):
        if self._subtitle_tracks is None:
            tracks = [track for track in self.xml_root.find('File').findall('track')]
            self._subtitle_tracks = [_SubtitleTrack(element) for element in tracks
                                     if element.attrib['type'] == 'Text']

        return self._subtitle_tracks

    @property
    def chapters(self):
        tracks = [track for track in self.xml_root.find('File').findall('track')
                  if track.attrib['type'] == 'Menu']

        if len(tracks) == 0:
            return [{'Number': 1, 'Start': 0, 'Duration': self.duration}]

        chapters = []
        chapter_number = 1

        for element in tracks[0]:
            if len(element.tag.split('_')) != 4:
                continue

            _, hour, minutes, seconds = element.tag.split('_')
            chapters.append({'Number': chapter_number,
                             'Start': float(hour)*3600 + float(minutes)*60 + float(seconds)/1000,
                             'Duration': None})

            chapter_number += 1

        chapters.append({'Start': self.duration})
        for idx in range(len(chapters) - 1):
            chapters[idx]['Duration'] = chapters[idx + 1]['Start'] - chapters[idx]['Start']

        chapters.pop(-1)
        return chapters

    @property
    def main_video_track(self):
        return self.video_tracks[0]

    @property
    def main_audio_track(self):
        if len(self.audio_tracks) == 0:
            return None

        return self.audio_tracks[0]

    @property
    def width(self):
        return self.main_video_track.width

    @property
    def height(self):
        return self.main_video_track.height

    @property
    def interlaced(self):
        return self.main_video_track.interlaced

    @property
    def duration(self):
        return float(self.xml_root.find('File').find('track').find('Duration').text)/1000

    @staticmethod
    def hint():
        return ['.avi', '.mov', '.mp4', '.m4v', '.m4a', '.mkv', '.mpg', '.mpeg', '.ts', '.m2ts']

    def is_audio_track_empty(self):
        return len(self.audio_tracks) == 0

    def is_hd(self):
        return self.width >= 1200 or self.height >= 700

    def is_video(self):
        return len(self.video_tracks) > 0

    def is_audio(self):
        return not self.is_video() and len(self.audio_tracks) > 0


class _Track:
    def __init__(self, element):
        self._element = element

    @property
    def stream_id(self):
        return min([int(sid.text) for sid in self._element.findall('Stream_identifier')])

    @property
    def language(self):
        for tag in self._element.findall('Language'):
            try:
                return pycountry.languages.get(name=tag.text)
            except:
                pass

        return None


class _VideoTrack(_Track):
    @property
    def codec(self):
        return self._element.find('Codec').text

    @property
    def display_aspect_ratio(self):
        values = [tag.text for tag in self._element.findall('Display_aspect_ratio')]
        for value in values:
            if ':' in value:
                return value

        if len(values) == 0:
            return None

        return values[0]

    @property
    def width(self):
        return int(self._element.find('Width').text)

    @property
    def height(self):
        return int(self._element.find('Height').text)

    @property
    def display_width(self):
        aspect_ratio = self.display_aspect_ratio
        if ':' in aspect_ratio:
            w_ratio, h_ratio = self.display_aspect_ratio.split(':')
        else:
            fraction = Fraction(self.display_aspect_ratio)
            w_ratio, h_ratio = fraction.numerator, fraction.denominator

        return int(self.height * Fraction(w_ratio) / Fraction(h_ratio))

    @property
    def display_height(self):
        return int(self._element.find('Height').text)

    @property
    def interlaced(self):
        if self._element.find('Scan_type') is None:
            return False

        return self._element.find('Scan_type').text != 'Progressive'

    @property
    def progressive(self):
        return not self.interlaced

    @property
    def frame_rate(self):
        if self._element.find('Frame_rate') is None:
            return float(self._element.find('Original_frame_rate').text)

        return float(self._element.find('Frame_rate').text)

    @property
    def frame_count(self):
        return int(self._element.find('Frame_count').text)


class _AudioTrack(_Track):
    @property
    def codec(self):
        return self._element.find('Codec').text

    @property
    def channels(self):
        return self._element.find('Channel_s_').text

    @property
    def compression_mode(self):
        if self._element.find('Compression_mode') is None:
            return None

        return self._element.find('Compression_mode').text


class _SubtitleTrack(_Track):
    @property
    def format(self):
        return self._element.find('Format').text


def _which(name):
    folders = os.environ.get('PATH', os.defpath).split(':')
    for folder in folders:
        file_path = os.path.join(folder, name)
        if os.path.exists(file_path) and os.access(file_path, os.X_OK):
            return file_path

    return None
