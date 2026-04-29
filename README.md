# foldmount
### Create case-insensitive directories on Linux

foldmount converts any directory on your machine from case-sensitive to case-insensitive by backing it with an ext4 loop mount formatted with the `casefold` option.

## Requirements

- `sudo`
- `python3`
- `e2fsprogs >= 1.45` (`mkfs.ext4`, `debugfs`)
- `losetup`, `findmnt`

## Install

```bash
sudo ./install.sh
```

To uninstall:

```bash
sudo ./install.sh --uninstall
```

> Uninstalling removes `/opt/foldmount` and `/usr/local/bin/foldmount`. Your images and mounts in `/var/lib/foldmount/` are left intact.

## Usage

```bash
foldmount <command> [directory]
```

## Commands

| Command | Description |
|---|---|
| `select <directory>` | Set the active directory for subsequent commands |
| `create [directory]` | Create a casefold mount (uses selected if omitted) |
| `remove [directory]` | Unmount and remove the image, preserving all files (uses selected if omitted) |
| `list` | Show all foldmount images with mount status and fstab info |
| `permanent [directory]` | Add the mount to `/etc/fstab` so it persists across reboots (uses selected if omitted) |
| `permanent [directory] --remove` | Remove the mount from `/etc/fstab` |
| `fix` | Clear ghost volumes from Nautilus |

## Example

```bash
foldmount select ~/Music
foldmount create
foldmount permanent
```

Or in one step:

```bash
foldmount create ~/Music
foldmount permanent ~/Music
```
