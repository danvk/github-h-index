#!/usr/bin/env python

"""Pull all the results for a GitHub query, until hasNextPage is false."""

import fileinput
import json
import os
import requests
import sys
import time

token = open('.token').read().strip()

def run_query(payload, variables=None):
    r = requests.post(
        'https://api.github.com/graphql',
        headers={'Authorization': f'bearer {token}'},
        json={"query": payload, "variables": variables or {}}
    )
    r.raise_for_status()
    return r.json()


def find_page_info(d):
    if not isinstance(d, dict):
        return None

    for k, v in d.items():
        if k == 'pageInfo':
            return d
        r = find_page_info(v)
        if r is not None:
            return r

    return None


def scrape(q):
    all_nodes = []

    cursor = None
    while True:
        r = run_query(q, { 'start': cursor })
        pip = find_page_info(r)
        pi = pip['pageInfo']
        cursor = pi['endCursor']
        has_next = pi['hasNextPage']
        nodes = pip['nodes']

        all_nodes += nodes

        if 'rateLimit' in r:
            sys.stderr.write(r['rateLimit'], '\n')

        if not has_next:
            break

    return {
        'query': query,
        'nodes': all_nodes
    }


if __name__ == '__main__':
    query = ''.join(fileinput.input())
    print(json.dumps(scrape(query)))
