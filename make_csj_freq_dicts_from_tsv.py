'''Script that generates various ranked frequency dictionaries in a forma
understood by yomitan from the CSJ frequency list tsv file which must be in
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

This script parses the data from the CSJ project and produces several
frequency dictionaries corresponding to the different rankings in different
domains for the words. Each dict only has one one term_meta_bank_1.json file
fwiw.

The dictionary source files are written to "{cwd}/CSJ dicts/{domain}/" per domain.

The zip files that can actually be imported in yomitan are written to
"{cwd}/CSJ releases/Corpus of Spontaneous Japanese - CSJ ({domain}).zip" per
domain.

'''

import datetime
import json
import os
import shutil
import zipfile

import jaconv
import numpy
import pandas as pd


def make_freq_listings(data, words, readings, domain, rank_key):
    ranks = data[rank_key].to_numpy()
    listings = []
    for i in range(len(data)):
        listings.append([
            words[i],
            'freq',
            { 'reading': jaconv.kata2hira(str(readings[i])), 'frequency': int(ranks[i]) }
        ])

    return listings


def get_index_metadata(domain, word_key):
    title = '話し言葉 CSJ'
    if domain != word_key:
        title += f' ({domain})'

    return {
        'title': title,
        'format': 3,
        'revision': f'CSJ_ver201803_{datetime.datetime.now(datetime.timezone.utc).isoformat()}',
        'frequencyMode': 'rank-based',
        'url': 'https://clrd.ninjal.ac.jp/csj/en/index.html',
        'description': 'Converted programmatically from the dataset. See repo at https://github.com/Maltesaa/CSJ_and_NWJC_yomitan_freq_dict. Fork of https://github.com/forsakeninfinity/CEJC_yomichan_freq_dict',
    }


word_key = 'lemma' # primary key for words in the dataset
reading_key = 'lForm' # key for the reading of the word in the dataset
overall_rank_key = 'rank' # key for overall (i.e., all domains combined) rank in the dataset

data = pd.read_csv('CSJ_frequencylist_suw_ver201803.tsv', sep='\t')
data.dropna(subset=['lemma'], inplace=True) # Drop empty words without data

# This is just parsing out the names of the various domains available in the dataset.
domains_to_rank_keys = {k.removesuffix('_rank') : k for k in data if k.endswith('_rank') and not 'コア' in k}
domains_to_rank_keys[word_key] = overall_rank_key

os.makedirs('CSJ releases', exist_ok=True)
words = data[word_key].to_numpy()
readings = data[reading_key].to_numpy()
for domain, rank_key in domains_to_rank_keys.items():
    freq_listings = make_freq_listings(data, words, readings, domain, rank_key)

    # Print a slice of the listings to verify that the format is correct
    print(f'\n\n{domain}\n----------\n')
    print(json.dumps(freq_listings[100:110], ensure_ascii=False))
    print(f'----------\n\n')

    with open('term_meta_bank_1.json', 'w', encoding='utf-8') as fp:
        json.dump(freq_listings, fp, ensure_ascii=False)

    with open('index.json', 'w', encoding='utf-8') as fp:
        json.dump(get_index_metadata(domain, word_key), fp, ensure_ascii=False)

    zip_path = f'Corpus of Spontaneous Japanese - CSJ'
    if domain != word_key:
        zip_path += f' ({domain})'
    zip_path += '.zip'
    with zipfile.ZipFile(zip_path, 'w') as outzip:
        outzip.write('index.json')
        outzip.write('term_meta_bank_1.json')

    os.makedirs(f'CSJ dicts/{domain}', exist_ok=True)
    shutil.move('term_meta_bank_1.json', f'CSJ dicts/{domain}')
    shutil.move('index.json', f'CSJ dicts/{domain}')
    shutil.move(zip_path, 'CSJ releases')
