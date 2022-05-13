#!/usr/bin/python3
# yubikey-oath-dmenu - dmenu interface for getting OATH codes from a YubiKey
# Copyright (C) 2017-2018  Emil Lundberg <emil@emlun.se>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import click
import os
import re
import shlex
import shutil
import subprocess
import sys
import ykman.pcsc

from threading import Timer
from ykman.oath import calculate_steam, is_steam
from yubikit.core.smartcard import ApduError
from yubikit.core.smartcard import SW
from yubikit.core.smartcard import SmartCardConnection
from yubikit.oath import Credential
from yubikit.oath import OathSession


VERSION = '0.14.0'

notify_enabled = False

def notify_raw(ctx, *args, expire_time=3000, urgency='normal'):
    if notify_enabled:
        subprocess.run([
            'notify-send',
            '--app-name=%s' % ctx.info_name,
            '--expire-time=%d' % expire_time,
            '--urgency=%s' % urgency,
            *args
        ])


@click.pass_context
def notify(ctx, *args, **kwargs):
    notify_raw(ctx, *args, **kwargs)


def notify_err(*args):
    notify(*args, expire_time=5000, urgency='critical')


def touch_callback(ctx):
    print('Please touch your YubiKey...', file=sys.stderr)
    notify_raw(ctx, 'Please touch your YubiKey...')

def enter_password_if_needed(oath_controller, pinentry_program, retries=3):
    if retries == 0:
        return False
    else:
        try:
            oath_controller.list_credentials()
            return True
        except ApduError as e:
            if e.sw == SW.SECURITY_CONDITION_NOT_SATISFIED:
                try:
                    password = ask_password(pinentry_program)
                    if password is None:
                        return False
                    else:
                        verify_password(oath_controller, password)
                        return True

                except ApduError as ee:
                    if ee.sw == SW.INCORRECT_PARAMETERS:
                        return enter_password_if_needed(
                            oath_controller,
                            pinentry_program=pinentry_program,
                            retries = retries - 1
                        )
                    else:
                        raise
            else:
                raise


def ask_password(pinentry_program, retries=3):
    try:
        pinentry_process = subprocess.run(
            [pinentry_program],
            input='SETTITLE YubiKey OATH\nSETPROMPT Password:\nGETPIN\n',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8'
        )
        password_match = re.search(r"(?:^|\n)D (.*?)(?:^|\n)", pinentry_process.stdout)
        if password_match is None:
            print(pinentry_process.stdout)
            print(pinentry_process.stderr)
            return None
        else:
            return password_match.group(1)
    except FileNotFoundError as e:
        print(str(e))
        return None


def verify_password(oath_controller, password):
    key = oath_controller.derive_key(password)
    oath_controller.validate(key)


def format_cred_name(cred: Credential) -> str:
    return (f"{cred.issuer.strip()}: " if cred.issuer else "") + cred.name.strip()


@click.command(context_settings=dict(ignore_unknown_options=True))
@click.pass_context
@click.option('--clipboard', default=False, is_flag=True,
              help='Copy OTP to clipboard')
@click.option('--clipboard-cmd', metavar='CLIPBOARD_CMD', default=None,
              help='Command for copying to clipboard; should accept content on standard input. '
              'Implies --clipboard. '
              'If --clipboard-cmd is not present, --clipboard tries in order: "wl-copy", "xclip"')
@click.option('--menu-cmd', 'menu_cmd', metavar='MENU_CMD',
              help='Command used to summon the menu. '
              '''Default: dmenu -p 'Credentials:' -i''')
@click.option('--no-hidden', 'no_hidden', default=False, is_flag=True,
              help='Hide _hidden credentials')
@click.option('--notify', 'notify_enable', default=False, is_flag=True,
              help='Provide feedback via notify-send')
@click.option('--pinentry', 'pinentry_program', metavar='BINARY', default='pinentry',
              help='Use pinentry program BINARY to prompt for password when needed')
@click.option('--stdout', 'use_stdout', default=False, is_flag=True,
              help='Print OTP to standard output')
@click.option('--type', 'typeit', default=False, is_flag=True,
              help='Type OTP into focused window')
