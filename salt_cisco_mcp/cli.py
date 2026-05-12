import argparse
import os
import sys

import anyio

from salt_cisco_mcp import __version__
from salt_cisco_mcp.config import Settings
from salt_cisco_mcp.docs.scraper import scrape_docs
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
    install_p = sub.add_parser("install", help="Bootstrap config dirs and write a starter config.")
    install_p.add_argument("--config-dir", default="/etc/salt/mcp", metavar="PATH")
    install_p.add_argument("--data-dir", default="/var/lib/salt-mcp", metavar="PATH")
    install_p.add_argument("--log-dir", default="/var/log/salt-mcp", metavar="PATH")
    install_p.add_argument("--audit-dir", default="~/.salt-mcp", metavar="PATH")
    install_p.add_argument("--dry-run", action="store_true", default=False)

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
        if args.transport:
            settings.server.transport = args.transport
        if args.host:
            settings.server.http_host = args.host
        if args.port:
            settings.server.http_port = args.port
        if args.allow_write:
            settings.server.allow_write = True
        from salt_cisco_mcp.transports import run_server

        run_server(settings)

    if args.command == "install":
        from salt_cisco_mcp.install_cmd import install_logic

        result = install_logic(
            config_dir=args.config_dir,
            data_dir=args.data_dir,
            log_dir=args.log_dir,
            audit_dir=args.audit_dir,
            dry_run=args.dry_run,
        )
        prefix = "[DRY RUN] " if args.dry_run else ""
        for d in result.created_dirs:
            print(f"{prefix}directory: {d}")
        if result.config_file:
            print(f"{prefix}config written: {result.config_file}")
        for w in result.warnings:
            print(f"WARNING: {w}", file=sys.stderr)
        if result.success:
            print("\nNext steps:")
            print(f"  1. Edit {args.config_dir}/config.yaml")
            print("  2. Run: salt-cisco-mcp scrape")
            print("  3. Run: salt-cisco-mcp serve --transport http")
        sys.exit(0 if result.success else 1)

    if args.command == "scrape":

        async def _run_scrape() -> None:
            stats = await scrape_docs(settings, settings.paths.doc_db)
            print(
                f"scrape complete: {stats.pages_fetched} pages fetched, "
                f"{stats.chunks_written} chunks indexed",
                file=sys.stderr,
            )

        anyio.run(_run_scrape)
        sys.exit(0)

    if args.command == "verify":
        config_file = os.environ.get("SALT_MCP_CONFIG_FILE", "/etc/salt/mcp/config.yaml (default)")
        print(f"config file : {config_file}")
        print(f"transport   : {settings.server.transport}")
        print(f"allow_write : {settings.server.allow_write}")
        print(f"salt-call   : {settings.salt_master.salt_call_path}")
        print(f"doc_db      : {settings.paths.doc_db}")
        print(f"telemetry   : {'on' if settings.telemetry.enabled else 'off'}")
        print()
        code = run_verify(
            salt_call_path=settings.salt_master.salt_call_path,
            doc_db_path=settings.paths.doc_db,
            metrics_dir=settings.telemetry.metrics_dir,
        )
        sys.exit(code)


if __name__ == "__main__":
    main()
