import os
import unittest
from unittest import mock

from pymediainfo import MediaInfo
from pyfileinfo import PyFileInfo, Medium
from tests import DATA_ROOT


class TestMedium(unittest.TestCase):
    def test_medium(self):
        medium = PyFileInfo(os.path.join(DATA_ROOT, 'empty.mp4'))
        self.assertTrue(isinstance(medium.instance, Medium))

    def test_is_medium(self):
        medium = PyFileInfo(os.path.join(DATA_ROOT, 'empty.mp4'))
        self.assertTrue(medium.is_medium())

    @mock.patch('pymediainfo.MediaInfo.parse')
    @mock.patch('os.path.getsize')
    def test_run_script(self, mock_size, mock_mediainfo):
        medium = PyFileInfo('pooq.mp4')
        self._set_mediainfo_as_pooq(mock_size, mock_mediainfo)
        self.assertEqual(medium.duration, 5022.400)

    @mock.patch('pymediainfo.MediaInfo.parse')
    @mock.patch('os.path.getsize')
    def test_video_track(self, mock_size, mock_mediainfo):
        self._set_mediainfo_as_pooq(mock_size, mock_mediainfo)

        medium = PyFileInfo('pooq.mp4')
        video_track = medium.video_tracks[0]

        self.assertEqual(len(medium.video_tracks), 1)
        self.assertEqual(video_track.codec, 'AVC')
        self.assertEqual(video_track.display_aspect_ratio, '16:9')
        self.assertEqual(video_track.width, 1920)
        self.assertEqual(video_track.height, 1080)
        self.assertEqual(video_track.frame_rate, '29.970')
        self.assertTrue(video_track.progressive)
        self.assertFalse(video_track.interlaced)

    @mock.patch('pymediainfo.MediaInfo.parse')
    @mock.patch('os.path.getsize')
    def test_audio_track(self, mock_size, mock_mediainfo):
        self._set_mediainfo_as_pooq(mock_size, mock_mediainfo)

        medium = PyFileInfo('pooq.mp4')
        audio_track = medium.audio_tracks[0]

        self.assertEqual(len(medium.audio_tracks), 1)
        self.assertEqual(audio_track.codec, 'AAC LC')
        self.assertEqual(audio_track.channels, 2)
        self.assertTrue(audio_track.language is None)
        self.assertEqual(audio_track.compression_mode, 'Lossy')

    @mock.patch('pymediainfo.MediaInfo.parse')
    @mock.patch('os.path.getsize')
    def test_audio_track_with_language(self, mock_size, mock_mediainfo):
        self._set_mediainfo_as_starwars_ep3(mock_size, mock_mediainfo)

        medium = PyFileInfo('starwars-ep3.mp4')
        audio_track = medium.audio_tracks[0]

        self.assertEqual(len(medium.audio_tracks), 6)
        self.assertEqual(audio_track.codec, 'DTS-HD')
        self.assertEqual(audio_track.channels, '7 / 6')
        self.assertEqual(audio_track.compression_mode, 'Lossless / Lossy')
        self.assertEqual(audio_track.language.name, 'English')

    @mock.patch('pymediainfo.MediaInfo.parse')
    @mock.patch('os.path.getsize')
    def test_no_chapter_pooq(self, mock_size, mock_mediainfo):
        self._set_mediainfo_as_pooq(mock_size, mock_mediainfo)

        medium = PyFileInfo('pooq.mp4')
        self.assertEqual(len(medium.chapters), 1)

    @mock.patch('pymediainfo.MediaInfo.parse')
    @mock.patch('os.path.getsize')
    def test_chapter_starwars(self, mock_size, mock_mediainfo):
        self._set_mediainfo_as_starwars_ep3(mock_size, mock_mediainfo)

        medium = PyFileInfo('starwars-ep3.mp4')
        self.assertEqual(len(medium.chapters), 50)

    @mock.patch('pymediainfo.MediaInfo.parse')
    @mock.patch('os.path.getsize')
    def test_track_name(self, mock_size, mock_mediainfo):
        self._set_mediainfo_as_pooq(mock_size, mock_mediainfo)

        medium = PyFileInfo('pooq.mp4')
        self.assertEqual(medium.subtitle_tracks[0].title, 'subtitle')

    @mock.patch('pymediainfo.MediaInfo.parse')
    @mock.patch('os.path.getsize')
    def test_codec_name(self, mock_size, mock_mediainfo):
        self._set_mediainfo_as_starwars_ep3(mock_size, mock_mediainfo)

        medium = PyFileInfo('starwars-ep3.mp4')
        self.assertEqual(medium.subtitle_tracks[0].codec, 'S_HDMV/PGS')

    def _set_mediainfo_as_pooq(self, mock_size, mock_mediainfo):
        media_xml = open(os.path.join(DATA_ROOT, 'mediainfo/pooq.xml')).read()
        mock_mediainfo.return_value = MediaInfo(media_xml)

        mock_size.return_value = 3270214572  # file size

    def _set_mediainfo_as_starwars_ep3(self, mock_size, mock_mediainfo):
        media_xml = open(os.path.join(DATA_ROOT, 'mediainfo/star_wars_e_3.xml')).read()
        mock_mediainfo.return_value = MediaInfo(media_xml)

        mock_size.return_value = 39074393952  # file size
