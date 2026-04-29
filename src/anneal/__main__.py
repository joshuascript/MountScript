import os
from . import context, cli
from .models import VersionInfo

def main():
    if os.geteuid() != 0:
        print("anneal requires sudo — run with: sudo anneal")
        return

    context.initialize()

    parser = cli.build_parser()
    args = parser.parse_args()

    if not VersionInfo.meets_minimum:
        print(f"e2fsprogs {VersionInfo.version or 'unknown'} — version 1.45 or higher required")
        return

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

main()
