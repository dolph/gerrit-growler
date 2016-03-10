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
import re


BUG_PATTERN = '([Rr]elated|[Pp]artial|[Cc]loses)-[Bb]ug[:]?[\s]?[#]?([0-9]+)'
BUG_RE = re.compile(BUG_PATTERN, re.MULTILINE)


def debug(d):
    print(json.dumps(d, indent=4, sort_keys=True))


EVENTS = []
with open('bugsmash/events') as f:
    for line in f.readlines():
        EVENTS.append(json.loads(line))

USERS = []
with open('bugsmash/validated-ids') as f:
    for line in f.readlines():
        USERS.append(line.strip())

STATS = {
    'participants': set(),
    'new-patches': 0,
    'new-patches-total': 0,
    'approved-patches': set(),
    'code-reviews': 0,
    'revised-patches': 0,
    'revised-patches-total': 0,
    'patches-merged-total': 0,
    'impacted-bugs': set(),
    'fixed-bugs': set(),
    'contributors-registered': set(USERS),
}

for event in EVENTS:
    # We don't care about these events for summary purposes.
    if event['type'] in (
            'change-abandoned',
            'change-restored',
            'ref-replicated',
            'ref-replication-done',
            'ref-updated',
            'reviewer-added',
            'topic-changed'):
        continue

    bugs = BUG_RE.findall(event['change']['commitMessage'])

    if event['type'] == 'patchset-created':
        if event['patchSet']['kind'] in (
                'NO_CHANGE',
                'NO_CODE_CHANGE',
                'TRIVIAL_REBASE'):
            continue

        if event['patchSet']['kind'] == 'REWORK':
            if event['patchSet']['uploader']['username'] in USERS:
                STATS['participants'].add(
                    event['patchSet']['uploader']['username'])
                for impact, bug_number in bugs:
                    STATS['impacted-bugs'].add(int(bug_number))

            if int(event['patchSet']['number']) == 1:
                STATS['new-patches-total'] += 1
                if event['patchSet']['uploader']['username'] in USERS:
                    STATS['new-patches'] += 1
            else:
                STATS['revised-patches-total'] += 1
                if event['patchSet']['uploader']['username'] in USERS:
                    STATS['revised-patches'] += 1
        else:
            debug(event)
            raise SystemExit()
    elif event['type'] == 'comment-added':
        if event['author'].get('username') in USERS:
            STATS['code-reviews'] += 1
            STATS['participants'].add(event['author']['username'])
            for impact, bug_number in bugs:
                STATS['impacted-bugs'].add(int(bug_number))
            for approval in event.get('approvals', []):
                if approval['type'] == 'Workflow' and approval['value'] == '1':
                    STATS['approved-patches'].add(event['change']['number'])
                    break
    elif event['type'] == 'change-merged':
        STATS['patches-merged-total'] += 1
        if (event['patchSet']['author']['username'] in USERS or
                event['patchSet']['uploader']['username'] in USERS or
                event['change']['owner'] in USERS):
            for impact, bug_number in bugs:
                for impact, bug_number in bugs:
                    STATS['impacted-bugs'].add(int(bug_number))
                if impact.lower() in ('closes', 'partial'):
                    STATS['fixed-bugs'].add(int(bug_number))
    else:
        debug(event)
        raise Exception(event)

STATS['impacted-bugs'] = len(STATS['impacted-bugs'])
STATS['approved-patches'] = len(STATS['approved-patches'])
STATS['fixed-bugs'] = len(STATS['fixed-bugs'])
STATS['participants'] = len(STATS['participants'])
STATS['contributors-registered'] = len(STATS['contributors-registered'])
debug(STATS)
print(
    'Of %d contributors that were tracked, %d participated in gerrit '
    '(%.0f%%). Those %d participants did %d code reviews, authored patches to '
    'fix %d bugs, and impacted %d bugs in total.' % (
        STATS['contributors-registered'],
        STATS['participants'],
        100.0 * STATS['participants'] / STATS['contributors-registered'],
        STATS['participants'],
        STATS['code-reviews'],
        STATS['fixed-bugs'],
        STATS['impacted-bugs'],
    )
)
