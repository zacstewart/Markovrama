import re
import random
import os
from glob import glob

class Scene(object):
  LOCATION_PATTERN = r'Scene: ([^.]+)'

  def __init__(self, transcript_line):
    self.name = transcript_line[1:-2]
    m = re.match(self.LOCATION_PATTERN, self.name)
    self.location = m.group(1)
    self.characters = set()
    self.dialog = []

  def __repr__(self):
    return "<Scene({}, {})>".format(self.location, self.characters)

class Episode:
  def __init__(self, transcript_file):
    self.characters = set()
    self.scenes = []
    with open(transcript_file) as file_:
      [self.consume(line.strip()) for line in file_]

  def consume(self, line):
    if len(line) < 1: return
    if self.is_dialog(line):
      self.add_dialog(line)
    elif self.is_scene(line):
      self.add_scene(line)

  def add_dialog(self, line):
    parts = line.split(': ')
    if len(parts) > 1:
      character = parts[0].strip()
      statement = ': '.join(parts[1:]).strip()
      self.last_scene.characters.add(character)
      self.last_scene.dialog.append((character, statement))

  def add_scene(self, line):
    scene = Scene(line)
    self.last_scene = scene
    self.scenes.append(scene)

  def is_dialog(self, line):
    return line[0] is not '['

  def is_scene(self, line):
    return line[0:7] == '[Scene:'

class Chain:
  def __init__(self, name):
    self.name = name
    self.word_counts = {}
    self.next_words = {}

  def increment_word_count(self, word):
    if word in self.word_counts:
      self.word_counts[word] += 1
    else:
      self.word_counts[word] = 1

  def increment_next_word(self, key, word):
    if key not in self.next_words:
      self.next_words[key] = {}

    if word not in self.next_words[key]:
      self.next_words[key][word] = 0

    self.next_words[key][word] += 1

  def add_ngram(self, ngram):
    key = tuple(ngram[:-1])
    word = ngram[-1]
    self.increment_word_count(key)
    self.increment_next_word(key, word)

  def add_statement(self, statement):
    if type(statement) == str:
      words = re.split('\s', statement)
    else:
      words = statement

    words = ['_START_'] + words + ['_STOP_']
    for i in range(len(words) - 2):
      for j in range(2): # unigrams and bigrams plox
        self.add_ngram(words[i:i+j+2])

  def next_word(self, prefix):
    candidate_next_words = self.next_words[tuple(prefix)]
    return random.choice(candidate_next_words.keys())

  def pair_starting_with(self, starter):
    if len(starter) is 2:
      return starter

    candidate_pairs = self.next_words[tuple(starter)]
    return starter + [random.choice(candidate_pairs.keys())]

  def generate_statement(self, initial='_START_'):
    initial = re.split('\s+', initial)
    ignored = initial[:-2]
    starter = initial[-2:]
    starter = self.pair_starting_with(starter)

    statement = ignored + starter
    nw = None

    while nw is not '_STOP_':
      nw = self.next_word(starter)
      statement.append(nw)
      starter = [starter[-1], nw]
    return statement[1:-1]

episodes = []
for file_name in glob('data/*.txt'):
  episodes.append(Episode(file_name))

characters = {}
scenes = {}
new_episode = Chain('episode')

for episode in episodes:
  new_episode.add_statement([scene.location for scene in episode.scenes])

  for scene in episode.scenes:
    if scene.location not in scenes:
      scenes[scene.location] = Chain(scene.location)
    scenes[scene.location].add_statement([character for character, _ in scene.dialog])

    for character, statement in scene.dialog:
      if character not in characters:
        characters[character] = Chain(character)

      characters[character].add_statement(statement)

for location in new_episode.generate_statement():
  print "[Scene: {}]".format(location)
  for character in scenes[location].generate_statement():
    print "{}: {}".format(character, ' '.join(characters[character].generate_statement()))

for name, character in characters.items():
  #print "{}, {}".format(name, character.generate_statement())
  pass
