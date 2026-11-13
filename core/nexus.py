"""Nexus command-line entry point."""
import logging
import os

from dotenv import load_dotenv

from core.orchestrator import Orchestrator


def main() -> None:
    load_dotenv()
    logging.basicConfig(
        level=os.getenv("NCLAW_LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    nexus = Orchestrator()
    nexus.register("Nexus")
    nexus.register("Sandmann")
    print("NClaw gestartet. Registrierte Agenten:")
    for agent in nexus.snapshot():
        print(f"- {agent['name']}: {agent['state']}")


if __name__ == "__main__":
    main()
