pyfileinfo
==========

pyfileinfo is file's metadata reader. You can read basic information about json, yaml, image, media and etcs. Simply create PyFileInfo object, then you can get what you want.


Installation
------------

    pip install pyfileinfo

Examples
--------

..
>>> from pyfileinfo import PyFileInfo
>>> file = PyFileInfo('filepath')
>>> file.size
937

This is it. Now, you can get detailed information about that file. Such as size or md5.


..
>>> from pyfileinfo import PyFileInfo
>>> file = PyFileInfo('directory')
>>> file.files_in()
<generator object Directory.files_in at ...>
>>> list(file.files_in())
[<PyFileInfo object at ...>, <PyFileInfo object at ...>, ...]

You can get files in directory too.


..
>>> from pyfileinfo import PyFileInfo
>>> file = PyFileInfo('src.png')
>>> file.resolution
(1024, 768)
>>> file.format
'JPEG'

If file is image, you can read resolution, format, mode and etcs. In fact, you can reach every attribute that pillow's Image class can get.


..
>>> from pyfileinfo import PyFileInfo
>>> file = PyFileInfo('list.json')
>>> file[0]
7
>>> file = PyFileInfo('dict.yaml')
>>> file['key']
'value'

You can read json or yaml file as well.


..
>>> from pyfileinfo import PyFileInfo
>>> file = PyFileInfo('vid.mkv')
>>> file.width
1920
>>> file.video_tracks[0].codec
'AVC'
>>> file.audio_tracks[0].channels
2

If you have mediainfo, then you can read media file as well.
