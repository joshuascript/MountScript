import os
import subprocess
import tempfile
from src.paths import Paths
from src.info_states import SessionState
from src import startup

# checks the state of a directory — returns a string describing its current state
def check_directory_state(directory: str) -> str:
    if not os.path.isdir(directory):
        return "does_not_exist"
    if startup.volume_cache.is_casefold_mount(directory):
        return "mountscript_mount"
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
    if state == "mountscript_mount":
        print(f"Already a MountScript casefold mount: {directory}")
    if state == "external_casefold":
        print(f"External casefold mount detected: {directory}")
    if state == "mounted":
        print(f"Directory is already mounted: {directory}")
        return

    SessionState.selected_directory = directory
    SessionState.save()
    print(f"Selected: {directory}")

def create(directory: str = None):
    target = directory or SessionState.selected_directory
    if not target:
        print("No directory specified. Run 'mountscript select <directory>' first, or pass a directory: 'mountscript create <directory>'")
        return

    target = os.path.abspath(target)
    state = check_directory_state(target)

    if state == "does_not_exist":
        print(f"Directory does not exist: {target}")
        return
    if state == "mountscript_mount":
        print(f"Already a MountScript casefold mount: {target}")
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
        print("Stashing existing files...")
        temp_dir = tempfile.mkdtemp(dir=os.path.dirname(target))
        subprocess.run(["cp", "-a", target + "/.", temp_dir + "/"], check=True)
        subprocess.run(["rm", "-rf"] + [
            os.path.join(target, f) for f in os.listdir(target)
        ], check=True)

    try:
        print(f"Creating image {image_name}...")
        create_image(image_path)

        print("Formatting image...")
        format_image(image_path)

        print("Removing lost+found...")
        remove_lost_found(image_path)

        print("Mounting image...")
        mount_image(image_path, target)

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
    mounts = startup.volume_cache.casefold_volumes()
    if not mounts:
        print("No active MountScript mounts")
        return
    for v in mounts:
        print(f"{v.directory} <- {v.source_image}")

def remove(directory: str = None):
    target = directory or SessionState.selected_directory
    if not target:
        print("No directory specified. Run 'mountscript select <directory>' first, or pass a directory: 'mountscript remove <directory>'")
        return

    target = os.path.abspath(target)
    state = check_directory_state(target)

    if state != "mountscript_mount":
        print(f"No MountScript mount found at: {target}")
        return

    image_name = os.path.basename(target) + ".img"
    image_path = os.path.join(Paths.IMAGES_DIR, image_name)

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

def fix():
    subprocess.run(["udevadm", "trigger", "--subsystem-match=block"], check=True)
    print("Done — ghost volumes cleared")

def create_image(image_path: str, size_gb: int = 50):
    subprocess.run(["truncate", "-s", f"{size_gb}G", image_path], check=True)

def format_image(image_path: str):
    subprocess.run(["mkfs.ext4", "-O", "casefold", "-E", "encoding=utf8,encoding_flags=strict", image_path], check=True)

def mount_image(image_path: str, destination: str):
    subprocess.run(["sudo", "mount", "-o", "loop", image_path, destination], check=True)

def unmount_image(destination: str):
    subprocess.run(["sudo", "umount", "-l", destination], check=True)

# detaches the loop device backing the given image file
def detach_loop(image_path: str):
    result = subprocess.run(
        ["sudo", "losetup", "--output", "NAME", "--noheadings", "--associated", image_path],
        capture_output=True,
        text=True
    )
    loop_device = result.stdout.strip()
    if loop_device:
        subprocess.run(["sudo", "losetup", "-d", loop_device], check=True)

def remove_image(image_path: str):
    subprocess.run(["sudo", "rm", image_path], check=True)

# transfers ownership of the mounted directory to the current user
def set_ownership(destination: str):
    user = os.getlogin()
    subprocess.run(["sudo", "chown", f"{user}:{user}", destination], check=True)

def set_casefold(destination: str):
    subprocess.run(["sudo", "chattr", "+F", destination], check=True)

# removes lost+found directly from the image file before mounting
def remove_lost_found(image_path: str):
    subprocess.run(["sudo", "debugfs", "-w", image_path, "-R", "rmdir lost+found"], check=True)
