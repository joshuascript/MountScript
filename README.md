# anneal
### Create case-insensitive directories on Linux

anneal converts any directory on your machine from case-sensitive to case-insensitive by backing it with an ext4 loop mount formatted with the `casefold` option.

## Requirements

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

> Uninstalling removes `/opt/anneal` and `/usr/local/bin/anneal`. Your images and mounts in `/var/lib/anneal/` are left intact.

## Usage

```bash
anneal <command> [directory]
```

## Commands

| Command | Description |
|---|---|
| `select <directory>` | Set the active directory for subsequent commands |
| `create [directory]` | Create a casefold mount (uses selected if omitted) |
| `remove [directory]` | Unmount and remove the image, preserving all files (uses selected if omitted) |
| `list` | Show all anneal images with mount status and fstab info |
| `permanent [directory]` | Add the mount to `/etc/fstab` so it persists across reboots (uses selected if omitted) |
| `permanent [directory] --remove` | Remove the mount from `/etc/fstab` |
| `fix` | Clear ghost volumes from Nautilus |

## Example

```bash
anneal select ~/Music
anneal create
anneal permanent
```

Or in one step:

```bash
anneal create ~/Music
anneal permanent ~/Music
```
