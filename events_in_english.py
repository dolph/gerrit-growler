# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
import fileinput
import json
import sys
import time


# http://stackoverflow.com/q/21129020/
reload(sys)
sys.setdefaultencoding('utf8')

BOTS = set()


def is_bot(user):
    if 'username' not in user:
        return False
    return user['username'] in BOTS or ' CI' in user['name']


def name(user):
    return '**%s**' % user.get('username', user['name'])
    if 'email' in user:
        return '[%s](mailto:%s) (%s)' % (
            user['name'], user['email'], user['username'])
    else:
        return '%s (%s)' % (
            user['name'], user['username'])


def review(review):
    return '`%s` [%s](%s)' % (
        review['project'],
        review['subject'],
        review['url'])


def pretty_print(event, message):
    if 'received_at' in event:
        received_at = time.gmtime(event['received_at'])
        print(u'- [{0}] {1}'.format(
            time.strftime('%Y-%m-%d %H:%M:%S', received_at).encode('utf-8'),
            message))


def main():
    for line in fileinput.input():
        event = json.loads(line)
        if event['type'] == 'change-abandoned':
            if is_bot(event['abandoner']):
                continue
            pretty_print(event, '%s abandoned %s' % (
                name(event['abandoner']),
                review(event['change'])))
        elif event['type'] == 'change-restored':
            if is_bot(event['restorer']):
                continue
            pretty_print(event, '%s restored %s' % (
                name(event['restorer']),
                review(event['change'])))
        elif event['type'] == 'patchset-created':
            if is_bot(event['uploader']):
                continue
            pretty_print(event, '%s revised %s' % (
                name(event['uploader']),
                review(event['change'])))
        elif event['type'] == 'change-merged':
            pretty_print(event, '%s merged %s' % (
                name(event['submitter']),
                review(event['change'])))
        elif event['type'] == 'comment-added':
            if is_bot(event['author']):
                continue
            code_review = 0
            verified = 0
            workflow = 0
            for approval in event.get('approvals', []):
                if approval['type'] == 'Workflow':
                    workflow = int(approval['value'])
                elif approval['type'] == 'Verified':
                    verified = int(approval['value'])
                elif approval['type'] == 'Code-Review':
                    code_review = int(approval['value'])

            if workflow >= 1:
                pretty_print(event, '%s approved %s' % (
                    name(event['author']),
                    review(event['change'])))
            elif workflow <= -1:
                pretty_print(event, '%s WIP\'d %s' % (
                    name(event['author']),
                    review(event['change'])))
            elif code_review != 0:
                pretty_print(event, '%s %s%d\'d %s' % (
                    name(event['author']),
                    '+' if code_review >= 1 else '',
                    code_review,
                    review(event['change']))),
            elif verified != 0:
                BOTS.add(event['author']['username'])
                pretty_print(event, '%s tested %s (%s%d)' % (
                    name(event['author']),
                    review(event['change']),
                    '+' if verified >= 1 else '',
                    verified))
            else:
                pretty_print(event, '%s commented on %s' % (
                    name(event['author']),
                    review(event['change'])))
        elif event['type'] == 'reviewer-added':
            # I think this is review request spam; ignore?
            pass
        elif event['type'] == 'topic-changed':
            # A bug was added to the commit message, etc; ignore?
            pass
        elif event['type'] == 'ref-updated':
            # I think this is a change rebased by gerrit; ignore?
            pass
        elif event['type'] == 'merge-failed':
            # Non-human event; ignore?
            pass
        else:
            raise SystemExit(json.dumps(event, indent=2))


if __name__ == '__main__':
    main()
