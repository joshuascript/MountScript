import argparse
from . import commands

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="anneal",
        description="Manage case-insensitive directories on Linux",
        epilog="Run 'anneal <command> --help' for help on a specific command.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(
        dest="command",
        metavar="{select, create, remove, list, fix, permanent}",
    )

    select_parser = subparsers.add_parser("select", help="Select a directory")
    select_parser.add_argument("directory", help="Path to the directory")
    select_parser.set_defaults(func=lambda args: commands.select(args.directory))

    create_parser = subparsers.add_parser("create", help="Create a casefold mount on the selected directory")
    create_parser.add_argument("directory", nargs="?", help="Path to the directory (optional if already selected)")
    create_parser.set_defaults(func=lambda args: commands.create(args.directory))

    remove_parser = subparsers.add_parser("remove", help="Remove the casefold mount from the selected directory")
    remove_parser.add_argument("directory", nargs="?", help="Path to the directory (optional if already selected)")
    remove_parser.set_defaults(func=lambda args: commands.remove(args.directory))

    list_parser = subparsers.add_parser("list", help="List all active anneal casefold mounts")
    list_parser.set_defaults(func=lambda args: commands.list_images())

    fix_parser = subparsers.add_parser("fix", help="Clear ghost volumes from Nautilus")
    fix_parser.set_defaults(func=lambda args: commands.fix())

    permanent_parser = subparsers.add_parser("permanent", help="Make the casefold mount permanent (use --remove to undo)")
    permanent_parser.add_argument("directory", nargs="?", help="Path to the directory (optional if already selected)")
    permanent_parser.add_argument("--remove", action="store_true", help="Remove the mount from fstab")
    permanent_parser.set_defaults(func=lambda args: commands.permanent(args.directory, args.remove))

    return parser
