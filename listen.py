import argparse
import getpass
import json
import os
import select
import subprocess
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
            time.sleep(1)
    finally:
        client.close()


def is_priority(event, host, port, username):
    """Priority changes are starred."""
    if 'change' not in event:
        # this is probably a ref-updated event
        return False

    change_number = event['change']['number']

    if 'author' in event:
        user = event['author'].get('username')
        if user == username:
            # this is an event we created ourselves, so ignore it
            print('Ourself: %s' % change_number)
            return False

    starred_review_numbers = starred_reviews(host, port, username)
    if VERBOSE:
        print('%sStarred: change %s in %s' % (
            'Not ' if change_number not in starred_review_numbers else '',
            change_number,
            event['change']['project']))
    return change_number in starred_review_numbers


@CACHE.cache_on_arguments(expiration_time=60)
def starred_reviews(host, port, username):
    """List change numbers of starred reviews."""
    command = ['gerrit query']
    command.extend(['--format=JSON'])
    command.extend(['is:starred'])

    return_buffer = ''
    try:
        client = get_client(host, port, username)

        if DEBUG:
            print(' '.join(command))
        stdin, stdout, stderr = client.exec_command(' '.join(command))

        while not stderr.channel.exit_status_ready():
            while stderr.channel.recv_ready():
                readable, w, e = select.select(
                    [stderr.channel], [], [], GERRIT_TIMEOUT)

                # readable will be an empty string when the channel closes
                if readable:
                    return_buffer += stderr.channel.recv(GERRIT_RECV_BYTES)
    finally:
        client.close()

    change_numbers = []
    try:
        for change in return_buffer.splitlines()[:-1]:
            change_numbers.append(json.loads(change)['number'])
    except IndexError:
        if DEBUG:
            print(return_buffer)
        return starred_reviews(retry=False)
    return change_numbers


def notify(event):
    """Emit a growl notification for the specified event."""
    command = ['terminal-notifier']

    # The notification title.
    title = event['change']['subject']
    command.extend(['-title', '"%s"' % title])

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
    command.extend(['-message', '"%s"' % message])

    # The notification subtitle.
    subtitle = event['change']['project']
    command.extend(['-subtitle', '"%s"' % subtitle])

    # The URL of a resource to open when the user clicks the notification.
    url = 'https://review.openstack.org/#/c/%s/' % event['change']['number']
    command.extend(['-open', '"%s"' % url])

    if DEBUG:
        print(' '.join(command))
    subprocess.call(command)


def main(args):
    global DEBUG, VERBOSE

    DEBUG = args.debug
    VERBOSE = args.verbose

    while True:
        try:
            for event in list_events(args.host, args.port, args.username):
                if is_priority(event, args.host, args.port, args.username):
                    notify(event)
        except Exception:
            traceback.print_exc()


if __name__ == '__main__':
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
    main(args)
