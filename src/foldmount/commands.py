import os
import subprocess
import tempfile
from .paths import Paths
from .models import Session, DirectoryState
from . import context, prepare

def image_path_for(target: str) -> str:
    return os.path.join(Paths.IMAGES_DIR, os.path.basename(target) + ".img")

def resolve_target(directory: str | None, cmd: str) -> str | None:
    target = directory or Session.selected_directory
    if not target:
        print(f"No directory specified. Run 'foldmount select <directory>' first, or pass a directory: 'foldmount {cmd} <directory>'")
        return None
    return os.path.abspath(target)

def _is_unavailable(state: DirectoryState, target: str) -> bool:
    messages = {
        DirectoryState.MISSING:           f"Directory does not exist: {target}",
        DirectoryState.FOLDMOUNT:         f"Already a foldmount casefold mount: {target}",
        DirectoryState.EXTERNAL_CASEFOLD: f"External casefold mount detected: {target}",
        DirectoryState.MOUNTED:           f"Directory is already mounted: {target}",
    }
    if state in messages:
        print(messages[state])
        return True
    return False

def get_directory_state(directory: str) -> DirectoryState:
    if not os.path.isdir(directory):
        return DirectoryState.MISSING
    if context.volume_cache.is_casefold_mount(directory):
        return DirectoryState.FOLDMOUNT
    if context.volume_cache.is_external_casefold(directory):
        return DirectoryState.EXTERNAL_CASEFOLD
    if context.volume_cache.is_mounted(directory):
        return DirectoryState.MOUNTED
    if os.listdir(directory):
        return DirectoryState.NOT_EMPTY
    return DirectoryState.EMPTY

def select(directory: str):
    directory = os.path.abspath(directory)
    state = get_directory_state(directory)
    if _is_unavailable(state, directory):
        return
    Session.selected_directory = directory
    Session.save()
    print(f"Selected: {directory}")

def create(directory: str = None):
    target = resolve_target(directory, "create")
    if not target:
        return

    state = get_directory_state(target)
    if _is_unavailable(state, target):
        return

    if state == DirectoryState.NOT_EMPTY:
        cache = prepare.scan_conflicts(target)
        if cache.has_conflicts:
            if not prepare.resolve_conflicts(cache, target):
                return
            prepare.apply_conflicts(cache, target)

    image_path = image_path_for(target)
    image_name = os.path.basename(image_path)

    temp_dir = None
    if state == DirectoryState.NOT_EMPTY:
        # Temp dir is placed next to the target so it stays on the same
        # underlying filesystem, avoiding a cross-device copy on restore.
        print("Stashing existing files...")
        temp_dir = tempfile.mkdtemp(dir=os.path.dirname(target))
        # The trailing "/." copies directory contents including hidden files.
        subprocess.run(["cp", "-a", target + "/.", temp_dir + "/"], check=True)
        subprocess.run(["rm", "-rf"] + [
            os.path.join(target, f) for f in os.listdir(target)
        ], check=True)

    try:
        print(f"Creating image {image_name}...")
        create_image(image_path)

        print("Formatting image...")
        format_image(image_path)

        # Removes lost+found from the image before mounting so it never
        # appears inside the user's directory.
        print("Removing lost+found...")
        remove_lost_found(image_path)

        print("Mounting image...")
        mount_image(image_path, target)

        # +F enables the casefold attribute, making lookups case-insensitive.
        print("Setting casefold...")
        set_casefold(target)

        print("Setting ownership...")
        set_ownership(target)

        if temp_dir:
            print("Restoring files...")
            subprocess.run(["cp", "-a", temp_dir + "/.", target + "/"], check=True)
            subprocess.run(["rm", "-rf", temp_dir], check=True)
            temp_dir = None
    except Exception:
        if temp_dir:
            print(f"Error during create — files are safe in: {temp_dir}")
        raise

    print(f"Done — {target} is now case-insensitive")

def list_images():
    images = context.image_cache.images
    if not images:
        print("No foldmount images found")
        return

    headers = ["DIRECTORY", "IMAGE", "SIZE", "LOOP", "STATUS", "PERM"]
    rows = []
    for image in images:
        volume = context.volume_cache.get_by_source(image.path)
        directory = image.mount_point if image.mount_point else "-"
        img_name = os.path.basename(image.path)
        size = f"{image.size_gb}G"
        loop = volume.loop_device if volume else "-"
        status = "mounted" if volume else "not mounted"
        permanent = "x" if image.permanent else "-"
        rows.append([directory, img_name, size, loop, status, permanent])

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    fmt = "  ".join(f"{{:<{w}}}" for w in col_widths)
    print(fmt.format(*headers))
    for row in rows:
        print(fmt.format(*row))

