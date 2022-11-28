from mido import MidiFile, MetaMessage, MidiTrack, Message
from random import choice, random
from copy import deepcopy
from tqdm import tqdm
from typing import List

BAR_LENGTH = 384 * 2


class Music:
    def __init__(self, filename):
        self.file = MidiFile(filename)

    def unique_notes(self):
        notes = set()
        for track in self.file.tracks[1:]:
            for msg in track[2:-1]:
                notes.add(msg.note % 12)
        return notes

    def all_notes(self):
        notes = []
        for track in self.file.tracks[1:]:
            for msg in track[2:-1]:
                notes.append(msg.note % 12)
        return notes

    def accompaniment(self, chords):
        new_track = MidiTrack()
        vel = self.average_velocity()
        octave = self.average_octave() * 12
        print(vel, type(vel))
        new_track.append(MetaMessage("track_name", name='Elec. Piano (Classic)', time=0))
        for ch in chords:
            new_track.append(Message('note_on', channel=0, note=octave + ch[0], velocity=vel, time=0))
            new_track.append(Message('note_on', channel=0, note=octave + ch[1], velocity=vel, time=0))
            new_track.append(Message('note_on', channel=0, note=octave + ch[2], velocity=vel, time=0))

            new_track.append(Message('note_off', channel=0, note=octave + ch[0], velocity=vel, time=BAR_LENGTH))
            new_track.append(Message('note_off', channel=0, note=octave + ch[1], velocity=vel, time=0))
            new_track.append(Message('note_off', channel=0, note=octave + ch[2], velocity=vel, time=0))
        new_track.append(MetaMessage("end_of_track", time=0))
        self.file.tracks.append(new_track)
        self.file.save(f"{self.file.filename}_with_accompaniment.mid")

    def average_velocity(self):
        number = 0
        sum_of_velocities = 0
        for track in self.file.tracks[1:]:
            for msg in track[2:-1]:
                if msg.type == "note_on":
                    number += 1
                    sum_of_velocities += msg.velocity
        return sum_of_velocities // number

    def average_octave(self):
        number = 0
        octave = 0
        for track in self.file.tracks[1:]:
            for msg in track[2:-1]:
                if msg.type == "note_on":
                    number += 1
                    octave += (msg.note // 12)
        return octave // number

    def get_duration_in_bars(self):
        time = 0
        for track in self.file.tracks[1:]:
            for msg in track[2:-1]:
                time += msg.time
        return time // BAR_LENGTH

    def divide_by_bars(self):
        amount_bars = self.get_duration_in_bars()
        result = [[] for _ in range(amount_bars)]
        arr = []
        for track in self.file.tracks[1:]:
            for msg in track[2:-1]:
                arr.append((msg.type, msg.note % 12, msg.time))

        absolute_time_begin = 0
        for i in range(0, len(arr), 2):
            on = arr[i]
            off = arr[i + 1]
            absolute_time_end = absolute_time_begin + on[2] + off[2]
            cur_time = absolute_time_begin + on[2]
            while cur_time < absolute_time_end:
                for j in range(0, len(result)):
                    if BAR_LENGTH * j <= cur_time < BAR_LENGTH * (j + 1):
                        result[j].append(on[1])
                cur_time += BAR_LENGTH
            absolute_time_begin = absolute_time_end
        return result


class Key:
    KEYS = ["C", "Db|C#", "D", "Eb|D#", "E", "F", "Gb|F#", "G", "Ab|G#", "A", "Bb|A#", "B"]
    major_keys = {}
    minor_keys = {}
    major_triad = {0, 4, 7}
    minor_triad = {0, 3, 7}
    dim = {0, 3, 6}

    def __init__(self, music):
        self.music = music
        for index, note in enumerate(self.KEYS):
            self.major_keys[note] = []
            self.minor_keys[note] = []
            self.major_keys[note].append(self.chord((0 + index) % 12, self.major_triad))
            self.major_keys[note].append(self.chord((2 + index) % 12, self.major_triad))
            self.major_keys[note].append(self.chord((4 + index) % 12, self.major_triad))
            self.major_keys[note].append(self.chord((5 + index) % 12, self.major_triad))
            self.major_keys[note].append(self.chord((7 + index) % 12, self.major_triad))
            self.major_keys[note].append(self.chord((9 + index) % 12, self.major_triad))
            self.major_keys[note].append(self.chord((11 + index) % 12, self.dim))

            self.minor_keys[note].append(self.chord((0 + index) % 12, self.minor_triad))
            self.minor_keys[note].append(self.chord((2 + index) % 12, self.dim))
            self.minor_keys[note].append(self.chord((3 + index) % 12, self.minor_triad))
            self.minor_keys[note].append(self.chord((5 + index) % 12, self.minor_triad))
            self.minor_keys[note].append(self.chord((7 + index) % 12, self.minor_triad))
            self.minor_keys[note].append(self.chord((8 + index) % 12, self.minor_triad))
            self.minor_keys[note].append(self.chord((10 + index) % 12, self.minor_triad))

    def chord(self, scale, tonic):
        chord = []
        for el in tonic:
            chord.append((scale + el) % 12)
        return chord

    def key(self):
        notes = self.music.unique_notes()
        possible_keys_major = []
        possible_keys_minor = []
        for note_string in self.major_keys:
            un_chords_notes = set(el[0] for el in self.major_keys[note_string])
            res = all(note in un_chords_notes for note in notes)
            if res:
                possible_keys_major.append(note_string)
        for note_string in self.minor_keys:
            un_chords_notes = set(el[0] for el in self.minor_keys[note_string])
            # print(note_string, list(un_chords_notes))
            res = all(note in un_chords_notes for note in notes)
            if res:
                possible_keys_minor.append(note_string)

        return self.correct_key(possible_keys_minor, possible_keys_major)

    def correct_key(self, possible_key_minor, possible_key_major):
        notes = self.music.all_notes()
        last_note = notes[-1]

        for i in range(len(possible_key_minor)):
            row = list(map(lambda x: x[0], self.minor_keys[possible_key_minor[i]]))
            tonic = row[0]
            if last_note == tonic:
                return possible_key_minor[i], "minor"

        for i in range(len(possible_key_major)):
            row = list(map(lambda x: x[0], self.minor_keys[possible_key_major[i]]))
            tonic = row[0]
            if last_note == tonic:
                return possible_key_major[i], "major"

        for i in range(len(possible_key_minor)):
            row = list(map(lambda x: x[0], self.minor_keys[possible_key_minor[i]]))
            mediant = row[2]
            dominant = row[4]
            if last_note == mediant or last_note == dominant:
                return possible_key_minor[i], "minor"

        for i in range(len(possible_key_major)):
            row = list(map(lambda x: x[0], self.major_keys[possible_key_major[i]]))
            mediant = row[2]
            dominant = row[4]
            if last_note == mediant or last_note == dominant:
                return possible_key_major[i], "major"

        for i in range(len(possible_key_minor)):
            row = list(map(lambda x: x[0], self.minor_keys[possible_key_minor[i]]))
            supertonic = row[1]
            subdominant = row[3]
            submedian = row[5]
            leading_tone = row[6]
            if last_note in [subdominant, submedian, leading_tone, supertonic]:
                return possible_key_minor[i], "minor"

        for i in range(len(possible_key_major)):
            row = list(map(lambda x: x[0], self.major_keys[possible_key_major[i]]))
            subdominant = row[3]
            submedian = row[5]
            supertonic = row[1]
            leading_tone = row[6]
            if last_note in [subdominant, submedian, leading_tone, supertonic]:
                return possible_key_major[i], "major"


    def good_chords(self):
        key_note, scale = self.key()
        if scale == "major":
            return self.major_keys[key_note]
        else:
            return self.minor_keys[key_note]


class Chord:
    major_triad = {0, 4, 7}
    minor_triad = {0, 3, 7}
    major_first_inversion = {4, 7, 12}
    minor_first_inversion = {3, 7, 12}
    major_second_inversion = {7, 12, 16}
    minor_second_inversion = {7, 12, 15}
    dim = {0, 3, 6}
    sus2 = {0, 2, 7}
    sus4 = {0, 5, 7}

    def __init__(self, notes, step, scale):
        self.notes = notes
        self.scale = scale
        self.current_note = self.notes[0]
        self.step = step

    def mutation(self):
        n = random()
        if n <= 0.3:
            if self.scale == "minor":
                self.notes = [self.current_note + i for i in self.minor_first_inversion]
        if 0.3 < n <= 0.5:
            if self.scale == "major":
                self.notes = [self.current_note + i for i in self.major_first_inversion]
        if 0.5 < n <= 0.65:
            if self.scale == "major":
                self.notes = [self.current_note + i for i in self.major_second_inversion]
        if 0.65 < n <= 0.95:
            if self.scale == "minor":
                self.notes = [self.current_note + i for i in self.minor_second_inversion]
        if 0.95 < n <= 0.97:
            if self.scale == "major" and self.step not in [3, 7]:
                self.notes = [self.current_note + i for i in self.sus2]
            if self.scale == "minor" and self.step not in [2, 5]:
                self.notes = [self.current_note + i for i in self.sus2]
        if 0.97 < n <= 1:
            if self.scale == "major" and self.step not in [4, 7]:
                self.notes = [self.current_note + i for i in self.sus4]
            if self.scale == "minor" and self.step not in [2, 6]:
                self.notes = [self.current_note + i for i in self.sus4]

    def check_dim(self) -> bool:
        dim_triad = [self.current_note + i for i in self.dim]
        return self.notes == dim_triad

    def check_sus2(self) -> bool:
        sus2_triad = [self.current_note + i for i in self.sus2]
        return self.notes == sus2_triad

    def check_sus4(self) -> bool:
        sus4_triad = [self.current_note + i for i in self.sus2]
        return self.notes == sus4_triad

    def get_tuple(self):
        return self.notes[0], self.notes[1], self.notes[2]


class Chromosome:
    def __init__(self, chords: list[Chord]):
        self.chords = chords

    def mutation_chromosome(self):
        for chord in self.chords:
            chord.mutation()

    def fitness(self, music: Music, key: Key) -> int:
        fit_res = 0
        notes = music.all_notes()
        div_music = music.divide_by_bars()

        for i in range(len(self.chords)):
            if self.chords[i].notes[0] == notes[-1] or self.chords[i].notes[0] == notes[0]:
                fit_res += 9

            if self.chords[i].check_dim() or self.chords[i].check_sus2() or self.chords[i].check_sus4():
                fit_res -= 20
            else:
                fit_res += 10

            for j in range(0, len(div_music), 4):
                if self.chords[0].notes in div_music[j]:
                    fit_res += 20
                if (self.chords[1].notes in div_music[j]) or (self.chords[2].notes in div_music[j]):
                    fit_res += 5
                else:
                    fit_res -= 10

            for k in range(1, len(div_music), 4):
                if self.chords[0].notes in div_music[k]:
                    fit_res += 8
                if (self.chords[1].notes in div_music[k]) or (self.chords[2].notes in div_music[k]):
                    fit_res += 5
                else:
                    fit_res += 1

            for l in range(2, len(div_music), 4):
                if self.chords[0].notes in div_music[l]:
                    fit_res += 10
                if (self.chords[1].notes in div_music[l]) or (self.chords[2].notes in div_music[l]):
                    fit_res += 5
                else:
                    fit_res -= 10

            for m in range(2, len(div_music), 4):
                if self.chords[0].notes in div_music[m]:
                    fit_res += 10
                if (self.chords[1].notes in div_music[m]) or (self.chords[2].notes in div_music[m]):
                    fit_res += 5
                else:
                    fit_res += 1
        return fit_res


class Population:

    def __init__(self, music, population_size, iterations):
        self.iterations = iterations
        self.population_size = population_size
        self.music = music
        self.melody = Key(music)
        self.key = self.melody.key()
        tmp = self.melody.good_chords()
        self.good_chords = list(zip(tmp, range(1, len(tmp) + 1)))
        self.amount_of_chords_in_accompaniment = self.music.get_duration_in_bars()

    def initial_population(self) -> list[Chromosome]:
        init_population = []
        for i in range(self.population_size):
            list_for_chromosome = []
            for j in range(self.amount_of_chords_in_accompaniment):
                list_for_chromosome.append(Chord(*choice(self.good_chords), self.key[1]))
            init_population.append(Chromosome(list_for_chromosome))
        return init_population

    def crossover(self, chromosome1: Chromosome, chromosome2: Chromosome):
        new_chromosome = list()
        for i in range(len(chromosome1.chords)):
            if i % 2 == 0:
                new_chromosome.append(chromosome1.chords[i])
            else:
                new_chromosome.append(chromosome2.chords[i])
        return Chromosome(new_chromosome)

    def next_generation(self, previous_population: List[Chromosome]):
        next_gener = deepcopy(previous_population)
        next_gener.sort(key=lambda x: -x.fitness(self.music, self.melody))

        for _ in range(self.population_size):
            next_gener.append(self.crossover(choice(previous_population), choice(previous_population)))

        for chromosome in previous_population:
            mutated_chromosome = deepcopy(chromosome)
            mutated_chromosome.mutation_chromosome()
            next_gener.append(mutated_chromosome)
        next_gener.sort(key=lambda x: -x.fitness(self.music, self.melody))
        next_gener = next_gener[:self.population_size]
        return next_gener

    def generator(self):
        population = self.initial_population()
        for _ in tqdm(range(self.iterations)):
            population = self.next_generation(population)
        chords = [chord.get_tuple() for chord in population[0].chords]
        self.music.accompaniment(chords)


song = Music("input3.mid")
population = Population(song, 100, 200)
population.generator()
