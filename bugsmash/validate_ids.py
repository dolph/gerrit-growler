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


def equal(s1, s2):
    if s1 is None and s2 is None:
        return True

    if s1 is None or s2 is None:
        return False

    if s1.lower() == s2.lower():
        return True


def gerrit_id(user):
    return user.get('gerrit_id', user.get('launchpad_id'))


if __name__ == '__main__':
    with open('default_data.json') as f:
        stackalytics_users = json.loads(f.read())['users']

    with open('unvalidated-ids') as f:
        bugsmash_ids = [s.strip() for s in f.readlines()]

    for token in bugsmash_ids:
        token = token.lower()
        for user in stackalytics_users:
            if equal(token, user.get('launchpad_id')):
                print(gerrit_id(user))
                break

            if equal(token, user.get('user_name')):
                print(gerrit_id(user))
                break

            for email in user.get('emails'):
                if equal(token, email):
                    print(gerrit_id(user))
                    break
        else:
            # sys.stderr.write('%s\n' % token)
            pass
