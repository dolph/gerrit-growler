# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json
import os

import dogpile.cache
import requests


DEFAULT_DATA = 'default_data.json'
UNVALIDATED_IDS = 'unvalidated-ids'
VALIDATED_IDS = 'validated-ids'
INVALID_IDS = 'invalid-ids'


CACHE_DIR = '/tmp/gerrit-logger'
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR, 0o0700)

CACHE = dogpile.cache.make_region().configure(
    'dogpile.cache.dbm',
    expiration_time=60 * 60 * 24 * 7,
    arguments={
        'filename': '%s/cache.dbm' % CACHE_DIR,
    }
)


@CACHE.cache_on_arguments()
def GET(url, params=None):
    resp = requests.get(url, params=params)
    print('GET %s' % resp.url)
    resp.raise_for_status()
    data = resp.json()
    return data


STACKALYTICS = 'http://stackalytics.com/api/1.0'
USERS_ENDPOINT = STACKALYTICS + '/users'
CONTRIBUTORS = GET(USERS_ENDPOINT)['data']

for contributor in CONTRIBUTORS:
    user = GET(STACKALYTICS + '/users/' + contributor['id'])['user']
    contributor.update(user)


def equal(s1, s2):
    if s1 is None and s2 is None:
        return True

    if s1 is None or s2 is None:
        return False

    if s1.lower() == s2.lower():
        return True


def write_gerrit_id(contributor):
    with open(VALIDATED_IDS, 'a') as f:
        f.write('%s\n' % contributor['gerrit_id'])


def write_invalid_id(token):
    with open(INVALID_IDS, 'a') as f:
        f.write('%s\n' % token)


if __name__ == '__main__':
    # Truncate output files.
    with open(VALIDATED_IDS, 'w+') as f:
        pass

    with open(INVALID_IDS, 'w+') as f:
        pass

    with open(DEFAULT_DATA) as f:
        stackalytics_users = json.loads(f.read())['users']

    with open(UNVALIDATED_IDS) as f:
        bugsmash_ids = [s.strip() for s in f.readlines()]

    for token in bugsmash_ids:
        token = token.lower()
        found = True

        for contributor in CONTRIBUTORS:
            if equal(token, contributor.get('id')):
                found = True
                break

            if equal(token, contributor.get('launchpad_id')):
                found = True
                break

            if equal(token, contributor.get('user_id')):
                found = True
                break

            if equal(token, contributor.get('user_name')):
                found = True
                break

            if equal(token, contributor.get('gerrit_id')):
                found = True
                break

            if equal(token, contributor.get('text')):
                found = True
                break

            for email in contributor.get('emails'):
                if equal(token, email):
                    found = True
                    break

        if found:
            write_gerrit_id(contributor)
        else:
            write_invalid_id(token)

    print(
        ' '.join([
            'cat', VALIDATED_IDS, '|', 'sort', '-u', '>', '%s-sorted' %
            VALIDATED_IDS]))

    print(
        ' '.join([
            'mv', '%s-sorted' % VALIDATED_IDS, VALIDATED_IDS]))
