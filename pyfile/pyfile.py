import os
import re
import shutil
import hashlib
import unicodedata
from functools import partial


__all__ = ['pyfile', 'File', 'Directory']


def pyfile(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError()

    ext = os.path.splitext(file_path)[1].lower()
    classes = [class_ for class_ in File.__subclasses__() if ext in class_.hint()] + \
              [class_ for class_ in File.__subclasses__() if ext not in class_.hint()]
    classes.remove(Directory)
    classes.append(Directory)

    for class_ in classes:
        inst = class_.from_path(file_path)
        if inst is not None:
            return inst

    return File(file_path)


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
        return self.path == other.path

    def __str__(self):
        return self._path

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
        return pyfile(os.path.split(self._path)[0])

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

    def is_equal(self, other):
        if type(other) is not str and not isinstance(other, File):
            return False

        if type(other) is str:
            other = pyfile(other)

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

    def is_hidden(self):
        return self._name[0] in ['.', '$', '@']

    def is_exists(self):
        return os.path.exists(self.path)

    def is_dir(self):
        return False

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
        return pyfile(destination)

    def remove(self):
        os.remove(self.path)

    def files(self, include_hidden_files=False):
        return []

    def walk(self, include_hidden_files=False):
        return []


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

        result = [pyfile(os.path.join(self.path, filename)) for filename in os.listdir(self._path)]
        result.sort()
        if include_hidden_files:
            return result

        return [file for file in result if not file.is_hidden()]

    def walk(self, include_hidden_files=False):
        result = []
        for file in self.files(include_hidden_files):
            if file.is_hidden() and not include_hidden_files:
                continue

            result.append(file)
            if file.is_dir():
                result.extend(file.walk())

        result.sort()

        return result

    def copy_to(self, destination):
        body, _ = os.path.split(destination)
        if not os.path.exists(body):
            os.makedirs(body)

        print('type:info\tcommand:copy\tsrc:%s\tdst:%s' % (self.path, destination))
        shutil.copytree(self._path, destination)
        return pyfile(destination)

    def remove(self):
        shutil.rmtree(self.path)

    def is_dir(self):
        return True
