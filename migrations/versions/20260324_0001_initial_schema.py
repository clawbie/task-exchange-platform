"""Initial schema

Revision ID: 20260324_0001
Revises:
Create Date: 2026-03-24 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260324_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "actors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("reasoning_tier", sa.String(length=32), nullable=False),
        sa.Column("browser_capability", sa.String(length=32), nullable=False),
        sa.Column("compute_capacity", sa.String(length=32), nullable=False),
        sa.Column("speed_tier", sa.String(length=32), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_actors")),
    )
    op.create_index(op.f("ix_actors_name"), "actors", ["name"], unique=False)
    op.create_index(op.f("ix_actors_type"), "actors", ["type"], unique=False)

    op.create_table(
        "tasks",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_by_actor_id", sa.Integer(), nullable=True),
        sa.Column("assigned_to_actor_id", sa.Integer(), nullable=True),
        sa.Column("executor_constraints", sa.String(length=32), nullable=False),
        sa.Column("reasoning_tier", sa.String(length=32), nullable=False),
        sa.Column("browser_requirement", sa.String(length=32), nullable=False),
        sa.Column("compute_requirement", sa.String(length=32), nullable=False),
        sa.Column("speed_priority", sa.String(length=32), nullable=False),
        sa.Column("deliverables", sa.JSON(), nullable=False),
        sa.Column("acceptance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["assigned_to_actor_id"],
            ["actors.id"],
            name=op.f("fk_tasks_assigned_to_actor_id_actors"),
        ),
        sa.ForeignKeyConstraint(
            ["created_by_actor_id"],
            ["actors.id"],
            name=op.f("fk_tasks_created_by_actor_id_actors"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tasks")),
    )
    op.create_index(op.f("ix_tasks_status"), "tasks", ["status"], unique=False)

    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("key_prefix", sa.String(length=32), nullable=False),
        sa.Column("key_hash", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["actor_id"], ["actors.id"], name=op.f("fk_api_keys_actor_id_actors")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_api_keys")),
        sa.UniqueConstraint("key_hash", name=op.f("uq_api_keys_key_hash")),
    )
    op.create_index(op.f("ix_api_keys_actor_id"), "api_keys", ["actor_id"], unique=False)
    op.create_index(op.f("ix_api_keys_key_prefix"), "api_keys", ["key_prefix"], unique=False)

    op.create_table(
        "task_packages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("manifest_json", sa.JSON(), nullable=False),
        sa.Column("bundle_path", sa.String(length=500), nullable=True),
        sa.Column("sha256", sa.String(length=128), nullable=True),
        sa.Column("created_by_actor_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_actor_id"], ["actors.id"], name=op.f("fk_task_packages_created_by_actor_id_actors")),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], name=op.f("fk_task_packages_task_id_tasks")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_task_packages")),
    )
    op.create_index(op.f("ix_task_packages_task_id"), "task_packages", ["task_id"], unique=False)

    op.create_table(
        "task_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.String(length=32), nullable=False),
        sa.Column("executor_actor_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("progress_percent", sa.Integer(), nullable=False),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["executor_actor_id"], ["actors.id"], name=op.f("fk_task_runs_executor_actor_id_actors")),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], name=op.f("fk_task_runs_task_id_tasks")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_task_runs")),
    )
    op.create_index(op.f("ix_task_runs_task_id"), "task_runs", ["task_id"], unique=False)

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.String(length=32), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=True),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["actors.id"], name=op.f("fk_events_actor_id_actors")),
        sa.ForeignKeyConstraint(["run_id"], ["task_runs.id"], name=op.f("fk_events_run_id_task_runs")),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], name=op.f("fk_events_task_id_tasks")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_events")),
    )
    op.create_index(op.f("ix_events_event_type"), "events", ["event_type"], unique=False)
    op.create_index(op.f("ix_events_task_id"), "events", ["task_id"], unique=False)

    op.create_table(
        "submissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_run_id", sa.Integer(), nullable=False),
        sa.Column("submitted_by_actor_id", sa.Integer(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("result_json", sa.JSON(), nullable=False),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("reviewed_by_actor_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["reviewed_by_actor_id"], ["actors.id"], name=op.f("fk_submissions_reviewed_by_actor_id_actors")),
        sa.ForeignKeyConstraint(["submitted_by_actor_id"], ["actors.id"], name=op.f("fk_submissions_submitted_by_actor_id_actors")),
        sa.ForeignKeyConstraint(["task_run_id"], ["task_runs.id"], name=op.f("fk_submissions_task_run_id_task_runs")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_submissions")),
    )
    op.create_index(op.f("ix_submissions_task_run_id"), "submissions", ["task_run_id"], unique=False)

    op.create_table(
        "files",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.String(length=32), nullable=True),
        sa.Column("run_id", sa.Integer(), nullable=True),
        sa.Column("submission_id", sa.Integer(), nullable=True),
        sa.Column("uploaded_by_actor_id", sa.Integer(), nullable=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("original_name", sa.String(length=260), nullable=False),
        sa.Column("stored_name", sa.String(length=260), nullable=False),
        sa.Column("mime_type", sa.String(length=120), nullable=True),
        sa.Column("extension", sa.String(length=32), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("sha256", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["task_runs.id"], name=op.f("fk_files_run_id_task_runs")),
        sa.ForeignKeyConstraint(["submission_id"], ["submissions.id"], name=op.f("fk_files_submission_id_submissions")),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], name=op.f("fk_files_task_id_tasks")),
        sa.ForeignKeyConstraint(["uploaded_by_actor_id"], ["actors.id"], name=op.f("fk_files_uploaded_by_actor_id_actors")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_files")),
    )
    op.create_index(op.f("ix_files_task_id"), "files", ["task_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_files_task_id"), table_name="files")
    op.drop_table("files")
    op.drop_index(op.f("ix_submissions_task_run_id"), table_name="submissions")
    op.drop_table("submissions")
    op.drop_index(op.f("ix_events_task_id"), table_name="events")
    op.drop_index(op.f("ix_events_event_type"), table_name="events")
    op.drop_table("events")
    op.drop_index(op.f("ix_task_runs_task_id"), table_name="task_runs")
    op.drop_table("task_runs")
    op.drop_index(op.f("ix_task_packages_task_id"), table_name="task_packages")
    op.drop_table("task_packages")
    op.drop_index(op.f("ix_api_keys_key_prefix"), table_name="api_keys")
    op.drop_index(op.f("ix_api_keys_actor_id"), table_name="api_keys")
    op.drop_table("api_keys")
    op.drop_index(op.f("ix_tasks_status"), table_name="tasks")
    op.drop_table("tasks")
    op.drop_index(op.f("ix_actors_type"), table_name="actors")
    op.drop_index(op.f("ix_actors_name"), table_name="actors")
    op.drop_table("actors")
