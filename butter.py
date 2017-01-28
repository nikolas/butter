import math
import butter.prob as prob
import re
import butter.grammar as grammar
from functools import reduce

class Scorer(object):
    class Score(tuple):
        def __new__(cls, total, each):
            return tuple.__new__(cls, each)

        def __init__(self, total, each):
            self.total = total

        def __repr__(self):
            return '<{0}, {1}>'.format(self.total, list(self))

    block_words = {
        'the', 'and', 'but', 'not', 'also', 'from', 'for', 'with', 'without',
        'then', 'which', 'too', 'any', 'all', 'some', 'once', 'been',
        'isn', 'are', 'aren', 'was', 'wasn', 'were', 'weren',
        'will', 'won', 'would', 'can', 'could', 'should',
        'does', 'doesn', 'don', 'did',
        'has', 'had', 'hadn', 'have', 'haven',
        'this', 'that', 'these', 'those', 'here', 'there',
        'she', 'him', 'her', 'its', 'his', 'hers',
        'they', 'their', 'theirs', 'you', 'your', 'our', 'ours',
        'who', 'what', 'where', 'when', 'why', 'how',
        'yes', 'yeah', 'yah', 'yep', 'nah', 'nope',
    }

    good_prewords = {
        'the', 'an', 'a', 'my', 'your', 'his', 'her', 'our', 'their', 'to',
        'this', 'that', 'these', 'those',
    }

    block_sylls = {
        'ing', 'sion', 'tion',
    }

    def __init__(self, sent, min_words=2):
        self.values = self._score_sentence(sent, min_words)

    def _score_sentence(self, sent, min_words):
        words = [self._score_word(word) for word in sent]

        for i in range(len(sent)):
            if words[i].total == 0: continue

            # words after good pre-words
            if i > 0:
                prev = str(sent[i-1]).lower()
                if prev in self.good_prewords:
                    words[i].total += 5

            # repeated words
            factor = 1.25 ** (len(sent.related(i))-1)
            words[i].total = int(words[i].total * factor)

        if len(words) >= min_words:
            score = int(reduce(lambda x, y: x+y.total, words, 0) //
                        (len(words) ** 0.75))
        else:
            score = 0
        return self.Score(score, words)

    def _score_word(self, word):
        if (len(str(word)) < 3 or
            str(word).lower() in self.block_words or
            isinstance(word, grammar.Unword)):
            return self.Score(0, [])

        sylls = [self._score_syllable(syll) for syll in word]
        for i in range(len(word) - 1):
            # check if "butt" got split across syllables
            if 'butt' in (word[i] + word[i+1]).lower():
                sylls[i] = 0
            elif word[i+1][0].lower() == 't':
                sylls[i] += 1

        score = int(sum(sylls) // math.sqrt(len(sylls)))
        if score == 0:
            return self.Score(0, [])

        # earlier syllables are funnier
        if len(sylls) > 1:
            for i, mult in enumerate(prob.linspace( 2.0, 1.0, len(sylls) )):
                sylls[i] = int(sylls[i] * mult)

        # one-syllable words are always easy to butt
        if len(sylls) == 1:
            score += 3

        return self.Score(score, sylls)

    def _score_syllable(self, syll):
        syll = syll.lower()
        if syll in self.block_sylls: return 0
        if 'butt' in syll: return 0

        lengths = [0, 0, 1, 2, 3, 2, 2, 1]
        score = lengths[min(len(syll), len(lengths)-1)]
        if score == 0:
            return 0

        if re.match(r'^[^aeiou][aeiouy]([^aeiouy])\1', syll):
            score += 4
        elif re.match(r'^[^aeiou][aeiouy][^aeiouy]+$', syll):
            score += 2
        elif re.match(r'^[^aeiou][aeiouy][^aeiouy]', syll):
            score += 1

        if syll[0] == 'b': score += 2
        # bilabial/voiced plosives
        if syll[0] in 'pgd' and syll[1] != 'h': score += 1
        if syll[-1] == 't': score += 1
        if syll[-2] == 't': score += 1

        score = int(score ** 1.25)
        return score

    def sentence(self):
        return self.values.total

    def word(self, i=None):
        if i is None:
            return [w.total for w in self.values]
        else:
            return self.values[i].total

    def syllable(self, i, j=None):
        if j is None:
            return list(self.values[i])
        else:
            return self.values[i][j]


def score_sentence(text, scorer=Scorer, min_words=2):
    sent = grammar.Sentence(text)
    score = Scorer(sent, min_words)
    return sent, score

def buttify_sentence(sent, score, rate=60):
    count = min(sum(score.word())//rate+1, max(len(sent)//4, 1))
    word_indices = prob.weighted_sample(score.word(), count)

    # Get all the instances of the words we randomly selected.
    all_words = []
    for related in (sent.related(i) for i in word_indices):
        if related not in all_words:
            all_words.append(related)

    all_words = sorted(all_words, key = lambda *x_y: sort_lamb(*x_y))

    curr_count = 0
    for group in all_words:
        syllable = prob.weighted_choice(score.syllable(group[0]))
        curr_count += len(group)
        for word in group:
            buttify_word(sent, word, syllable)
        if curr_count >= count:
            break
    return str(sent)

def sort_lamb(*x_y):
    if len(x_y) is 1:
      return -1

    return len(x_y[1]) - len(x_y[0])

def buttify_word(sentence, word, syllable):
    butt = 'butt'

    # if the syllable has repeated characters, emulate that
    m = re.search(r'(.)\1{2,}', sentence[word][syllable])
    if m:
        butt = 'b' + 'u'*(m.end() - m.start()) + 'tt'

    if syllable == len(sentence[word])-1:
        if grammar.is_plural(str(sentence[word])):
            butt += 's'
        elif grammar.is_past_tense(str(sentence[word])):
            butt += 'ed'

    if sentence[word][syllable].isupper():
        sentence[word][syllable] = butt.upper()
    elif sentence[word][syllable].istitle():
        sentence[word][syllable] = butt.title()
    else:
        sentence[word][syllable] = butt.lower()

    # if there would be 3 't's in a row, remove one
    if (len(sentence[word]) > syllable+1 and
        sentence[word][syllable+1][0].lower() == 't'):
        sentence[word][syllable] = sentence[word][syllable][:-1]

    # if this is the first syllable and the previous word is "an", fix it
    if syllable == 0 and word > 0 and str(sentence[word-1]).lower() == 'an':
        sentence[word-1][0] = sentence[word-1][0][0:1]

def buttify(text, scorer=Scorer, rate=60, min_words=2):
    sent, score = score_sentence(text, scorer, min_words)
    if score.sentence() == 0:
        raise ValueError('sentence has too few buttable words')
    return buttify_sentence(sent, score)

if __name__ == '__main__':
    from optparse import OptionParser

    usage = 'usage: %prog [options] string'
    parser = OptionParser(usage=usage)
    parser.add_option('-m', '--min-words',
                  action='store', type='int', dest='min_words', default=2,
                  help='minimum number of words in a sentence')
    parser.add_option('-s', '--score',
                  action='store_true', dest='score', default=False,
                  help='show sentence score')

    (options, args) = parser.parse_args()
    if len(args) != 1:
        print(parser.get_usage())
        exit(1)

    text = args[0].decode('utf_8')
    if options.score:
        sent, score = score_sentence(text, min_words=options.min_words)

        print(u'{0}:'.format(score.sentence()))
        for i, word in enumerate(sent):
            if score.word(i) == 0:
                print(u'-'.join(word) + u'(0)')
            else:
                print(u'-'.join(word) + u'({0}: {1})'.format(
                    score.word(i), score.syllable(i)))
    else:
        print(buttify(text, min_words=options.min_words))
