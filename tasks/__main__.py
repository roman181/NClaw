"""Command-line interface for the local NClaw task ledger."""
from __future__ import annotations

import argparse

from tasks.store import STATUSES, TaskStore


def main() -> None:
    parser = argparse.ArgumentParser(description="NClaw – lokale Aufgabenverwaltung")
    commands = parser.add_subparsers(dest="command", required=True)

    add = commands.add_parser("add", help="Neue Aufgabe anlegen")
    add.add_argument("title")
    add.add_argument("--description", default="")
    add.add_argument("--priority", type=int, choices=range(1, 6), default=3)
    add.add_argument("--due")

    listing = commands.add_parser("list", help="Aufgaben anzeigen")
    listing.add_argument("--status", choices=sorted(STATUSES))
    listing.add_argument("--limit", type=int, default=100)

    show = commands.add_parser("show", help="Aufgabe und Verlauf anzeigen")
    show.add_argument("task_id")

    move = commands.add_parser("move", help="Status einer Aufgabe ändern")
    move.add_argument("task_id")
    move.add_argument("status", choices=sorted(STATUSES))
    move.add_argument("--note", default="")

    args = parser.parse_args()
    store = TaskStore()

    if args.command == "add":
        task = store.create(args.title, args.description, args.priority, args.due)
        print(f"Aufgabe angelegt: {task['id']} – {task['title']} [{task['status']}]")
    elif args.command == "list":
        for task in store.list(args.status, args.limit):
            print(f"{task['id']} | P{task['priority']} | {task['status']} | {task['title']}")
    elif args.command == "show":
        task = store.get(args.task_id)
        print(f"{task['title']} – {task['status']} (Priorität {task['priority']})")
        if task["description"]:
            print(task["description"])
        for event in store.history(args.task_id):
            print(f"{event['created_at']} | {event['old_status']} -> {event['new_status']} | {event['note']}")
    elif args.command == "move":
        task = store.transition(args.task_id, args.status, args.note)
        print(f"Status aktualisiert: {task['id']} -> {task['status']}")


if __name__ == "__main__":
    main()
