"""Celery application configuration and initialization."""

from celery import Celery

from app.config import Config


def make_celery(app=None):
    """Create and configure Celery application.

    Args:
        app: Optional Flask application instance

    Returns:
        Configured Celery application
    """
    celery = Celery(
        "homelab_manager",
        broker=Config.CELERY_BROKER_URL,
        backend=Config.CELERY_RESULT_BACKEND,
        include=["app.tasks.automation"],
    )

    celery.conf.update(
        task_serializer=Config.CELERY_TASK_SERIALIZER,
        result_serializer=Config.CELERY_RESULT_SERIALIZER,
        accept_content=Config.CELERY_ACCEPT_CONTENT,
        timezone=Config.CELERY_TIMEZONE,
        task_track_started=Config.CELERY_TASK_TRACK_STARTED,
        task_time_limit=Config.CELERY_TASK_TIME_LIMIT,
        # Retry settings
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        # Result settings
        result_expires=3600,  # Results expire after 1 hour
    )

    if app:
        celery.conf.update(app.config)

        class ContextTask(celery.Task):
            """Task that runs within Flask application context."""

            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery.Task = ContextTask

    return celery


# Create the celery instance for use by workers
celery_app = make_celery()
