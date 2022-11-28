from mido import MidiFile, MetaMessage, MidiTrack, Message
from random import choice, random
from copy import deepcopy

"""Constant that introduce length of each bar"""
BAR_LENGTH = 384 * 2


class Music:
    """
    Class Music considers the necessary values for accompaniment and generates an output
    """
    def __init__(self, filename):
        """
        Constructor of the class
        :param filename: name of input file
        """
        self.file = MidiFile(filename)

    def unique_notes(self):
        """
        Get unique note without repetitions from input file
        :return: set of notes
        """
        notes = set()
        for track in self.file.tracks[1:]:
            for msg in track[2:-1]:
                notes.add(msg.note % 12)

        return notes

    def all_notes(self):
        """
        Get consistency of all notes from input notes
        :return: array of all notes
        """
        notes = []
        for track in self.file.tracks[1:]:
            for msg in track[2:-1]:
                notes.append(msg.note % 12)

        return notes

    def accompaniment(self, chords):
        """
        Function that write output files
        :param chords: a set of chords that are included in the accompaniment
        """
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
        """
        Function that count average velocity of all melody
        :return: average velocity
        """
        number = 0
        sum_of_velocities = 0
        for track in self.file.tracks[1:]:
            for msg in track[2:-1]:
                if msg.type == "note_on":
                    number += 1
                    sum_of_velocities += msg.velocity

        return sum_of_velocities // number

    def average_octave(self):
        """
        Function that count average octave of all melody
        :return: average octave
        """
        number = 0
        octave = 0
        for track in self.file.tracks[1:]:
            for msg in track[2:-1]:
                if msg.type == "note_on":
                    number += 1
                    octave += (msg.note // 12)

        return octave // number

    def get_duration_in_bars(self):
        """
        Function that count duration in bars of melody
        :return: duration in bars
        """
        time = 0
        for track in self.file.tracks[1:]:
            for msg in track[2:-1]:
                time += msg.time

        return time // BAR_LENGTH

    def divide_by_bars(self):
        """
        Function creates an array of notes that were played during the i-th beat
        :return: array of notes that were played during the i-th beat
        """
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
    """
    The main function of class Key to chose correct key (tonic + scale)
    """

    """ Constant arrays of displacements"""
    KEYS = ["C", "Db|C#", "D", "Eb|D#", "E", "F", "Gb|F#", "G", "Ab|G#", "A", "Bb|A#", "B"]
    major_keys = {}
    minor_keys = {}
    major_triad = {0, 4, 7}
    minor_triad = {0, 3, 7}
    dim = {0, 3, 6}

    def __init__(self, music):
        """
        Constructor of class Key that generates table of chords
        :param music: instance of class Music
        """
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

    def chord(self, root_note, displacement):
        """
        Supporting function for generating chords
        :param root_note: scale of music
        :param displacement: tonic of music
        :return: array of chords
        """
        chord = []
        for el in displacement:
            chord.append((root_note + el) % 12)

        return chord

    def key(self):
        """
        Function that selects all suitable keys that have passed the "check" -comparison with the generated
        table and major chords and then chose one with the help of correct_key()
        :return: one key of melody
        """
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
            res = all(note in un_chords_notes for note in notes)
            if res:
                possible_keys_minor.append(note_string)

        return self.correct_key(possible_keys_minor, possible_keys_major)

    def correct_key(self, possible_key_minor, possible_key_major):
        """
        Function that chooses one key from all the approached by some rules (please, refer to report)
        :param possible_key_minor: possible minor keys
        :param possible_key_major: possible major keys
        :return:
        """
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
        """
        The function narrows the search for suitable chords to 7 (from generated table) by key
        :return: array of well-sounding chords by key
        """
        key_note, scale = self.key()
        if scale == "major":
            return self.major_keys[key_note]
        else:
            return self.minor_keys[key_note]


class Chord:
    """
    Class Chords it is an auxiliary class for the evolutionary algorithm. It helps to mutate chords,
    to check whether the chord is diminished, suspend2 or suspend4
    """

    """Some constant displacement"""
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
        """
        Constructor of the class
        :param notes: notes that make up chords
        :param step: step from minors/major keys
        :param scale: scale of music
        """
        self.notes = notes
        self.scale = scale
        self.current_note = self.notes[0]
        self.step = step

    def mutation(self):
        """
        Mutate chords if random probability more than 50%
        """
        if random() <= 0.5:
            return

        n = random()
        if n <= 0.3:
            if self.scale == "minor":
                self.notes = [self.current_note + i for i in self.minor_first_inversion]
            else:
                self.notes = [self.current_note + i for i in self.major_first_inversion]

        if 0.3 < n <= 0.6:
            if self.scale == "major":
                self.notes = [self.current_note + i for i in self.major_second_inversion]
            else:
                self.notes = [self.current_note + i for i in self.minor_second_inversion]

        if 0.6 < n <= 0.8:
            if self.scale == "major" and self.step not in [3, 7]:
                self.notes = [self.current_note + i for i in self.sus2]
            if self.scale == "minor" and self.step not in [2, 5]:
                self.notes = [self.current_note + i for i in self.sus2]

        if 0.8 < n <= 1:
            if self.scale == "major" and self.step not in [4, 7]:
                self.notes = [self.current_note + i for i in self.sus4]
            if self.scale == "minor" and self.step not in [2, 6]:
                self.notes = [self.current_note + i for i in self.sus4]

    def check_dim(self) -> bool:
        """
        Function checks if chord is diminished
        :return: True if chord is diminished, otherwise false
        """
        dim_triad = [self.current_note + i for i in self.dim]
        return self.notes == dim_triad

    def check_sus2(self) -> bool:
        """
        Function checks if chord is suspend2
        :return: True if chord is suspend2, otherwise false
        """
        sus2_triad = [self.current_note + i for i in self.sus2]
        return self.notes == sus2_triad

    def check_sus4(self) -> bool:
        """
        Function checks if chord is suspend4
        :return: True if chord is suspend4, otherwise false
        """
        sus4_triad = [self.current_note + i for i in self.sus2]
        return self.notes == sus4_triad

    def get_tuple(self):
        """
        Supporting function for change array of notes of one chord into tuple
        :return: tuple of chords
        """
        return self.notes[0], self.notes[1], self.notes[2]


class Chromosome:
    """
    Class Chromosome generates chromosome from chords, then mutate and estimate them
    """
    def __init__(self, chords: list[Chord]):
        """
        Constructor of the class
        :param chords: array of chords
        """
        self.chords = chords

    def mutation_chromosome(self):
        """
        Function that mutate all chords in chromosome
        """
        for chord in self.chords:
            chord.mutation()

    def fitness(self, music: Music) -> int:
        """
        Estimates chromosome by several rules (please, refer to report)
        :param music: instance of class Music
        :return: fitness sum
        """
        fit_res = 0
        div_music = music.divide_by_bars()

        for i in range(len(self.chords)):
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

            for n in range(2, len(div_music), 4):
                if self.chords[0].notes in div_music[n]:
                    fit_res += 10
                if (self.chords[1].notes in div_music[n]) or (self.chords[2].notes in div_music[n]):
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
    """
    Class Population can produce generations of chromosomes
    """
    def __init__(self, music, generations_size, iterations):
        """
        Constructor of the class
        :param music: instance of class Music
        :param generations_size: user defined size of
        :param iterations: number of iterations
        """
        self.iterations = iterations
        self.population_size = generations_size
        self.music = music
        self.melody = Key(music)
        self.key = self.melody.key()
        tmp = self.melody.good_chords()
        self.good_chords = list(zip(tmp, range(1, len(tmp) + 1)))
        self.amount_of_chords_in_accompaniment = self.music.get_duration_in_bars()

    def initial_generation(self) -> list[Chromosome]:
        """
        Function that creates initial generation
        :return: array of chromosomes
        """
        init_population = []
        for i in range(self.population_size):
            list_for_chromosome = []
            for j in range(self.amount_of_chords_in_accompaniment):
                list_for_chromosome.append(Chord(*choice(self.good_chords), self.key[1]))

            init_population.append(Chromosome(list_for_chromosome))

        return init_population

    def crossover(self, chromosome1: Chromosome, chromosome2: Chromosome):
        """
        Function take the odd positions from chromosome1 and the even positions from chromosome2,
        and then we create a new chromosome
        :param chromosome1: parent chromosome1
        :param chromosome2: parent chromosome2
        :return:
        """
        new_chromosome = list()
        for i in range(len(chromosome1.chords)):
            if i % 2 == 0:
                new_chromosome.append(chromosome1.chords[i])
            else:
                new_chromosome.append(chromosome2.chords[i])
        return Chromosome(new_chromosome)

    def next_generation(self, previous_generation):
        """
        Function produce next generation of chromosome
        :param previous_generation: previous generation
        :return: array of chromosomes that make next generation
        """
        next_gener = deepcopy(previous_generation)
        for _ in range(self.population_size):
            next_gener.append(self.crossover(choice(previous_generation), choice(previous_generation)))

        for chromosome in previous_generation:
            mutated_chromosome = deepcopy(chromosome)
            mutated_chromosome.mutation_chromosome()
            next_gener.append(mutated_chromosome)

        next_gener.sort(key=lambda x: -x.fitness(self.music, self.melody))
        next_gener = next_gener[:self.population_size]
        return next_gener

    def generator(self):
        """
        Function generates populations, which number is number of iterations
        :return: music with accompaniment
        """
        generation = self.initial_generation()
        for _ in range(self.iterations):
            generation = self.next_generation(generation)
        chords = [chord.get_tuple() for chord in generation[0].chords]
        self.music.accompaniment(chords)


music = Music("input2.mid")  # change it to the needed file
population = Population(music, 100, 200)
population.generator()
