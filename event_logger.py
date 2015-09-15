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

import argparse
import getpass
import json
import os
import select
import time
import traceback

import dogpile.cache
import paramiko


GERRIT_TIMEOUT = 15
GERRIT_RECV_BYTES = 16384

DEBUG = False
VERBOSE = False


CACHE_DIR = os.path.expanduser('~/.gerrit-growler')
if not os.path.exists(CACHE_DIR):
    os.mkdir(CACHE_DIR, 0o0700)

CACHE = dogpile.cache.make_region().configure(
    'dogpile.cache.dbm',
    expiration_time=15,
    arguments={'filename': '%s/cache.dbm' % CACHE_DIR})


def get_client(host, port, username, password=None):
    """Return an authenticated SSH client."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.load_system_host_keys()
    try:
        client.connect(
            host,
            port=port,
            username=username,
            password=password)
    except paramiko.PasswordRequiredException:
        password = getpass.getpass('SSH Key Passphrase: ')
        return get_client(password=getpass.getpass('SSH Key Passphrase: '))
    except paramiko.AuthenticationException:
        raise SystemExit('Failed to authenticate against %s. Have you added '
                         'your SSH public key to Gerrit?' % host)
    return client


def list_events(host, port, username):
    """A real-time iterable of events occurring in gerrit."""
    return_buffer = ''
    try:
        client = get_client(host, port, username)
        stdin, stdout, stderr = client.exec_command('gerrit stream-events')

        while not stderr.channel.exit_status_ready():
            while stderr.channel.recv_ready():
                readable, w, e = select.select(
                    [stderr.channel], [], [], GERRIT_TIMEOUT)

                # readable will be an empty string when the channel closes
                if readable:
                    return_buffer += stderr.channel.recv(GERRIT_RECV_BYTES)
                    if '\n' in return_buffer:
                        event, return_buffer = return_buffer.split('\n', 1)
                        yield json.loads(event)
            # FIXME: there's got to be a more efficient way to idle here
            time.sleep(0.1)
    finally:
        client.close()


def is_priority(event, host, port, username):
    if 'change' not in event:
        # this is probably a ref-updated event
        return False

    return True


def log_event(event):
    event['received_at'] = time.time()
    with open('event.log', 'a') as f:
        f.write(json.dumps(event, separators=(',', ':')))
        f.write('\n')


def notify(event):
    """Emit a growl notification for the specified event."""
    # The notification title.
    title = event['change']['subject']

    # The notification message.
    message = list()
    message.append(event['type'].replace('-', ' ').capitalize())
    if 'author' in event:
        message.append('by')
        message.append(event['author'].get('name',
                                           event['author']['username']))
    for approval in event.get('approvals', []):
        message.append('(%(type)s %(negative)s%(value)s)' % {
            'type': approval['type'],
            'negative': '+' if '-' not in approval['value'] else '',
            'value': approval['value']})
    message = ' '.join(message)

    # The notification subtitle.
    subtitle = event['change']['project']

    # The URL of a resource to open when the user clicks the notification.
    url = 'https://review.openstack.org/%s' % event['change']['number']

    print((title, subtitle, message, url))


def main():
    global DEBUG, VERBOSE

    parser = argparse.ArgumentParser(
        description='Receive growl notifications for your starred changes in '
                    'Gerrit.')
    parser.add_argument(
        '--verbose', dest='verbose', action='store_true',
        help='Enable verbose output.')
    parser.add_argument(
        '--debug', dest='debug', action='store_true',
        help='Enable debug output.')
    parser.add_argument(
        '--host', dest='host',
        default='review.openstack.org',
        help='SSH hostname for Gerrit.')
    parser.add_argument(
        '--port', dest='port', type=int,
        default=29418,
        help='SSH port for Gerrit.')
    parser.add_argument(
        '--username', dest='username',
        default=getpass.getuser(),
        help='Your SSH username for Gerrit.')
    args = parser.parse_args()

    DEBUG = args.debug
    VERBOSE = args.verbose

    while True:
        try:
            for event in list_events(args.host, args.port, args.username):
                log_event(event)
                if is_priority(event, args.host, args.port, args.username):
                    notify(event)
        except Exception:
            traceback.print_exc()


if __name__ == '__main__':
    main()
