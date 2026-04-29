# anneal
### Native case-insensitive directories on Linux

anneal turns any Linux directory case-insensitive by backing it with a real ext4
filesystem formatted with the kernel's built-in `casefold` option. Your files
stay put. Your apps stop caring about case.

## About

- **Kernel-native** — no FUSE overlay, no userspace translation. Full ext4
  performance at every read and write.
- **Non-destructive** — anneal stashes your existing files, mounts the new
  image, and restores them automatically. Nothing is lost.
- **Conflict-aware** — before mounting, anneal scans for case-colliding files
  and lets you resolve them interactively.
- **Persistent** — one `anneal permanent` command writes an fstab entry so the
  mount survives reboots.

## How it works

anneal creates a sparse ext4 disk image with `-O casefold` enabled, loop-mounts
it over your target directory, and sets the casefold attribute. The result is a
real ext4 filesystem where `File.txt` and `file.txt` are the same file — resolved
at the kernel level, not through a compatibility shim.

## Requirements

- `python3`
- `e2fsprogs >= 1.45` (`mkfs.ext4`, `debugfs`)
- `losetup`, `findmnt`

## Install

```bash
./install.sh
```

To uninstall:

```bash
./install.sh --uninstall
```

> Uninstalling removes `/opt/anneal` and `/usr/local/bin/anneal`. Your images
> and data in `/var/lib/anneal/` are left intact.

## Commands

| Command | Description |
|---|---|
| `select <directory>` | Set the active directory for subsequent commands |
| `create [directory]` | Create a casefold mount (uses selected if omitted) |
| `remove [directory]` | Unmount and remove the image, preserving all files |
| `list` | Show all anneal mounts with status and fstab info |
| `permanent [directory]` | Add the mount to `/etc/fstab` so it persists across reboots |
| `permanent [directory] --remove` | Remove the mount from `/etc/fstab` |
| `fix` | Clear ghost volumes from Nautilus |

## Example

```bash
anneal create ~/Games/Skyrim
anneal permanent ~/Games/Skyrim
```

Or select first and reuse:

```bash
anneal select ~/Games/Skyrim
anneal create
anneal permanent
```
