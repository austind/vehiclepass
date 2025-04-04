"""Testing with Nox."""

import nox


@nox.session(python="3.10")
def lint(session):
    """Run linting."""
    session.install("uv")
    session.run("uv", "sync", "--active")
    session.run(
        "uv",
        "run",
        "--active",  # Ensures that uv uses the virtualenv created by nox, not the project's venv
        "ruff",
        "check",
        ".",
    )


@nox.session(python=["3.9", "3.10", "3.11", "3.12", "3.13"])
def tests(session):
    """Run unit tests."""
    session.install("uv")
    session.run("uv", "sync")
    session.run(
        "uv",
        "run",
        "--active",  # Ensures that uv uses the virtualenv created by nox, not the project's venv
        "pytest",
    )
