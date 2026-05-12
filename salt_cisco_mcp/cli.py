import argparse
import os
import sys

from salt_cisco_mcp import __version__
from salt_cisco_mcp.config import Settings
from salt_cisco_mcp.logging_config import configure_logging
from salt_cisco_mcp.verify import run_verify


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="salt-cisco-mcp",
        description="Offline-first MCP server for Salt-driven Cisco automation.",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    # serve
    serve_p = sub.add_parser("serve", help="Start the MCP server.")
    serve_p.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    serve_p.add_argument("--host", default="127.0.0.1")
    serve_p.add_argument("--port", type=int, default=7842)
    serve_p.add_argument("--allow-write", action="store_true", default=False)
    serve_p.add_argument("--config", metavar="PATH", default=None)

    # install
    sub.add_parser("install", help="Bootstrap the doc index on the Salt master.")

    # scrape
    sub.add_parser("scrape", help="Re-scrape docs.saltproject.io.")

    # verify
    verify_p = sub.add_parser("verify", help="Check salt-call and index status.")
    verify_p.add_argument("--config", metavar="PATH", default=None)

    # version
    sub.add_parser("version", help="Print the version and exit.")

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "version":
        print(__version__)
        return

    if args.command is None:
        parser.print_help()
        return

    if getattr(args, "config", None):
        os.environ["SALT_MCP_CONFIG_FILE"] = args.config

    settings = Settings()
    configure_logging(settings)

    if args.command == "serve":
        print("serve: not implemented yet (Milestone 3)", file=sys.stderr)
        sys.exit(0)

    if args.command == "install":
        print("install: not implemented yet (Milestone 13)", file=sys.stderr)
        sys.exit(0)

    if args.command == "scrape":
        print("scrape: not implemented yet (Milestone 2)", file=sys.stderr)
        sys.exit(0)

    if args.command == "verify":
        code = run_verify(
            salt_call_path=settings.salt_master.salt_call_path,
            doc_db_path=settings.paths.doc_db,
        )
        sys.exit(code)


if __name__ == "__main__":
    main()