def remove(directory: str = None):
    target = resolve_target(directory, "remove")
    if not target:
        return

    state = get_directory_state(target)
    if state != DirectoryState.FOLDMOUNT:
        print(f"No foldmount mount found at: {target}")
        return

    image_path = image_path_for(target)

    # Stash files before unmounting — once the mount is gone the directory
    # reverts to its empty underlying state and the image is deleted.
    print("Stashing files...")
    temp_dir = tempfile.mkdtemp(dir=os.path.dirname(target))
    subprocess.run(["cp", "-a", target + "/.", temp_dir + "/"], check=True)

    try:
        print("Unmounting image...")
        unmount_image(target)

        print("Detaching loop device...")
        detach_loop(image_path)

        print("Removing image...")
        remove_image(image_path)
    except Exception:
        print(f"Error during remove — files are safe in: {temp_dir}")
        raise

    print("Restoring files...")
    subprocess.run(["cp", "-a", temp_dir + "/.", target + "/"], check=True)
    subprocess.run(["rm", "-rf", temp_dir], check=True)

    if Session.selected_directory == target:
        Session.clear()

    print(f"Done — {target} restored with files intact")

# Replays udev events on block devices, causing udisks2 to drop stale
# loop device entries that Nautilus shows as ghost volumes.
def fix():
    subprocess.run(["udevadm", "trigger", "--subsystem-match=block"], check=True)
    print("Done — ghost volumes cleared")

def create_image(image_path: str, size_gb: int = 50):
    # truncate creates a sparse file — it allocates no real disk space upfront.
    subprocess.run(["truncate", "-s", f"{size_gb}G", image_path], check=True)

def format_image(image_path: str):
    # encoding_flags=strict rejects filenames that aren't valid UTF-8.
    subprocess.run(["mkfs.ext4", "-O", "casefold", "-E", "encoding=utf8,encoding_flags=strict", image_path], check=True)

def mount_image(image_path: str, destination: str):
    subprocess.run(["mount", "-o", "loop", image_path, destination], check=True)

def unmount_image(destination: str):
    # -l (lazy) defers the unmount until the filesystem is no longer busy,
    # preventing failures if a file manager has the directory open.
    subprocess.run(["umount", "-l", destination], check=True)

def detach_loop(image_path: str):
    result = subprocess.run(
        ["losetup", "--output", "NAME", "--noheadings", "--associated", image_path],
        capture_output=True,
        text=True
    )
    loop_device = result.stdout.strip()
    if loop_device:
        subprocess.run(["losetup", "-d", loop_device], check=True)

def remove_image(image_path: str):
    subprocess.run(["rm", image_path], check=True)

# Transfers ownership of the mounted directory to the invoking user.
# The mount operation runs as root, so without this the directory is root-owned.
def set_ownership(destination: str):
    user = os.environ["SUDO_USER"]
    subprocess.run(["chown", f"{user}:{user}", destination], check=True)

def set_casefold(destination: str):
    subprocess.run(["chattr", "+F", destination], check=True)

# Uses debugfs to remove lost+found directly from the image before it is
# mounted — deleting it after mounting would leave it on the ext4 filesystem.
def remove_lost_found(image_path: str):
    subprocess.run(["debugfs", "-w", image_path, "-R", "rmdir lost+found"], check=True)

def permanent(directory: str = None, remove: bool = False):
    target = resolve_target(directory, "permanent")
    if not target:
        return

    image_path = image_path_for(target)

    if remove:
        if target not in Session.permanent_directories:
            print(f"Not permanent: {target}")
            return
        with open("/etc/fstab", "r") as f:
            lines = f.readlines()
        with open("/etc/fstab", "w") as f:
            f.writelines(l for l in lines if image_path not in l)
        Session.permanent_directories.remove(target)
        Session.save()
        print(f"Done — {target} will no longer mount at boot")
        return

    state = get_directory_state(target)
    if state != DirectoryState.FOLDMOUNT:
        print(f"No foldmount mount found at: {target}")
        return

    if target in Session.permanent_directories:
        print(f"Already permanent: {target}")
        return

    with open("/etc/fstab", "r") as f:
        fstab = f.read()
    if image_path in fstab:
        print(f"Already in /etc/fstab: {image_path}")
        Session.permanent_directories.append(target)
        Session.save()
        return

    with open("/etc/fstab", "a") as f:
        f.write(f"{image_path}\t{target}\text4\tloop\t0\t0\n")

    Session.permanent_directories.append(target)
    Session.save()
    print(f"Done — {target} will mount automatically at boot")
