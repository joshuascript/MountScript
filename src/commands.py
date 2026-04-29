import os
import subprocess
import tempfile
from paths import Paths
from info_states import SessionState
import startup

# Returns a string describing the current state of a directory,
# checked in priority order so callers get the most specific classification.
def check_directory_state(directory: str) -> str:
    if not os.path.isdir(directory):
        return "does_not_exist"
    if startup.volume_cache.is_casefold_mount(directory):
        return "foldmount_mount"
    if startup.volume_cache.is_external_casefold(directory):
        return "external_casefold"
    if startup.volume_cache.is_mounted(directory):
        return "mounted"
    if os.listdir(directory):
        return "not_empty"
    return "empty"

def select(directory: str):
    directory = os.path.abspath(directory)
    state = check_directory_state(directory)

    if state == "does_not_exist":
        print(f"Directory does not exist: {directory}")
        return
    if state == "foldmount_mount":
        print(f"Already a foldmount casefold mount: {directory}")
        return
    if state == "external_casefold":
        print(f"External casefold mount detected: {directory}")
        return
    if state == "mounted":
        print(f"Directory is already mounted: {directory}")
        return

    SessionState.selected_directory = directory
    SessionState.save()
    print(f"Selected: {directory}")

def create(directory: str = None):
    target = directory or SessionState.selected_directory
    if not target:
        print("No directory specified. Run 'foldmount select <directory>' first, or pass a directory: 'foldmount create <directory>'")
        return

    target = os.path.abspath(target)
    state = check_directory_state(target)

    if state == "does_not_exist":
        print(f"Directory does not exist: {target}")
        return
    if state == "foldmount_mount":
        print(f"Already a foldmount casefold mount: {target}")
        return
    if state == "external_casefold":
        print(f"External casefold mount detected: {target}")
        return
    if state == "mounted":
        print(f"Directory is already mounted: {target}")
        return

    image_name = os.path.basename(target) + ".img"
    image_path = os.path.join(Paths.IMAGES_DIR, image_name)

    temp_dir = None
    if state == "not_empty":
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

def list_mounts():
    images = startup.image_cache.images
    if not images:
        print("No foldmount images found")
        return

    headers = ["DIRECTORY", "IMAGE", "SIZE", "LOOP", "STATUS", "PERM"]
    rows = []
    for image in images:
        volume = startup.volume_cache.get_by_source(image.image_path)
        directory = image.mounted_to if image.mounted_to else "-"
        img_name = os.path.basename(image.image_path)
        size = f"{image.size_gb}G"
        loop = volume.name if volume else "-"
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
    target = directory or SessionState.selected_directory
    if not target:
        print("No directory specified. Run 'foldmount select <directory>' first, or pass a directory: 'foldmount remove <directory>'")
        return

    target = os.path.abspath(target)
    state = check_directory_state(target)

    if state != "foldmount_mount":
        print(f"No foldmount mount found at: {target}")
        return

    image_name = os.path.basename(target) + ".img"
    image_path = os.path.join(Paths.IMAGES_DIR, image_name)

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

    if SessionState.selected_directory == target:
        SessionState.clear()

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

# Detaches the loop device backing the given image file.
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
    target = directory or SessionState.selected_directory
    if not target:
        print("No directory specified. Run 'foldmount select <directory>' first, or pass a directory: 'foldmount permanent <directory>'")
        return

    target = os.path.abspath(target)
    image_name = os.path.basename(target) + ".img"
    image_path = os.path.join(Paths.IMAGES_DIR, image_name)

    if remove:
        if target not in SessionState.permanent_directories:
            print(f"Not permanent: {target}")
            return
        with open("/etc/fstab", "r") as f:
            lines = f.readlines()
        filtered = [l for l in lines if image_path not in l]
        with open("/etc/fstab", "w") as f:
            f.writelines(filtered)
        SessionState.permanent_directories.remove(target)
        SessionState.save()
        print(f"Done — {target} will no longer mount at boot")
        return

    state = check_directory_state(target)
    if state != "foldmount_mount":
        print(f"No foldmount mount found at: {target}")
        return

    if target in SessionState.permanent_directories:
        print(f"Already permanent: {target}")
        return

    with open("/etc/fstab", "r") as f:
        fstab = f.read()
    if image_path in fstab:
        print(f"Already in /etc/fstab: {image_path}")
        SessionState.permanent_directories.append(target)
        SessionState.save()
        return

    fstab_line = f"{image_path}\t{target}\text4\tloop\t0\t0\n"
    with open("/etc/fstab", "a") as f:
        f.write(fstab_line)

    SessionState.permanent_directories.append(target)
    SessionState.save()
    print(f"Done — {target} will mount automatically at boot")

REGISTRY = {
    "select":    lambda args: select(args.directory),
    "create":    lambda args: create(args.directory),
    "remove":    lambda args: remove(args.directory),
    "list":      lambda args: list_mounts(),
    "fix":       lambda args: fix(),
    "permanent": lambda args: permanent(args.directory, args.remove),
}