@click.help_option('-h', '--help')
@click.version_option(version=VERSION)
def cli(ctx, clipboard, clipboard_cmd, menu_cmd, notify_enable, no_hidden, pinentry_program, typeit, use_stdout):
    '''
    Select an OATH credential on your YubiKey using dmenu, then copy the
    corresponding OTP to the clipboard, "type" it, and/or print it to standard
    output.
    '''
    global notify_enabled
    notify_enabled = notify_enable

    def message(*args, console=True, notification=True, **kwargs):
        if console:
            print(*args, file=sys.stderr)
        if notification:
            notify(*args, **kwargs)

    def err_message(*args, console=True, notification=True):
        if console:
            print(*args, file=sys.stderr)
        if notification:
            notify_err(*args)

    typeit_cmd = None
    if typeit:
        if "WAYLAND_DISPLAY" in os.environ and shutil.which('wtype'):
            typeit_cmd = ['wtype']
        elif shutil.which('xdotool'):
            typeit_cmd = ['xdotool', 'type']
        else:
            err_message('Error: wtype or xdotool binary not found')
            sys.exit(1)

    if not (clipboard or typeit or use_stdout):
        err_message('No output mode specified. '
                    'Please specify --clipboard, --type, and/or --stdout.')
        sys.exit(1)

    clip_cmd = None
    if clipboard or clipboard_cmd is not None:
        if clipboard_cmd:
            clip_cmd = shlex.split(clipboard_cmd)
        elif shutil.which('wl-copy'):
            clip_cmd = ['wl-copy']
        elif shutil.which('xclip'):
            clip_cmd = ['xclip']
        else:
            err_message('Error: wl-copy or xclip binary not found')
            sys.exit(1)

    controllers = {i: OathSession(driver.open_connection(SmartCardConnection))
                   for i, driver in enumerate(
                       ykman.pcsc.list_devices())
                   }

    for k, ctrl in controllers.items():
        if not enter_password_if_needed(ctrl, pinentry_program):
            msg = 'Password authentication failed'
            notify_err(msg)
            ctx.fail(msg)

    credentials = {
        k: {format_cred_name(cred): cred
            for cred in ctrl.list_credentials() if not (no_hidden and cred.name.startswith("_hidden"))
            }
        for k, ctrl in controllers.items()
    }

    credential_ids = [cred_id
                      for creds in credentials.values()
                      for cred_id in creds.keys()
                      ]

    if len(credential_ids) != len(set(credential_ids)):
        dups = [id for id in credential_ids if credential_ids.count(id) > 1]
        err_message('Error: Credential ID present on multiple YubiKeys:\n'
                    + '\n'.join(set(dups)))
        sys.exit(1)

    credential_id_to_controller_idx = {
        cred_id: k
        for k, creds in credentials.items()
        for cred_id in creds.keys()
    }

    dmenu_proc = subprocess.Popen(
        shlex.split(menu_cmd if menu_cmd else '''dmenu -p 'Credentials:' -i'''),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        encoding='utf-8'
    )
    (selected_cred_id, _) = dmenu_proc.communicate('\n'.join(credential_ids))

    if dmenu_proc.returncode == 0:
        selected_cred_id = selected_cred_id.strip()

        ctrl_idx = credential_id_to_controller_idx[selected_cred_id]
        ctrl = controllers[ctrl_idx]

        touch_timer = Timer(0.500, touch_callback, [ctx])
        touch_timer.start()
        credential = credentials[ctrl_idx][selected_cred_id]
        if is_steam(credential):
            code = calculate_steam(ctrl, credential)
        else:
            code = ctrl.calculate_code(credential).value
        touch_timer.cancel()

        if typeit_cmd:
            subprocess.run(typeit_cmd + [code])

        if clip_cmd:
            clip_proc = subprocess.Popen(
                clip_cmd,
                stdin=subprocess.PIPE,
                encoding='utf-8'
            )
            clip_proc.communicate(code)
            message('OTP copied to clipboard: %s' % selected_cred_id)

        if use_stdout:
            print(code)

    else:
        message('Aborted by user.', notification=False)


if __name__ == '__main__':
    cli()
