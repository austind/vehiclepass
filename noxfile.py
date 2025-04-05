"""Testing with Nox."""

import nox

nox.options.default_venv_backend = "uv|virtualenv"

UV_RUN = (
    "uv",
    "run",
    "--active",  # Ensures that uv uses the virtualenv created by nox, not the project's venv
)


@nox.session(python="3.9")
def type_checking(session):
    """Run type checking."""
    session.run(
        *UV_RUN,
        "mypy",
        "src",
    )


@nox.session(python="3.9")
def lint(session):
    """Run linting."""
    session.run(
        *UV_RUN,
        "ruff",
        "check",
        ".",
    )


@nox.session(python=["3.9", "3.10", "3.11", "3.12", "3.13"])
def tests(session):
    """Run unit tests."""
    session.run(
        *UV_RUN,
        "pytest",
    )
