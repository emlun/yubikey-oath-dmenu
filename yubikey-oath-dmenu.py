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
import re
import shutil
import shlex
import subprocess
import sys
import ykman.driver_ccid
import ykman.oath

from threading import Timer


VERSION = '0.9.0'

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
            oath_controller.list()
            return True
        except ykman.oath.APDUError as e:
            if e.sw == ykman.oath.SW.SECURITY_CONDITION_NOT_SATISFIED:
                try:
                    password = ask_password(pinentry_program)
                    if password is None:
                        return False
                    else:
                        verify_password(oath_controller, password)
                        return True

                except ykman.oath.APDUError as ee:
                    if ee.sw == ykman.oath.SW.INCORRECT_PARAMETERS:
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


@click.command(context_settings=dict(ignore_unknown_options=True))
@click.pass_context
@click.option('--clipboard', metavar='CLIPBOARD',
              help='DEPRECATED: Use --clipboard-cmd instead. '
              'Passed through as -selection option to xclip; ignored if --clipboard-cmd is given')
@click.option('--clipboard-cmd', metavar='CLIPBOARD_CMD',
              help='Copy-to-clipboard command to use instead of xclip')
@click.option('--dmenu-prompt', 'dmenu_prompt', metavar='PROMPT',
              help='DEPRECATED: Use --menu-cmd instead. '
              'Passed as -p argument to dmenu.')
@click.option('--menu-cmd', 'menu_cmd', metavar='MENU_CMD',
              help='Command used to summon the menu. '
              '''Default: dmenu -p 'Credentials:' -i''')
@click.help_option('-h', '--help')
@click.option('--no-hidden', 'no_hidden', default=False, is_flag=True,
              help='Hide _hidden credentials')
@click.option('--notify', 'notify_enable', default=False, is_flag=True,
              help='Provide feedback via notify-send')
@click.option('--pinentry', 'pinentry_program', metavar='BINARY', default='pinentry',
              help='Use pinentry program BINARY to prompt for password when needed')
@click.option('--type', 'typeit', default=False, is_flag=True,
              help='Type code instead of copying to clipboard')
@click.argument('dmenu_args', nargs=-1, type=click.UNPROCESSED)
@click.version_option(version=VERSION)
def cli(ctx, clipboard, clipboard_cmd, dmenu_prompt, menu_cmd, notify_enable, no_hidden, pinentry_program, typeit, dmenu_args):
    '''
    Select an OATH credential on your YubiKey using dmenu, then copy the
    corresponding OTP to the clipboard.

    Unknown options and arguments are passed through to dmenu.
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

    if clipboard:
        message('Warning: --clipboard is deprecated and will be removed in the next release, please use --clipboard-cmd instead.',
                expire_time=10000)

    typeit_cmd = None
    if typeit:
        if shutil.which('wtype'):
            typeit_cmd = ['wtype']
        elif shutil.which('xdotool'):
            typeit_cmd = ['xdotool', 'type']
        else:
            err_message('Error: wtype or xdotool binary not found')
            sys.exit(1)

    if dmenu_prompt:
        message('Warning: --dmenu-prompt is deprecated and will be removed in the next release, please use --menu-cmd instead.',
                expire_time=10000)

    if dmenu_args:
        message('Warning: trailing dmenu arguments are deprecated and will be removed in the next release, please use --menu-cmd instead.',
                expire_time=10000)

    if menu_cmd and (dmenu_args or dmenu_prompt):
        if dmenu_prompt:
            err_message('Error: --menu-cmd conflicts with --dmenu-prompt')
        if dmenu_args:
            err_message('Error: --menu-cmd conflicts with trailing dmenu arguments')
        sys.exit(1)

    controllers = {i: ykman.oath.OathController(driver)
                   for i, driver in enumerate(
                       ykman.driver_ccid.open_devices())
                   }

    for k, ctrl in controllers.items():
        if not enter_password_if_needed(ctrl, pinentry_program):
            msg = 'Password authentication failed'
            err_message(msg)
            sys.exit(1)

    credentials = {
        k: {cred.printable_key: cred
            for cred in ctrl.list() if not (no_hidden and cred.printable_key.startswith("_hidden"))
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
        shlex.split(menu_cmd) if menu_cmd
        else ['dmenu', '-p', dmenu_prompt or 'Credentials:', '-i'] + list(dmenu_args),
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
        code = ctrl.calculate(credentials[ctrl_idx][selected_cred_id]).value
        touch_timer.cancel()

        if typeit_cmd:
            subprocess.run(typeit_cmd + [code])
        else:
            clip_cmd = shlex.split('xclip' if clipboard_cmd is None else clipboard_cmd)
            if clipboard_cmd is None and clipboard is not None:
                clip_cmd += ['-selection', clipboard]
            clip_proc = subprocess.Popen(
                clip_cmd,
                stdin=subprocess.PIPE,
                encoding='utf-8'
            )
            clip_proc.communicate(code)
            message('OTP copied to clipboard: %s' % selected_cred_id)

    else:
        message('Aborted by user.', notification=False)


if __name__ == '__main__':
    cli()
