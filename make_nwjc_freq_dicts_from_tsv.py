'''Script that generates various ranked frequency dictionaries in a forma
understood by yomitan from the NWJC frequency list tsv file which must be in
the same folder as where the script is executed from.

Yomitan frequency dictionaries are a zip file that must contain the following:
1. an index.json fitting the schema documented at:
   https://github.com/FooSoft/yomichan/blob/master/ext/data/schemas/dictionary-index-schema.json
2. any number of term_meta_bank_{num}.json files where num > 0 fitting the schema documented at:
   https://github.com/FooSoft/yomichan/blob/master/ext/data/schemas/dictionary-term-meta-bank-v3-schema.json

In this case, we are picking a schema which differentiates between different
readings for the same term, for example,

[
    ["うん", "freq", {"reading": "うん", "frequency": 2}],
    ...,
    ["居る", "freq", {"reading": "いる", "frequency": 69}],
    ...,
    ["居る", "freq", {"reading": "おる", "frequency": 438}],
    ...
]
'''

import datetime
import json
import os
import shutil
import zipfile
import re
import jaconv
import numpy
import pandas as pd


def partial_hiragana_conversion(word, reading):
    common_chars = set(word)
    def replace_char(char):
        if char not in common_chars:
            return jaconv.kata2hira(char)
        else:
            return char

    result = ''.join(replace_char(char) for char in reading)
    return result

def make_freq_listings(data, words, readings, rank_key):
    ranks = data[rank_key].to_numpy()
    listings = []
    for i in range(len(data)):
        listings.append([
            words[i],
            'freq',
            { 'reading': jaconv.kata2hira(str(readings[i])) if not re.search(r'[ァ-ンー]+[一-龯]*', words[i]) else partial_hiragana_conversion(str(words[i]), str(readings[i])), 'frequency': int(ranks[i]) }
        ])

    return listings


def get_index_metadata():
    title = 'ウェブ NWJC'

    return {
        'title': title,
        'format': 3,
        'revision': f'NWJC_ver202202_{datetime.datetime.now(datetime.timezone.utc).isoformat()}',
        'frequencyMode': 'rank-based',
        'url': 'https://masayu-a.github.io/NWJC/',
        'description': 'Converted programmatically from the dataset. See repo at https://github.com/Maltesaa/CSJ_and_NWJC_yomitan_freq_dict. Fork of https://github.com/forsakeninfinity/CEJC_yomichan_freq_dict',
    }


word_key = 'lemma' # primary key for words in the dataset
reading_key = 'lForm' # key for the reading of the word in the dataset
overall_rank_key = 'rank' # key for overall (i.e., all domains combined) rank in the dataset

data = pd.read_csv('NWJC_frequencylist_suw_ver2022_02.tsv', sep='\t')
data.dropna(subset=['lemma'], inplace=True) # Drop empty words without data

os.makedirs('NWJC releases', exist_ok=True)
words = data[word_key].to_numpy()
readings = data[reading_key].to_numpy()
freq_listings = make_freq_listings(data, words, readings, overall_rank_key)

# Print a slice of the listings to verify that the format is correct
print(f'\n\n----------\n')
print(json.dumps(freq_listings[100:110], ensure_ascii=False))
print(f'----------\n\n')

with open('term_meta_bank_1.json', 'w', encoding='utf-8') as fp:
    json.dump(freq_listings, fp, ensure_ascii=False)

with open('index.json', 'w', encoding='utf-8') as fp:
    json.dump(get_index_metadata(), fp, ensure_ascii=False)

zip_path = f'NINJAL Web Japanese Corpus - NWJC'
zip_path += '.zip'
with zipfile.ZipFile(zip_path, 'w') as outzip:
    outzip.write('index.json')
    outzip.write('term_meta_bank_1.json')

os.makedirs(f'NWJC dicts/lemma', exist_ok=True)
shutil.move('term_meta_bank_1.json', f'NWJC dicts/lemma')
shutil.move('index.json', f'NWJC dicts/lemma')
shutil.move(zip_path, 'NWJC releases')