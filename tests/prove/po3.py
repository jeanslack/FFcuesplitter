# -*- encoding: utf-8 -*-

# https://gist.github.com/bancek/b37b780292540ed2d17d#gistcomment-3230756

import sys
import os.path
import codecs


if len(sys.argv) == 1:
  print("Usage: cue_to_mp3.py <CUE file path> [-o]")
  print("Options:")
  print("    -o, execute and output mp3 file")
  sys.exit(0)

cue_file = sys.argv[1]

d = open(cue_file).read().splitlines()

general = {}

tracks = []

current_file = None

for line in d:
    if line.startswith('REM GENRE '):
        general['genre'] = ' '.join(line.split(' ')[2:])
    if line.startswith('REM DATE '):
        general['date'] = ' '.join(line.split(' ')[2:])
    if line.startswith('PERFORMER '):
        general['artist'] = ' '.join(line.split(' ')[1:]).replace('"', '')
    if line.startswith('TITLE '):
        general['album'] = ' '.join(line.split(' ')[1:]).replace('"', '')
    if line.startswith('FILE '):
        current_file = ' '.join(line.split(' ')[1:-1]).replace('"', '')

    if line.startswith('  TRACK '):
        track = general.copy()
        track['track'] = int(line.strip().split(' ')[1], 10)

        tracks.append(track)

    if line.startswith('    TITLE '):
        tracks[-1]['title'] = ' '.join(line.strip().split(' ')[1:]).replace('"', '')
    if line.startswith('    PERFORMER '):
        tracks[-1]['artist'] = ' '.join(line.strip().split(' ')[1:]).replace('"', '')
    if line.startswith('    INDEX 01 '):
        t = list(map(int, ' '.join(line.strip().split(' ')[2:]).replace('"', '').split(':')))
        tracks[-1]['start'] = 60 * t[0] + t[1] + t[2] / 100.0

for i in range(len(tracks)):
    if i != len(tracks) - 1:
        tracks[i]['duration'] = tracks[i + 1]['start'] - tracks[i]['start']

for track in tracks:
    metadata = {
        'artist': track['artist'],
        'title': track['title'],
        'album': track['album'],
        'track': str(track['track']) + '/' + str(len(tracks))
    }

    if 'genre' in track:
        metadata['genre'] = track['genre']
    if 'date' in track:
        metadata['date'] = track['date']

    cmd = 'ffmpeg'
    cmd += ' -i "%s"' % current_file
    cmd += ' -ss %.2d:%.2d:%.2d' % (track['start'] / 60 / 60, track['start'] / 60 % 60, int(track['start'] % 60))

    if 'duration' in track:
        cmd += ' -t %.2d:%.2d:%.2d' % (track['duration'] / 60 / 60, track['duration'] / 60 % 60, int(track['duration'] % 60))

    cmd += ' ' + ' '.join('-metadata %s="%s"' % (k, v) for (k, v) in metadata.items())
    cmd += ' -b:a 320k'
    cmd += ' "%.2d - %s - %s.mp3"' % (track['track'], track['artist'], track['title'])

    print(cmd)
