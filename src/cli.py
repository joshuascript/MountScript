import argparse

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mountscript",
        description="Manage case-insensitive directories on Linux"
    )
    subparsers = parser.add_subparsers(dest="command")

    select_parser = subparsers.add_parser("select", help="Select a directory")
    select_parser.add_argument("directory", help="Path to the directory")

    create_parser = subparsers.add_parser("create", help="Create a casefold mount on the selected directory")
    create_parser.add_argument("directory", nargs="?", help="Path to the directory (optional if already selected)")

    remove_parser = subparsers.add_parser("remove", help="Remove the casefold mount from the selected directory")
    remove_parser.add_argument("directory", nargs="?", help="Path to the directory (optional if already selected)")
    subparsers.add_parser("list", help="List all active MountScript casefold mounts")
    subparsers.add_parser("fix", help="Clear ghost volumes from Nautilus")
    permanent_parser = subparsers.add_parser("permanent", help="Make the casefold mount permanent")
    permanent_parser.add_argument("directory", nargs="?", help="Path to the directory (optional if already selected)")

    return parser
