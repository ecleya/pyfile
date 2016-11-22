import os
import re
import json
import shutil
import hashlib
import pycountry
import subprocess
import unicodedata
from functools import partial
from fractions import Fraction
from xml.etree import ElementTree


__all__ = ['load', 'File', 'Directory', 'Json', 'Image', 'Medium']


def load(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError()

    ext = os.path.splitext(file_path)[1].lower()
    classes = [class_ for class_ in _subclasses() if ext in class_.hint()] + \
              [class_ for class_ in _subclasses() if ext not in class_.hint()]

    for class_ in classes:
        inst = class_.from_path(file_path)
        if inst is not None:
            return inst

    return File(file_path)


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


class File:
    def __init__(self, file_path):
        self._path = unicodedata.normalize('NFC', file_path)
        _, self._name = os.path.split(self._path)

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
        if type(other) is not str and not isinstance(other, File):
            return False

        if type(other) is str:
            other = load(other)

        if self.path == other.path:
            return True

        if self.size != other.size:
            return False

        block_size = 4096
        lhs = open(self.path, 'rb')
        rhs = open(other.path, 'rb')

        while True:
            lhs_block = lhs.read(block_size)
            rhs_block = rhs.read(block_size)

            if lhs_block != rhs_block:
                return False

            if lhs_block == b'':
                break

        return True

    def __str__(self):
        return self._path

    def __getattr__(self, item):
        for class_ in File.__subclasses__():
            if item == 'is_{}'.format(class_.__name__.lower()):
                return lambda: isinstance(self, class_)

        raise AttributeError()

    @staticmethod
    def replace_unusable_char(file_name):
        invalid_chars = '\\/:*?<>|"'
        for invalid_char in invalid_chars:
            file_name = file_name.replace(invalid_char, '_')

        if file_name[0] == '.':
            file_name = '_' + file_name[1:]

        return file_name

    @staticmethod
    def hint():
        return []

    @property
    def body(self):
        return load(os.path.split(self._path)[0])

    @property
    def path(self):
        return self._path

    @property
    def name(self):
        return self._name

    @property
    def size(self):
        return os.path.getsize(self.path)

    @property
    def extension(self):
        return os.path.splitext(self._path)[1].lower()

    @property
    def md5(self):
        return self._calculate_hash(hashlib.md5)

    def _calculate_hash(self, hash_algorithm):
        with open(self.path, mode='rb') as f:
            digest = hash_algorithm()
            for buf in iter(partial(f.read, 128), b''):
                digest.update(buf)

        return digest.digest()

    def relpath(self, start):
        return os.path.relpath(self.path, start)

    def is_hidden(self):
        return self._name[0] in ['.', '$', '@']

    def is_exists(self):
        return os.path.exists(self.path)

    def move_to(self, destination):
        body, _ = os.path.split(destination)
        if not os.path.exists(body):
            os.makedirs(body)

        print('type:info\tcommand:file move\tsrc:%s\tdst:%s' % (self.path, destination))
        shutil.move(self._path, destination)
        self._path = destination

    def copy_to(self, destination):
        body, _ = os.path.split(destination)
        if not os.path.exists(body):
            os.makedirs(body)

        print('type:info\tcommand:file copy\tsrc:%s\tdst:%s' % (self.path, destination))
        shutil.copy(self._path, destination)
        return load(destination)

    def remove(self):
        os.remove(self.path)


class Directory(File):
    def __init__(self, file_path):
        File.__init__(self, file_path)

    @staticmethod
    def from_path(file_path):
        if os.path.isdir(file_path):
            return Directory(file_path)

        return None

    def files(self, include_hidden_files=False):
        if not self.is_exists():
            return []

        files = [File(os.path.join(self.path, filename)) for filename in os.listdir(self._path)]
        files.sort()
        for file in files:
            if file.is_hidden() and not include_hidden_files:
                continue

            yield load(file.path)

    def walk(self, include_hidden_files=False):
        for file in self.files(include_hidden_files):
            if file.is_hidden() and not include_hidden_files:
                continue

            yield file
            if file.is_directory():
                yield from file.walk(include_hidden_files)

    @property
    def size(self):
        return sum([file.size for file in self.files(True)])

    def copy_to(self, destination):
        body, _ = os.path.split(destination)
        if not os.path.exists(body):
            os.makedirs(body)

        print('type:info\tcommand:copy\tsrc:%s\tdst:%s' % (self.path, destination))
        shutil.copytree(self._path, destination)
        return load(destination)

    def remove(self):
        shutil.rmtree(self.path)


class Json(File):
    def __init__(self, file_path):
        File.__init__(self, file_path)

    def __str__(self):
        return '%s\n%s' % (self.path,
                           json.dumps(self, indent=4, separators=(',', ': '),
                                      ensure_ascii=False, sort_keys=True))

    @staticmethod
    def from_path(file_path):
        try:
            json_value = json.load(open(file_path))
        except Exception as e:
            return None

        if type(json_value) is dict:
            return _Dict(file_path)

        return _List(file_path)

    def dump(self):
        json.dump(self, open(self.path, 'w', encoding='utf8'),
                  indent=4, separators=(',', ': '), ensure_ascii=False, sort_keys=True)


class _Dict(Json, dict):
    def __init__(self, file_path):
        Json.__init__(self, file_path)
        dict.__init__(self, json.load(open(self.path)) if self.is_exists() else {})


class _List(Json, list):
    def __init__(self, file_path):
        File.__init__(self, file_path)
        list.__init__(self, json.load(open(self.path)) if self.is_exists() else [])


class Image(File):
    def __init__(self, file_path):
        File.__init__(self, file_path)

        self._image = None

    def __getattr__(self, item):
        if self._image is None:
            from PIL import Image as PILImage
            self._image = PILImage.open(self.path)

        try:
            return getattr(self._image, item)
        except AttributeError:
            if item == 'resolution':
                return self._image.size

            return File.__getattr__(self, item)

    @staticmethod
    def from_path(file_path):
        try:
            from PIL import Image as PILImage
            PILImage.open(file_path)
        except Exception as e:
            return None

        return Image(file_path)

    @property
    def image(self):
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
