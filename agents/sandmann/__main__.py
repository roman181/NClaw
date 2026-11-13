"""Command-line interface for Sandmann file intake and inspection."""
from __future__ import annotations

import argparse
import json

from .agent import SandmannAgent


def main() -> None:
    parser = argparse.ArgumentParser(description="NClaw Sandmann – sichere lokale Dateianalyse")
    sub = parser.add_subparsers(dest="command", required=True)
    intake = sub.add_parser("import", help="Datei in incoming oder quarantine kopieren")
    intake.add_argument("path")
    inspect = sub.add_parser("inspect", help="Importierte Datei analysieren")
    inspect.add_argument("path")
    args = parser.parse_args()
    agent = SandmannAgent()
    if args.command == "import":
        result = agent.import_file(args.path)
    else:
        result = agent.inspect(args.path)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
