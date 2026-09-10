"""Flask CLI commands (only registered in the app factory)."""

from __future__ import annotations

import click
from flask import Flask

from app.extensions import db


def register_cli_commands(app: Flask) -> None:
    app.cli.add_command(seed)


@click.command("seed")
@click.option("--force", is_flag=True, help="Re-seed even if data exists.")
def seed(force: bool) -> None:
    """Seed per-country slip cursors (dev-friendly default data)."""
    from app.models import Country, SlipCursor

    countries = [
        ("ghana", "BC8GMS6X"),
        ("kenya", "BC5AAAAA"),
        ("nigeria", "BCDBAAAA"),
        ("tanzania", "BCHAAAAA"),
        ("uganda", "BCCAAAAA"),
        ("zambia", "BCKAAAAA"),
    ]
    created = 0
    for country, code in countries:
        if not Country.query.filter_by(name=country).first():
            db.session.add(Country(name=country))
        existing = SlipCursor.query.filter_by(country=country).first()
        if existing:
            if force:
                existing.code = code
                db.session.add(existing)
            continue
        db.session.add(SlipCursor(country=country, code=code))
        created += 1
    db.session.commit()
    click.echo(f"Seed complete: {created} new cursors.")
