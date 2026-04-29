import os
import hashlib
import shutil
from dataclasses import dataclass, field


@dataclass
class FileConflict:
    path_a: str
    path_b: str
    same_hash: bool
    choice: str = ""  # set during resolve for same_hash=False


@dataclass
class DirConflict:
    keep: str
    remove: str


@dataclass
class ConflictCache:
    file_conflicts: list = field(default_factory=list)
    dir_conflicts: list = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return bool(self.file_conflicts or self.dir_conflicts)


def scan_conflicts(directory: str) -> ConflictCache:
    cache = ConflictCache()
    _scan_dir(directory, cache)
    return cache


def _scan_dir(directory: str, cache: ConflictCache):
    try:
        entries = os.listdir(directory)
    except PermissionError:
        return

    by_lower: dict[str, list[str]] = {}
    for name in entries:
        by_lower.setdefault(name.lower(), []).append(name)

    for key, names in by_lower.items():
        paths = [os.path.join(directory, n) for n in names]

        if len(names) == 1:
            if os.path.isdir(paths[0]):
                _scan_dir(paths[0], cache)
            continue

        all_files = all(os.path.isfile(p) for p in paths)
        all_dirs = all(os.path.isdir(p) for p in paths)

        if all_files:
            a, b = paths[0], paths[1]
            ha, hb = _file_hash(a), _file_hash(b)
            cache.file_conflicts.append(FileConflict(a, b, ha == hb))
        elif all_dirs:
            keep, remove = _uppercase_preferred(names[0], names[1])
            cache.dir_conflicts.append(DirConflict(
                os.path.join(directory, keep),
                os.path.join(directory, remove),
            ))
        else:
            print(f"  Warning: mixed file/directory conflict for '{key}' in {directory} — skipped")


def _file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _uppercase_preferred(name_a: str, name_b: str) -> tuple[str, str]:
    score_a = sum(c.isupper() for c in name_a)
    score_b = sum(c.isupper() for c in name_b)
    if score_a >= score_b:
        return name_a, name_b
    return name_b, name_a


def resolve_conflicts(cache: ConflictCache, directory: str) -> bool:
    print(f"\nCase conflicts found in {directory}:\n")

    auto = [f for f in cache.file_conflicts if f.same_hash]
    manual = [f for f in cache.file_conflicts if not f.same_hash]

    if auto:
        print("  Auto-resolved (identical content — uppercase variant kept):")
        for f in auto:
            keep_name, remove_name = _uppercase_preferred(
                os.path.basename(f.path_a), os.path.basename(f.path_b)
            )
            rel = os.path.relpath(os.path.dirname(f.path_a), directory)
            prefix = f"{rel}/" if rel != "." else ""
            print(f"    {prefix}{keep_name}  <-  {prefix}{remove_name}")

    if manual:
        print("\n  Requires input (different content):")
        for f in manual:
            rel_a = os.path.relpath(f.path_a, directory)
            rel_b = os.path.relpath(f.path_b, directory)
            print(f"    {rel_a}  vs  {rel_b}")

    if cache.dir_conflicts:
        print("\n  Directories to merge:")
        for d in cache.dir_conflicts:
            rel_keep = os.path.relpath(d.keep, directory)
            rel_remove = os.path.relpath(d.remove, directory)
            print(f"    {rel_keep}/  <-  {rel_remove}/")

    answer = input("\nMerge conflicts and proceed? [y/N]: ").strip().lower()
    if answer != "y":
        return False

    manual = [f for f in cache.file_conflicts if not f.same_hash]
    for i, conflict in enumerate(manual, 1):
        rel_a = os.path.relpath(conflict.path_a, directory)
        rel_b = os.path.relpath(conflict.path_b, directory)
        print(f"\n[{i}/{len(manual)}] File conflict:")
        print(f"  [1] {rel_a}")
        print(f"  [2] {rel_b}")
        while True:
            choice = input("  Keep which? [1/2/a=abort]: ").strip().lower()
            if choice == "1":
                conflict.choice = conflict.path_a
                break
            elif choice == "2":
                conflict.choice = conflict.path_b
                break
            elif choice == "a":
                return False

    return True


def apply_conflicts(cache: ConflictCache, directory: str):
    for conflict in cache.file_conflicts:
        if conflict.same_hash:
            _, remove_name = _uppercase_preferred(
                os.path.basename(conflict.path_a),
                os.path.basename(conflict.path_b),
            )
            remove_path = os.path.join(os.path.dirname(conflict.path_a), remove_name)
            os.remove(remove_path)
        else:
            remove_path = conflict.path_a if conflict.choice == conflict.path_b else conflict.path_b
            os.remove(remove_path)

    for conflict in cache.dir_conflicts:
        _merge_dirs(conflict.remove, conflict.keep)
        shutil.rmtree(conflict.remove)


def _merge_dirs(src: str, dst: str):
    for name in os.listdir(src):
        src_entry = os.path.join(src, name)
        dst_entry = os.path.join(dst, name)
        if os.path.isdir(src_entry):
            if os.path.isdir(dst_entry):
                _merge_dirs(src_entry, dst_entry)
            else:
                shutil.move(src_entry, dst_entry)
        else:
            os.replace(src_entry, dst_entry)
