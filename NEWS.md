- Version 0.8.0 (unreleased)
  - Will now prompt for YubiKey OATH password if needed
  - New option `--pinentry` to set pinentry program to use to prompt for
    password when needed

- Version 0.7.0 - released 2018-10-20
  - New option `--dmenu-prompt` which is passed through as `-p` to dmenu -
    thanks Andrei Gherzan!

- Version 0.6.0 - released 2018-10-11
  - Unknown options and arguments are now passed through to dmenu - thanks
    @relatev!

- Version 0.5.1 - released 2018-10-09
  - Fixed version number

- Version 0.5.0 - released 2018-10-08
  - New option `--no-hidden` which hides credentials whose ID start with
    `_hidden` - thanks @relatev!

- Version 0.4.0 - released 2018-03-29
  - Now prints and notifies with a message asking to touch the YubiKey if needed

- Version 0.3.0 - released 2018-02-19
  - Complete rewrite in Python instead of shell; CLI should be mostly the same
  - Now supports multiple YubiKeys as long as no credential ID exists on both

- Version 0.2.0 - released 2017-11-17
  - Now requires `ykman>=0.5.0` and uses the `--single` option

- Version 0.1.1 - released 2017-11-17
  - Fix infinite-recursive substitution triggered by passing
    `--clipboard clipboard` option

- Version 0.1.0 - released 2017-11-17
  - Initial relase
