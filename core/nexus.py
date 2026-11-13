"""Nexus command-line entry point using one local Llama model."""
import argparse
import logging
import os

from dotenv import load_dotenv

from core.orchestrator import Orchestrator
from models.llama import LlamaModel
from sandbox.storage import LocalSandbox
from tokenguard.handoff import HandoffStore
from tokenguard.monitor import TokenGuard


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
        system = (
            "Du bist Llama, das einzige KI-Modell von NClaw. "
            "Antworte hilfreich, klar und auf Deutsch."
        )
        storage = LocalSandbox()
        guard = TokenGuard()
        check = guard.check(args.prompt, system=system)
        print(
            f"TokenGuard: ungefähr {check.estimated_tokens}/{check.context_window} Tokens "
            f"({check.usage_ratio:.1%})."
        )
        if check.should_handoff:
            handoff = HandoffStore(storage.root).create(
                goal=args.prompt,
                model=os.getenv("MODEL_NAME", "llama3.2"),
                estimated_tokens=check.estimated_tokens,
                context_window=check.context_window,
                usage_ratio=check.usage_ratio,
            )
            print(
                "90-%-Grenze erreicht. Llama-Aufruf wurde sicherheitshalber nicht gestartet.\n"
                f"Lokaler JSON-Handoff gespeichert: {handoff}"
            )
            return
        print("\nLlama denkt nach ...\n")
        answer = LlamaModel().generate(args.prompt, system=system)
        print(answer)


if __name__ == "__main__":
    main()
