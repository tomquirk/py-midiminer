"""
Helpers
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def parse_midi_csv(file_path):
    """
    Returns dictionary containing basic piece details and dataframe of notes
    """
    csv = open(file_path, 'r')
    csv_file = csv.read()
    lines = csv_file.split('\n')


    raw_title = lines[2].split(" - ")

    if len(raw_title) > 1:
        raw_title = raw_title[1][:-5]

    key_sig = ""

    for line in lines:
        if "Key_signature" in line:
            params = line.split(", ")
            key_sig = get_key_signature(int(params[3]), params[4].replace('"', ''))
            break

    title = parse_title(file_path, key_sig)

    note_rows = [i.replace(' ', '').split(',') for i in lines if 'Note' in i]

    dataframe = pd.DataFrame(note_rows, columns=['track', 'time', 'action', 'channel', 'note', 'velocity'])

    return {
        "raw_title": raw_title,
        "title": title,
        "key_sig": key_sig,
        "tempo": get_tempo(lines),
        "dataframe": dataframe
    }

def group_sonatas(pieces):
    """
    Groups movements by sonata
    """
    groups = [[] for i in range(32)]
    for piece in pieces:
        groups[piece["title"]["sonata"] - 1].append(piece)
    # print(groups)

    sonatas = []

    for group in groups:
        dataframe = [i["dataframe"] for i in group]
        sonatas.append({
            "raw_title": group[0]["raw_title"],
            "title": group[0]["title"],
            "key_sig": group[0]["key_sig"],
            "dataframe": pd.concat(dataframe)
        })

    return sonatas


def parse_title(filename, key_signature):
    """
    Takes a filename and returns its (as close to) sonata title
    """

    _filename = filename.split('/')[1]

    sonata = int(_filename[2:4])
    movement = int(_filename[5:7])
    if key_signature:
        title = "Sonata No. %d in %s %s: %d." % (sonata, key_signature["note"], key_signature["tonality"], movement)
    else:
        title = "Sonata No. %d: %d." % (sonata, movement)

    return  {
        "sonata": sonata,
        "movement": movement,
        "title": title
    }


def get_pitch_class(note):
    """
    Returns whether a note is a sharp, flat or neutral
    """
    if len(note) == 1:
        return None

    return note[1]


def get_piano_note(midi_note, pitch_class):
    """
    Returns letter note equivalent of midi note
    midi_note: int
    """
    if pitch_class is None:
        pitch_class = "#" # doesnt matter what it is

    notes = {
        "#": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
        "b": ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
    }

    if midi_note <= 11:
        return notes[pitch_class][midi_note]
    else:
        return get_piano_note(midi_note - 12, pitch_class)

def get_key_signature(index, tonality):
    """
    index: int, midi index (e.g. -4)
    tonality: str, minor or major
    """
    white = {
        "major": "C",
        "minor": "A"
    }

    flat = {
        "major": ["F", "Bb", "Eb", "Ab", "Db", "Gb", "Cb"],
        "minor": ["D", "G", "C", "F", "Bb", "Eb", "Ab",]
    }

    sharp = {
        "major": ["G", "D", "A", "E", "B", "F#", "C#"],
        "minor": ["E", "B", "F#", "C#", "G#", "D#", "A#",]
    }

    key = {
        "note": None,
        "tonality": tonality
    }

    if index == 0:
        key["note"] = white[tonality]
    elif index > 0:
        key["note"] = sharp[tonality][index - 1]
    else:
        key["note"] = flat[tonality][(index + 1) * -1]

    return key

def get_tempo(csv_rows):
    """
    Returns average tempo and approx. label from given list of rows:
    :param: csv_rows: List, comma-serperated rows
    """
    tempo = {
        "bpm": 0,
        "label": None
    }

    tempos = [int(i.split(', ')[3]) for i in csv_rows if 'Tempo' in i]
    tempo_ms = int(sum(tempos)/len(tempos))
    tempo["bpm"] = (60 * 1000000) / tempo_ms

    return tempo


def parse_all_pieces(directory):
    """
    Parses all midi files in given directory and returns them in an array
    """
    pieces = []

    for csv in os.listdir(directory):
        path = '%s/%s' % (directory, csv)
        if os.path.isfile(path) and os.path.splitext(path)[1] == '.csv':
            pieces.append(parse_midi_csv(path))

    return pieces

def get_unique_note_count(piece):
    """
    Returns list of note counts, found at index
    """
    notes = [0 for i in range(127)]
    for note in piece["dataframe"]["note"]:
        note = int(note)
        if notes[note] == 0:
            notes[note] = 1

    return len([note for note in notes if note == 1])

def get_note_letter_occurence(note, piece):
    """
    Get occurence of note letter (across all octaves) in given piece
    note: Letter, len(note) == (1 || 2)
    """
    return len([i for i in piece["dataframe"]["note"] if get_piano_note(int(i), get_pitch_class(note)) == note])

def get_midi_note_occurence(note, piece):
    """
    Get occurence of midi note in given piece
    note: int
    """
    return len([i for i in piece["dataframe"]["note"] if int(i) == note])

def get_scale_note_count(piece):
    """
    """
    if not piece["key_sig"]:
        return

    notes = {
        "#": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
        "b": ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B", "C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
    }

    semitones = {
        "minor": [2, 1, 2, 2, 1, 3, 1],
        "major": [2, 2, 1, 2, 2, 2, 1]
    }

    count = [0 for i in range(7)]
    if not piece["key_sig"]:
        return []

    # get scale
    root_note = piece["key_sig"]["note"]
    if len(root_note) == 1:
        if piece["key_sig"]["tonality"] == "minor":
            my_notes = notes["b"]
        else:
            my_notes = notes["#"]
    else:
        my_notes = notes[root_note[-1]]

    root_note_i = my_notes.index(root_note)
    scale = []

    current_note_i = root_note_i
    for i in semitones[piece["key_sig"]["tonality"]]:
        scale.append(my_notes[current_note_i])
        current_note_i += i

    for note in enumerate(scale):
        count[note[0]] += get_note_letter_occurence(note[1], piece)

    return count

def savefig(plt, name):
    plt.savefig(name + '.png', format='png', dpi=300)
