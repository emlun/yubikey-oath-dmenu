yubikey-oath-dmenu
===

[dmenu][] interface for getting OATH codes from a [YubiKey][]


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
- `xclip`
- [YubiKey Manager CLI][ykman], version 0.4.1 or later, installed in `$PATH` as
  `ykman`

Optional dependencies:

- [libnotify][]: For the `--notify` option, which uses `notify-send`
- `xdotool`: For the `--type` option


[dmenu]: https://tools.suckless.org/dmenu/
[libnotify]: https://developer.gnome.org/libnotify/
[ykman]: https://github.com/Yubico/yubikey-manager
[YubiKey]: https://www.yubico.com/products/yubikey-hardware/
