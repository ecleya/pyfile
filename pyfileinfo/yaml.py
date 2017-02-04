import yaml
from collections.abc import Sequence
from pyfileinfo.file import File


class YAML(File, Sequence):
    def __init__(self, file_path):
        File.__init__(self, file_path)
        Sequence.__init__(self)

        self._instance = None

    def __str__(self):
        return '%s\n%s' % (self.path, yaml.dump(self.instance))

    def __getitem__(self, item):
        return self.instance[item]

    def __len__(self):
        return len(self.instance)

    def __getattr__(self, item):
        return getattr(self.instance, item)

    @staticmethod
    def hint():
        return ['.yml']

    @staticmethod
    def is_valid(path):
        try:
            yaml.load(open(path))
        except Exception as e:
            return False

        return True

    @property
    def instance(self):
        if self._instance is None:
            self._instance = yaml.load(open(self.path))

        return self._instance
