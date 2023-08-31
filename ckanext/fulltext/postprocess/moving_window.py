# -*- coding: utf-8 -*-

'''
a moving window moves over the text and tries to make the longest correct word
by combining temrs inside the winow.
for example, if the text is in format: 'term1 term2 term3',
it creates combinations as 'term1', 'term1term2' and 'term1term2term3'
and sets the longest one as the valid one.
also, it ignores the wrong terms. wrong terms is a term which is not in the dictionary
example:
original text: ham burg a ltona nors
moving window: hamburg altona
-nors is ignored because it is not in the dictionary

the dictionaries are in the sub-folder of the current folder, named 'dictionaries'
the name of the dictionary is read from config file
'''

import logging
from .settings import config
import os
from .utils import _get_words_arr, _replace_all, _is_email, _is_url
import re

__version__ = 1.0

logging.basicConfig()
logger = logging.getLogger(__name__)
if config.getboolean('clean_fulltext', 'debug') is True:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

class DictionaryBase():
    def is_valid(self, word):
        pass

class Dictionary_File(DictionaryBase):
    words_dict = None
    def __init__(self, file_path):
        self._name = file_path.split('/')[-1]
        with open(file_path) as f:
            words = f.readlines()
            words = [w.strip().lower() for w in words] 

            self._generate_dict(words)

    def _get_key(self, word):
        return word[:5]

    def _generate_dict(self, words):
        self.words_dict = dict()
        for w in words:
            key = self._get_key(w)
            if key in self.words_dict:
                self.words_dict[key].append(w)
            else:
                self.words_dict[key] = [w]

    def is_valid(self, w):
        if len(w) == 0:
            return False
        word = w.lower()
        #is_valid = word in self.words
        is_valid = False
        key = self._get_key(word)
        if key in self.words_dict:
            is_valid = word in self.words_dict[key]
        else:
            is_valid = False
        return is_valid

class ClearText():
    dictionaries = []
    split_chars = '._-'
    dic = {c:'' for c in split_chars}

    def __init__(self):
        # how many parts should be combined, in order to check in the dictionray
        self.window_size = config.getint('clean_fulltext', 'window_size')
        # the maximum allowed length for a word, it the combined parts are more than this value, then the moving window proceeds to the next part
        self.max_length = config.getint('clean_fulltext', 'word_max_length')
        # the minimum length allowed for a word to be checked, otherwise skip
        self.min_length = config.getint('clean_fulltext', 'word_min_length')
        # if a word is only with uppercase chars, should it be also checked? otherwise skip
        self.ignore_upper_case = config.getboolean('clean_fulltext', 'ignore_uppercase')
        self.unique = config.getboolean('clean_fulltext', 'unique')
        self._init_dictionaries()


    def _init_dictionaries(self):
        self.dictionaries = []
        file_dictionaries = config.get('clean_fulltext', 'file_dictionaries').split(',')
        for f in file_dictionaries:
            f = f.strip()
            file_path = os.path.dirname(__file__) + '/dictionaries/' + f
            self.dictionaries.append(Dictionary_File(file_path))

    def _is_valid(self, word):
        is_valid = False
        for d in self.dictionaries:
            if d.is_valid(word):
                return True
        return False

    def _preprocess_text(self, text):
        '''
        gets raw text and returns list of words
        '''
        words = _get_words_arr(text, delimiter='  ')
        ret = []
        for i, w in enumerate(words):
            if _is_email(w) or _is_url(w):
                ret.append(w)
                continue
            '''
            check if current term has split_chars
            if yes, check each part of the terms, and if all of them are correct
            then mark the whole term as correct by adding _skip_add at the end of the term
            '''
            if any(c in w for c in self.split_chars):
                tmp_word = _replace_all(w, self.dic)
                if self._is_valid(tmp_word): # check if merged word is correct
                    ret.append(tmp_word)
                else:
                    tmp_words = _get_words_arr(w, self.split_chars)
                    if len(tmp_words)==0:
                        ret.append(tmp_word)
                        continue
                    tmp_valid = True
                    for tw in tmp_words:
                        if not self._is_valid(tw):
                            tmp_valid = False
                            break
                    if tmp_valid and all(len(tw) > 1 for tw in tmp_words):
                        ret.append(w + '_SKIP_ADD')
                    else:
                        ret += tmp_words
            else:
                ret.append(w)

        return ret

    def clear_text(self, text):
        '''
        text: one line containing all words
        '''
        words = self._preprocess_text(text)
        clear_words = []
        not_found = []
        '''
        first separate with more than one space
        check each item and see it can be merged
        merge all and separate by space
        '''
        last = 0 # should show the last currect index
        current = 0
        total = len(words)
        reg_digit = re.compile('\d')
        while current < total:
            found = False
            skip = False # for logging wrong words
            if words[current].endswith('_SKIP_ADD'):
                words[current] = words[current].replace('_SKIP_ADD', '')
                found = True
                last = current + 1
            else:
                for i in range(current, current + min(self.window_size, total - current)):
                    if current != i and words[i][0].isupper(): # if next word starts with uppercase, break
                        #skip = True
                        break
                    word = ''.join(words[current:i + 1])
                    if _is_email(word) or _is_url(word):
                        skip = True
                        break
                    ''' REMOVE
                    if any(c in word.strip(self.stop_chars) for c in self.stop_chars):
                        break
                    '''
                    if reg_digit.search(word): # if word contains digits, break
                        skip = True
                        break
                    if len(word) < self.min_length: # if length of word is less than threshold, continue to next
                        skip = True
                        continue
                    if self.ignore_upper_case and word.isupper(): # if all the chars are uppercase, break if defined
                        skip = True
                        break
                    if len(word) >= self.max_length: # if max length is reached, break
                        skip = True
                        break
                    if self._is_valid(word):
                        last = i + 1
                        found = True
            if found:
                word = ''.join(words[current:last])
                clear_words.append(word)
                current = last
            else:
                #clear_words.append(words[current])
                if not skip:
                    not_found.append(words[current])
                current += 1
        return ' '.join(clear_words), not_found
