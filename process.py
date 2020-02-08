#!/usr/bin/env python3

"""Massage the scraped data into something simpler."""

import csv
import glob
import json
import os


repo_to_stars = {}

files = [
    f
    for f in glob.glob('responses/repos.star*.json')
    if os.path.isfile(f)
]
files.sort(key=lambda x: os.path.getmtime(x))

for f in files:
    rows = json.load(open(f))
    for row in rows:
        if not row:
            print('row is falsey!')
            continue
        lang = row['primaryLanguage']
        repo_to_stars[row['nameWithOwner']] = (
            row['stargazers']['totalCount'],
            row['createdAt'],
            row['updatedAt'],
            lang['name'] if lang else '',
            row['watchers']['totalCount'],
            row['forkCount'],
            1 if row['isFork'] else ''
        )


by_stars = sorted(repo_to_stars.items(), key=lambda rs: -rs[1][0])
out = csv.writer(open('repos-by-stars.csv', 'w'))
out.writerow(['repo', 'stars', 'created', 'udpated', 'language', 'watchers', 'forks', 'isFork'])
out.writerows((repo, *data) for repo, data in by_stars)
