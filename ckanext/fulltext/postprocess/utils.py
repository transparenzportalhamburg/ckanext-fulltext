import re

_flatten = lambda l: [item for sublist in l for item in sublist]

def _replace_all(text, dic):
    for i, j in dic.items():
        text = text.replace(i, j)
    return text

def _is_url(word):
    if word.endswith('.de') or word.endswith('.com') or word.startswith('http'):
        return True
    return False

def _is_email(word):
    if len(word) > 7:
        if re.match("[^@]+@[^@]+\.[^@]+", word) != None:
            return True
    return False

def _get_words_arr(text, delimiter=",.!?/&-:;'... ", strip='-_,.;:\'\"!$%&/()=?[]\{\}+*/@'):
    words = re.split("["+"\\".join(delimiter)+"]", text) 
    words = [w.strip(strip) for w in words]
    return [w for w in words if w]