"""Nexus command-line entry point using one local Llama model."""
import argparse
import logging
import os

from dotenv import load_dotenv

from core.orchestrator import Orchestrator
from models.llama import LlamaModel


def main() -> None:
    load_dotenv()
    logging.basicConfig(
        level=os.getenv("NCLAW_LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="NClaw – lokaler Llama-Agent")
    parser.add_argument("--prompt", help="Aufgabe an das lokale Llama-Modell")
    args = parser.parse_args()

    nexus = Orchestrator()
    nexus.register("Nexus")
    nexus.register("Sandmann")
    print("NClaw gestartet. Registrierte Agenten:")
    for agent in nexus.snapshot():
        print(f"- {agent['name']}: {agent['state']}")

    if args.prompt:
        print("\nLlama denkt nach ...\n")
        answer = LlamaModel().generate(
            args.prompt,
            system="Du bist Llama, das einzige KI-Modell von NClaw. Antworte hilfreich, klar und auf Deutsch.",
        )
        print(answer)


if __name__ == "__main__":
    main()
