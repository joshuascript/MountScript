import argparse

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="foldmount",
        description="Manage case-insensitive directories on Linux",
        epilog="Run 'foldmount <command> --help' for help on a specific command.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(
        dest="command",
        metavar="{select, create, remove, list, fix, permanent}",
    )

    select_parser = subparsers.add_parser("select", help="Select a directory")
    select_parser.add_argument("directory", help="Path to the directory")

    create_parser = subparsers.add_parser("create", help="Create a casefold mount on the selected directory")
    create_parser.add_argument("directory", nargs="?", help="Path to the directory (optional if already selected)")

    remove_parser = subparsers.add_parser("remove", help="Remove the casefold mount from the selected directory")
    remove_parser.add_argument("directory", nargs="?", help="Path to the directory (optional if already selected)")
    subparsers.add_parser("list", help="List all active foldmount casefold mounts")
    subparsers.add_parser("fix", help="Clear ghost volumes from Nautilus")
    permanent_parser = subparsers.add_parser("permanent", help="Make the casefold mount permanent (use --remove to undo)")
    permanent_parser.add_argument("directory", nargs="?", help="Path to the directory (optional if already selected)")
    permanent_parser.add_argument("--remove", action="store_true", help="Remove the mount from fstab")

    return parser
