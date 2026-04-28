#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import startup, commands, cli
from src.info_states import VersionInfo

def main():
    if os.geteuid() != 0:
        print("mountscript requires sudo — run with: sudo mountscript")
        return

    startup.initialize()

    parser = cli.build_parser()
    args = parser.parse_args()

    if not VersionInfo.meets_minimum:
        print(f"e2fsprogs {VersionInfo.version or 'unknown'} — version 1.45 or higher required")
        return

    if args.command == "select":
        commands.select(args.directory)
    elif args.command == "create":
        commands.create(args.directory)
    elif args.command == "remove":
        commands.remove(args.directory)
    elif args.command == "list":
        commands.list_mounts()
    elif args.command == "fix":
        commands.fix()
    elif args.command == "permanent":
        pass
    else:
        parser.print_help()

main()
