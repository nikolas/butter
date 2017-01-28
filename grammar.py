import re
from collections import defaultdict
from butter.hyphenate import hyphenate_word
import functools


class Word(object):
    """A class representing a single word in a sentence."""

    camelcase_ex = re.compile(r'(?<=[a-z])[A-Z]')

    def __init__(self, text):
        # get runs of repeated characters for collapsing later
        runs = [(i.start(), i.end()) for i in re.finditer(r'(.)\1{2,}', text)]

        # if the word is camelCase (or similar), break it into pieces
        chunks = []
        i = 0
        for m in self.camelcase_ex.finditer(text):
            chunks.append(text[i:m.start()])
            i = m.start()
        chunks.append(text[i:])

        self.syllables = functools.reduce(lambda x, y: x + hyphenate_word(y), chunks, [])

        # collapse any long runs of identical characters
        for run in runs:
            begin = self._find_syllable(run[0])
            end   = self._find_syllable(run[1]-1) + 1
            self.syllables[begin:end] = [''.join(self.syllables[begin:end])]

    def _find_syllable(self, char):
        """Find the index of the syllable containing the character at index
           |char|"""
        curr_len = 0
        for i, s in enumerate(self.syllables):
            curr_len += len(s)
            if char < curr_len:
                return i
        raise ValueError('out of bounds')

    def __getitem__(self, i):
        return self.syllables[i]

    def __setitem__(self, i, value):
        self.syllables[i] = value

    def __len__(self):
        return len(self.syllables)

    def __iter__(self):
        return iter(self.syllables)

    def __unicode__(self):
        return ''.join(self.syllables)

class Unword(Word):
    """A class representing a non-word string of characters in a sentence (e.g.
    spaces, punctuation)."""

    def __init__(self, text):
        self.syllables = [text]

class Sentence(object):
    """A class representing a whole sentence; comprised of Words and Unwords."""

    words_ex = re.compile(r'([\W_]+)', re.UNICODE)
    space_ex = re.compile(r'\s', re.UNICODE)

    def __init__(self, text):
        self.words = self.words_ex.split(text)
        self.same_words = defaultdict(list)

        # rejoin any URLs together so they count as one (un)word
        i = 0
        urls = []
        while i < len(self.words):
            if self.words[i] == 'www':
                start = i
            elif self.words[i] == '://' and i > 0:
                start = i-1
            else:
                i += 1
                continue

            end = len(self.words)
            for j in range(i, len(self.words)):
                if self.space_ex.search(self.words[j]):
                    end = j
                    break
            self.words[start:end] = [''.join(self.words[start:end])]
            urls.append(start)
            i = start+1

        # ignore zero-character words at the ends of the list
        self.min = 2 if self.words[0] == '' else 0
        self.max = len(self.words)
        if self.words[-1] == '' and len(self.words) > 1:
            self.max -= 2

        for word, token in enumerate(range(self.min, self.max, 2)):
            if token in urls:
                self.words[token] = Unword(self.words[token])
            else:
                self.words[token] = Word(self.words[token])
                self.same_words[str(self.words[token]).lower()].append(word)

    def related(self, i):
        return self.same_words[ str(self[i]).lower() ]

    def __getitem__(self, i):
        if self.min + i*2 >= self.max:
            raise IndexError('index out of bounds')
        return self.words[self.min + i*2] # skip spaces

    def __len__(self):
        return (self.max - self.min + 1) // 2

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    def __unicode__(self):
        return ''.join((str(i) for i in self.words))

plurals = {
    'men', 'women', 'feet', 'geese', 'teeth', 'lice', 'mice', 'children',
}
def is_plural(word):
    word = str(word).lower()
    if word[-1] == 's' and word[-2] not in 'ius': return True
    return word in plurals

past_tense = {
    'ate', 'became', 'began', 'bent', 'blew', 'broke', 'bought', 'brought',
    'built', 'burnt', 'came', 'caught', 'chose', 'did', 'drew', 'drank',
    'dreamt', 'drove', 'dug', 'fell', 'flew', 'forgot', 'fought', 'found',
    'gave', 'grew', 'heard', 'held', 'hid', 'kept', 'knew', 'leapt', 'learnt',
    'made', 'meant', 'met', 'paid', 'ran', 'rang', 'said', 'sang', 'sank',
    'sent', 'shook', 'shot', 'slept', 'slid', 'sold', 'spent', 'spoke', 'stank',
    'stole', 'stood', 'stuck', 'swam', 'taught', 'threw', 'told', 'took',
    'tore', 'went', 'woke', 'won', 'wore', 'wrote',
}
def is_past_tense(word):
    word = str(word).lower()
    if len(word) > 2 and word[-2:] == 'ed' and word[-3] not in 'ae': return True
    return word in past_tense
