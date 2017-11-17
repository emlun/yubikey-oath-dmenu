yubikey-oath-dmenu
===

[dmenu][] interface for getting OATH codes from a [YubiKey][]

This program lets you pick an OATH credential from your YubiKey using [dmenu][],
and copies the corresponding OTP to the clipboard using [xclip][].
Alternatively, it can "type" the OTP using [xdotool][].


Usage
---

Invoke with `--help` to see the command line options.

    $ yubikey-oath-dmenu --help

Recommended usage is to map your preferred command line to a shortcut in your
window manager or desktop environment.

Note that your YubiKey may flash to ask you to touch it before generating the
code, and this program will give you no other indication of that.


Dependencies
---

- [dmenu][]
- [xclip][]
- [YubiKey Manager CLI][ykman], version 0.5.0 or later, installed in `$PATH` as
  `ykman`

Optional dependencies:

- [libnotify][]: For the `--notify` option, which uses `notify-send`
- [xdotool][]: For the `--type` option


Installation
---

- **Arch Linux**: [AUR package][aur]
- **Others**: Place `yubikey-oath-dmenu` somewhere on your `$PATH`.
  `/usr/local/bin/` probably works, for example.


[aur]: https://aur.archlinux.org/packages/yubikey-oath-dmenu
[dmenu]: https://tools.suckless.org/dmenu/
[libnotify]: https://developer.gnome.org/libnotify/
[xclip]: https://linux.die.net/man/1/xclip
[xdotool]: http://www.semicomplete.com/projects/xdotool/
[ykman]: https://github.com/Yubico/yubikey-manager
[YubiKey]: https://www.yubico.com/products/yubikey-hardware/
