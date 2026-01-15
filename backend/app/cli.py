"""CLI commands for the Homelab Manager application."""

import click
from flask.cli import with_appcontext

from app.database import Session
from app.models.user import User


@click.command("create-admin")
@click.option("--username", prompt=True, help="Admin username")
@click.option("--email", prompt=True, help="Admin email address")
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="Admin password",
)
@with_appcontext
def create_admin(username: str, email: str, password: str):
    """Create an initial admin user.

    This command creates an administrator account for the Homelab Manager.
    Use this when setting up the application for the first time.

    Example:
        flask create-admin --username admin --email admin@example.com
    """
    db = Session()
    try:
        # Check if username already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            click.echo(click.style(f"Error: User '{username}' already exists.", fg="red"))
            return

        # Check if email already exists
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            click.echo(click.style(f"Error: Email '{email}' is already in use.", fg="red"))
            return

        # Create the admin user
        admin = User(
            username=username,
            email=email,
            is_admin=True,
            is_active=True,
        )
        admin.set_password(password)

        db.add(admin)
        db.commit()

        click.echo(click.style(f"Admin user '{username}' created successfully!", fg="green"))
        click.echo(f"  Username: {username}")
        click.echo(f"  Email: {email}")
        click.echo("  Admin: Yes")

    except Exception as e:
        db.rollback()
        click.echo(click.style(f"Error creating admin user: {str(e)}", fg="red"))
        raise
    finally:
        db.close()


@click.command("list-users")
@with_appcontext
def list_users():
    """List all users in the system."""
    db = Session()
    try:
        users = db.query(User).all()
        if not users:
            click.echo("No users found.")
            return

        click.echo(f"\n{'ID':<5} {'Username':<20} {'Email':<30} {'Admin':<7} {'Active':<7}")
        click.echo("-" * 75)
        for user in users:
            click.echo(
                f"{user.id:<5} {user.username:<20} {user.email:<30} "
                f"{'Yes' if user.is_admin else 'No':<7} "
                f"{'Yes' if user.is_active else 'No':<7}"
            )
        click.echo(f"\nTotal: {len(users)} user(s)")
    finally:
        db.close()


@click.command("reset-password")
@click.option("--username", prompt=True, help="Username to reset password for")
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="New password",
)
@with_appcontext
def reset_password(username: str, password: str):
    """Reset a user's password from the command line."""
    db = Session()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            click.echo(click.style(f"Error: User '{username}' not found.", fg="red"))
            return

        user.set_password(password)
        db.commit()

        click.echo(click.style(f"Password for '{username}' has been reset.", fg="green"))

    except Exception as e:
        db.rollback()
        click.echo(click.style(f"Error resetting password: {str(e)}", fg="red"))
        raise
    finally:
        db.close()


def register_cli(app):
    """Register CLI commands with the Flask application."""
    app.cli.add_command(create_admin)
    app.cli.add_command(list_users)
    app.cli.add_command(reset_password)
