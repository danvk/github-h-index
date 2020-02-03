#!/usr/bin/env python3

"""Calculate the h-index for GitHub users & organizations."""

import csv
from collections import defaultdict, Counter

user_to_repo_to_stars = defaultdict(lambda: Counter())

for row in csv.DictReader(open('repos-by-stars.csv')):
    user, repo = row['repo'].split('/', 1)
    stars = int(row['stars'])

    user_to_repo_to_stars[user][repo] = stars


def h_index(repo_to_stars: Counter):
    by_stars = repo_to_stars.most_common()
    for i, (repo, stars) in enumerate(by_stars):
        if (i + 1) > stars:
            return i
    return i + 1


user_to_h = Counter({
    k: h_index(v)
    for k, v in user_to_repo_to_stars.items()
})

for user, h in user_to_h.most_common():
    if h < 5:
        break
    print(f'{h:-5} {user}')
