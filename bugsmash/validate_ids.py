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


DEFAULT_DATA = 'default_data.json'
UNVALIDATED_IDS = 'unvalidated-ids'
VALIDATED_IDS = 'validated-ids'
INVALID_IDS = 'invalid-ids'


def equal(s1, s2):
    if s1 is None and s2 is None:
        return True

    if s1 is None or s2 is None:
        return False

    if s1.lower() == s2.lower():
        return True


def write_gerrit_id(user):
    with open(VALIDATED_IDS, 'a') as f:
        f.write('%s\n' % user.get('gerrit_id', user.get('launchpad_id')))


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
        for user in stackalytics_users:
            if equal(token, user.get('launchpad_id')):
                write_gerrit_id(user)
                break

            if equal(token, user.get('user_name')):
                write_gerrit_id(user)
                break

            for email in user.get('emails'):
                if equal(token, email):
                    write_gerrit_id(user)
                    break
        else:
            # sys.stderr.write('%s\n' % token)
            pass

    print(
        ' '.join([
            'cat', VALIDATED_IDS, '|', 'sort', '-u', '>', '%s-sorted' %
            VALIDATED_IDS]))

    print(
        ' '.join([
            'mv', '%s-sorted' % VALIDATED_IDS, VALIDATED_IDS]))
