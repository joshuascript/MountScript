#!/usr/bin/env python3
import os
import startup, commands, cli
from info_states import VersionInfo

def main():
    if os.geteuid() != 0:
        print("foldmount requires sudo — run with: sudo foldmount")
        return

    startup.initialize()

    parser = cli.build_parser()
    args = parser.parse_args()

    if not VersionInfo.meets_minimum:
        print(f"e2fsprogs {VersionInfo.version or 'unknown'} — version 1.45 or higher required")
        return

    handler = commands.REGISTRY.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()

main()
