import os
import unittest
from unittest import mock

from pyfileinfo import PyFileInfo, Medium
from tests import DATA_ROOT


class TestMedium(unittest.TestCase):
    def test_medium(self):
        medium = PyFileInfo(os.path.join(DATA_ROOT, 'empty.mp4'))
        self.assertTrue(isinstance(medium.instance, Medium))

    def test_is_medium(self):
        medium = PyFileInfo(os.path.join(DATA_ROOT, 'empty.mp4'))
        self.assertTrue(medium.is_medium())

    @mock.patch('os.path.exists')
    @mock.patch('subprocess.Popen')
    def test_run_script(self, mock_popen, mock_exists):
        self._set_mediainfo_as_pooq(mock_popen, mock_exists)

        medium = PyFileInfo('pooq.mp4')
        self.assertEqual(medium.duration, 5022.400)

    @mock.patch('os.path.exists')
    @mock.patch('subprocess.Popen')
    def test_video_track(self, mock_popen, mock_exists):
        self._set_mediainfo_as_pooq(mock_popen, mock_exists)

        medium = PyFileInfo('pooq.mp4')
        video_track = medium.video_tracks[0]

        self.assertEqual(len(medium.video_tracks), 1)
        self.assertEqual(video_track.codec, 'AVC')
        self.assertEqual(video_track.display_aspect_ratio, '16:9')
        self.assertEqual(video_track.width, 1920)
        self.assertEqual(video_track.height, 1080)
        self.assertEqual(video_track.frame_rate, 29.970)
        self.assertTrue(video_track.progressive)
        self.assertFalse(video_track.interlaced)

    @mock.patch('os.path.exists')
    @mock.patch('subprocess.Popen')
    def test_audio_track(self, mock_popen, mock_exists):
        self._set_mediainfo_as_pooq(mock_popen, mock_exists)

        medium = PyFileInfo('pooq.mp4')
        audio_track = medium.audio_tracks[0]

        self.assertEqual(len(medium.audio_tracks), 1)
        self.assertEqual(audio_track.codec, 'AAC LC')
        self.assertEqual(audio_track.channels, '2')
        self.assertTrue(audio_track.language is None)
        self.assertEqual(audio_track.compression_mode, 'Lossy')

    @mock.patch('os.path.exists')
    @mock.patch('subprocess.Popen')
    def test_no_chapter_pooq(self, mock_popen, mock_exists):
        self._set_mediainfo_as_pooq(mock_popen, mock_exists)

        medium = PyFileInfo('pooq.mp4')
        self.assertEqual(len(medium.chapters), 1)

    @mock.patch('os.path.exists')
    @mock.patch('subprocess.Popen')
    def test_no_chapter_starwars(self, mock_popen, mock_exists):
        self._set_mediainfo_as_starwars_ep3(mock_popen, mock_exists)

        medium = PyFileInfo('starwars-ep3.mp4')
        self.assertEqual(len(medium.chapters), 50)

    def _set_mediainfo_as_pooq(self, mock_popen, mock_exists):
        media_xml = open(os.path.join(DATA_ROOT, 'mediainfo/pooq.xml')).read()

        process_mock = mock.Mock()
        attrs = {'communicate.return_value': (media_xml.encode('utf8'), '')}
        process_mock.configure_mock(**attrs)
        mock_popen.return_value = process_mock

        mock_exists.return_value = True

    def _set_mediainfo_as_starwars_ep3(self, mock_popen, mock_exists):
        media_xml = open(os.path.join(DATA_ROOT, 'mediainfo/star_wars_e_3.xml')).read()

        process_mock = mock.Mock()
        attrs = {'communicate.return_value': (media_xml.encode('utf8'), '')}
        process_mock.configure_mock(**attrs)
        mock_popen.return_value = process_mock

        mock_exists.return_value = True
