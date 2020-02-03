#!/usr/bin/env python

"""Collect data on the most-starred repos using GitHub's GraphQL API."""

import json
import os
import requests
import time
from datetime import datetime, timedelta

token = open('.token').read()

def query(payload, variables=None):
    r = requests.post(
        'https://api.github.com/graphql',
        headers={'Authorization': f'bearer {token}'},
        json={"query": payload, "variables": variables or {}}
    )
    r.raise_for_status()
    return r.json()

repo_query = '''
query popular_repos($start: String, $num: Int!){
  rateLimit {
    cost
    remaining
    resetAt
  }
  search(query: "is:public %s", type: REPOSITORY, first: $num, after: $start) {
    repositoryCount
    pageInfo {
      hasNextPage
      endCursor
    }
    edges {
      node {
        ... on Repository {
          nameWithOwner
          createdAt
          forkCount
          isFork
          updatedAt
          primaryLanguage {
            name
          }
          stargazers {
            totalCount
          }
          watchers {
            totalCount
          }
        }
      }
    }
  }
}
'''

count_query = '''
query {
  rateLimit {
    cost
    remaining
    resetAt
  }
  search(query: "is:public %s", type: REPOSITORY, first: 1) {
    repositoryCount
  }
}
'''

def get_repos(q, cursor, num):
    return query(repo_query % q, {'start': cursor, 'num': num})['data']


def get_count(q):
    return query(count_query % q)['data']['search']['repositoryCount']


def scrape(q, out_file):
    if os.path.exists(out_file):
        print('Skipping', out_file, 'already exists')
        return
    all_repos = []
    cursor = None
    print('Creating', out_file)
    while True:
        r = get_repos(q, cursor, 100)
        search = r['search']
        pi = search['pageInfo']
        cursor = pi['endCursor']
        has_next = pi['hasNextPage']
        total = search['repositoryCount']
        if total > 1000:
            raise ValueError(f'Too many results for {q}: {total}')
        all_repos += [e['node'] for e in search['edges']]
        print(r['rateLimit'])
        print(len(all_repos), ' / ', total, cursor)
        if not has_next or r['rateLimit']['remaining'] < 10:
            break
    with open(out_file, 'w') as out:
        json.dump(all_repos, out)
    time.sleep(4)


def scrape_star_range(low, high):
    """Scrape a simple star range [low, high]."""
    out_file = f'repos.stars={low}..{high}.json'
    q = 'stars:%d..%d' % (low, high)
    scrape(q, out_file)


def scrape_breaks():
    breaks = json.load(open('breaks.json'))
    for hi, lo in zip(breaks[:-1], breaks[1:]):
        scrape_star_range(lo, hi - 1)


def scrape_star_dates():
    for stars in range(123, 15, -1):
        out_file = f'repos.star={stars}.-2015.json'
        q = 'stars:%d created:<=2015' % stars
        scrape(q, out_file)

        out_file = f'repos.star={stars}.2016-.json'
        q = 'stars:%d created:>=2016' % stars
        scrape(q, out_file)


def query_for_star_years(stars, start, end):
    q = 'stars:%s' % stars
    if start == 2010 and end == 2019:
        return q
    elif start == 2010:
        return f'{q} created:<={end}'
    elif end == 2019:
        return f'{q} created:>={start}'
    else:
        return f'{q} created:{start}..{end}'


def split_interval(a, b):
    d = int((b - a) / 2)
    return [(a, a + d), (a + d + 1, b)]


def split_by_year(stars, start, end):
    if start == 2010 and end == 2019:
        c = 1001  # we know this will fail.
    elif start == end:
        split_by_days(
            stars,
            datetime(start, 1, 1),
            datetime(start, 12, 31)
        )
        return
    else:
        q = query_for_star_years(stars, start, end)
        c = get_count(q)
    if c <= 1000:
        out_file = f'repos.star={stars}.{start}-{end}.json'
        print(f'query: {q}')
        scrape(q, out_file)
    else:
        if start == end:
            raise ValueError(f'Can\'t split any more for {stars} / {start}')
        print(f'{stars} {start}..{end} -> {c}, will split')
        for a, b in split_interval(start, end):
            split_by_year(stars, a, b)


def split_by_days(stars, day_start, day_end):
    start_fmt = day_start.strftime('%Y-%m-%d')
    end_fmt = day_end.strftime('%Y-%m-%d')
    q = query_for_star_years(stars, start_fmt, end_fmt)
    c = get_count(q)
    if c <= 1000:
        out_file = f'repos.star={stars}.{start_fmt}-{end_fmt}.json'
        print(f'query: {q}')
        scrape(q, out_file)
    else:
        days = (day_end - day_start).days
        if days == 0:
            raise ValueError(f'Can\'t split any more: {stars} / {day_start} .. {day_end}')
        for a, b in split_interval(0, days):
            dt_a = day_start + timedelta(days=a)
            dt_b = day_start + timedelta(days=b)
            split_by_days(stars, dt_a, dt_b)


def scrape_star_dates_split():
    #for stars in range(83, 15, -1):
    for stars in range(40, 15, -1):
        split_by_year(stars, 2010, 2019)


def scrape_range_days():
    # Scrape from a low star range up, splitting by creation date (which never changes).
    # ranges = [(15, 20), (21, 25), (26, 30), (31, 35), (36, 40), (41, 45), (46, 50)]
    #ranges = [(51, 60), (61, 70), (71, 80), (81, 90), (91, 100)]
    # ranges = [(100, 119), (120, 139), (140, 159), (160, 179), (180, 200)]
    # ranges = [(201, 225), (226, 250), (251, 300), (301, 400), (401, 500)]
    # ranges = [(501, 700), (701, 1000), (1001, 1500), (1501, 5000), (5001, 1_000_000)]
    ranges = [(1001, 1500), (1501, 5000), (5001, 1_000_000)]
    for a, b in ranges:
        stars = f'{a}..{b}'
        split_by_days(stars, datetime(2007, 1, 1), datetime(2020, 2, 2))


if __name__ == '__main__':
    # scrape_breaks()
    # scrape_star_dates()
    # scrape_star_dates_split()
    scrape_range_days()
