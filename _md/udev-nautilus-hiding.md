# Hiding foldmount Loop Devices from Nautilus via udev

## Rule

```
SUBSYSTEM=="block", KERNEL=="loop*", PROGRAM="/bin/sh -c 'losetup -n -O BACK-FILE %N | grep -q /var/lib/foldmount'", ENV{UDISKS_IGNORE}="1"
```

Place in `/etc/udev/rules.d/99-foldmount.rules`.

## How it works

Sets `UDISKS_IGNORE=1` on any loop device whose backing file lives under `/var/lib/foldmount/`. This tells udisks2 to suppress the device, so it never appears as a volume in Nautilus or other file managers.

## Scope

Global — applies to all foldmount mounts. Per-mount suppression is possible by calling `udevadm` after mounting, but not via a static rule.

## Install integration

- Install: drop the rule file, run `udevadm control --reload-rules`
- Uninstall: remove the rule file, run `udevadm control --reload-rules`

The `fix` command (which replays udev events reactively) would only be needed for devices mounted before the rule was in place.
