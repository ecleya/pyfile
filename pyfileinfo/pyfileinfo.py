import os
import re
import json
import filecmp
import hashlib
import pycountry
import subprocess
import unicodedata
from functools import partial
from fractions import Fraction
from xml.etree import ElementTree
from PIL import Image as PILImage
from collections.abc import Sequence


__all__ = ['PyFileInfo', 'File', 'Directory', 'Json', 'Image', 'Medium']


class PyFileInfo(Sequence):
    def __init__(self, path):
        Sequence.__init__(self)

        self._path = unicodedata.normalize('NFC', path)
        self._instance = None

    def __lt__(self, other):
        def split_by_number(file_path):
            def to_int_if_possible(c):
                try:
                    return int(c)
                except:
                    return c.lower()

            return [to_int_if_possible(c) for c in re.split('([0-9]+)', file_path)]

        return split_by_number(self.path) < split_by_number(other.path)

    def __hash__(self):
        return self._path.__hash__()

    def __eq__(self, other):
        if type(other) is str:
            return filecmp.cmp(self.path, other, False)

        if isinstance(other, PyFileInfo):
            return filecmp.cmp(self.path, other.path, False)

        return False

    def __str__(self):
        return self._path

    def __getattr__(self, item):
        for class_ in File.__subclasses__():
            if item == 'is_{}'.format(class_.__name__.lower()):
                if self._instance is None:
                    return lambda: class_.is_valid(self.path)

                return lambda: isinstance(self.instance, class_)

        return getattr(self.instance, item)

    def __getitem__(self, item):
        return self.instance[item]

    def __len__(self):
        return len(self.instance)

    def is_hidden(self):
        return self.name[0] in ['.', '$', '@']

    def is_exists(self):
        return os.path.exists(self.path)

    @property
    def instance(self):
        if self._instance is None:
            classes = [class_ for class_ in _subclasses() if self.extension in class_.hint()] + \
                      [class_ for class_ in _subclasses() if self.extension not in class_.hint()]

            self._instance = File(self.path)
            for class_ in classes:
                if not class_.is_valid(self.path):
                    continue

                self._instance = class_(self.path)
                break

        return self._instance

    @property
    def path(self):
        return self._path

    @property
    def extension(self):
        return os.path.splitext(self.path)[1]

    @property
    def name(self):
        return os.path.split(self.path)[1]

    @property
    def body(self):
        return PyFileInfo(os.path.split(self.path)[0])

    @property
    def md5(self):
        return self._calculate_hash(hashlib.md5)

    def relpath(self, start):
        return os.path.relpath(self.path, start)

    def _calculate_hash(self, hash_algorithm):
        with open(self.path, mode='rb') as f:
            digest = hash_algorithm()
            for buf in iter(partial(f.read, 128), b''):
                digest.update(buf)

        return digest.digest()


class File:
    def __init__(self, path):
        self._path = path

    def __str__(self):
        return self._path

    @staticmethod
    def is_valid(path):
        return True

    @staticmethod
    def hint():
        return []

    @property
    def path(self):
        return self._path

    @property
    def size(self):
        return os.path.getsize(self.path)


class Directory(File):
    def __init__(self, file_path):
        File.__init__(self, file_path)

    @staticmethod
    def is_valid(path):
        return os.path.isdir(path)

    def files_in(self, include_hidden_file=False, recursive=False):
        files = [PyFileInfo(os.path.join(self.path, filename))
                 for filename in os.listdir(self.path)]
        files.sort()

        for file in files:
            if file.is_hidden() and not include_hidden_file:
                continue

            yield file
            if recursive and file.is_directory():
                yield from file.files_in(include_hidden_file=include_hidden_file,
                                         recursive=recursive)

    @property
    def size(self):
        return sum([file.size for file in self.files_in(include_hidden_file=True)])


class Json(File, Sequence):
    def __init__(self, file_path):
        File.__init__(self, file_path)
        Sequence.__init__(self)

        self._instance = None

    def __str__(self):
        return '%s\n%s' % (self.path,
                           json.dumps(self.instance, indent=4, separators=(',', ': '),
                                      ensure_ascii=False, sort_keys=True))

    def __getitem__(self, item):
        return self.instance[item]

    def __len__(self):
        return len(self.instance)

    @staticmethod
    def is_valid(path):
        try:
            json.load(open(path))
        except Exception as e:
            return False

        return True

    @property
    def instance(self):
        if self._instance is None:
            self._instance = json.load(open(self.path))

        return self._instance


class Image(File):
    def __init__(self, file_path):
        File.__init__(self, file_path)

        self._image = None

    def __getattr__(self, item):
        try:
            return getattr(self.image, item)
        except AttributeError:
            if item == 'resolution':
                return self.image.size

            return File.__getattr__(self, item)

    @staticmethod
    def is_valid(path):
        try:
            from PIL import Image as PILImage
            PILImage.open(path)
        except Exception as e:
            return False

        return True

    @property
    def image(self):
        if self._image is None:
            self._image = PILImage.open(self.path)

        return self._image

    @property
    def resolution(self):
        return self._image.size

    @staticmethod
    def hint():
        return ['.jpg', '.png', '.jpeg', '.bmp']


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


def _subclasses():
    return _custom_subclasses() + _default_subclasses()


def _custom_subclasses():
    return [class_ for class_ in File.__subclasses__() if class_ not in _default_subclasses()]


def _default_subclasses():
    return [Json, Image, Medium, Directory]


def _which(name):
    folders = os.environ.get('PATH', os.defpath).split(':')
    for folder in folders:
        file_path = os.path.join(folder, name)
        if os.path.exists(file_path) and os.access(file_path, os.X_OK):
            return file_path

    return None
