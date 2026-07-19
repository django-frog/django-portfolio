# Hand-edited to be idempotent across partial Postgres state from prior
# failed runs, and to safely backfill the new Skill.slug unique column.
#
# Execution order:
#   0.  Self-heal: drop any leftover indexes/columns/backup tables from a
#       previous half-applied run.
#   1.  Snapshot (skill_id, domain_id) pairs into core_skill_domain_backup.
#   2.  Apply auto-generated schema changes (drop FK, add M2M, add Skill.slug
#       WITH db_index=False and WITHOUT unique=True so we can backfill first).
#   3.  Populate slug from name (with -N collision suffix) for every row.
#   4.  Add the unique constraint on slug (which cleanly builds the index once).
#   5.  Restore the M2M relations from the snapshot and drop the backup.

from django.db import migrations, models
from django.utils.text import slugify


def _drop_index_if_exists(schema_editor, index_name: str) -> None:
    schema_editor.execute(
        "DROP INDEX IF EXISTS %s CASCADE" % index_name
    )


def _drop_column_if_exists(
    schema_editor, table: str, column: str
) -> None:
    schema_editor.execute(
        "ALTER TABLE %s DROP COLUMN IF EXISTS %s CASCADE" % (table, column)
    )


def _drop_table_if_exists(schema_editor, table: str) -> None:
    schema_editor.execute("DROP TABLE IF EXISTS %s CASCADE" % table)


def _drop_skill_slug_indexes(schema_editor) -> None:
    """
    Drop every leftover index or constraint on core_skill.slug from a prior run.
    Uses CASCADE to clear ghost entries in pg_class or pg_constraint.
    """
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'core_skill'
              AND indexname LIKE 'core_skill_slug%'
            """
        )
        for (indexname,) in cursor.fetchall():
            _drop_index_if_exists(schema_editor, indexname)

        cursor.execute(
            """
            SELECT relname FROM pg_class
            WHERE relname LIKE 'core_skill_slug%'
              AND relkind = 'i'
            """
        )
        for (relname,) in cursor.fetchall():
            _drop_index_if_exists(schema_editor, relname)

        cursor.execute(
            """
            SELECT conname FROM pg_constraint
            WHERE conname LIKE 'core_skill_slug%'
            """
        )
        for (conname,) in cursor.fetchall():
            schema_editor.execute(
                "ALTER TABLE core_skill DROP CONSTRAINT IF EXISTS %s CASCADE" % conname
            )


def pre_cleanup(apps, schema_editor):
    """Make this migration safe to re-run after a partial failure."""
    _drop_skill_slug_indexes(schema_editor)
    _drop_table_if_exists(schema_editor, "core_skill_domain_backup")
    _drop_column_if_exists(schema_editor, "core_skill", "slug")


def snapshot_skill_domains(apps, schema_editor):
    """Stash the existing skill↔domain pairs before the FK is dropped."""
    Skill = apps.get_model("core", "Skill")
    schema_editor.execute(
        """
        CREATE TABLE IF NOT EXISTS core_skill_domain_backup (
            skill_pk   INTEGER NOT NULL,
            domain_pk  INTEGER NOT NULL
        )
        """
    )
    schema_editor.execute("DELETE FROM core_skill_domain_backup")
    for skill in Skill.objects.exclude(domain__isnull=True):
        schema_editor.execute(
            "INSERT INTO core_skill_domain_backup (skill_pk, domain_pk) VALUES (%s, %s)",
            [skill.pk, skill.domain_id],
        )


def populate_skill_slugs(apps, schema_editor):
    """Backfill Skill.slug from Skill.name, ensuring uniqueness across rows."""
    Skill = apps.get_model("core", "Skill")
    seen: set[str] = set()
    for skill in Skill.objects.order_by("pk"):
        base: str = slugify(skill.name) or f"skill-{skill.pk}"
        candidate: str = base
        counter: int = 1
        while candidate in seen:
            counter += 1
            candidate = f"{base}-{counter}"
        seen.add(candidate)
        skill.slug = candidate
        skill.save(update_fields=["slug"])


def restore_skill_domains(apps, schema_editor):
    """Re-attach the saved pairs through the new M2M after the schema flip."""
    Skill = apps.get_model("core", "Skill")
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT skill_pk, domain_pk FROM core_skill_domain_backup")
        rows = cursor.fetchall()
    for skill_pk, domain_pk in rows:
        try:
            skill = Skill.objects.get(pk=skill_pk)
        except Skill.DoesNotExist:
            continue
        skill.domains.add(domain_pk)
    schema_editor.execute("DROP TABLE IF EXISTS core_skill_domain_backup")


def noop(apps, schema_editor):
    """Reverse helpers do nothing — the backup table is dropped in forward."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_alter_skill_proficiency'),
    ]

    operations = [
        # 0) Self-heal leftover state from any prior failed attempt.
        migrations.RunPython(pre_cleanup, noop),

        # 1) Snapshot the existing FK mapping before the column is dropped.
        migrations.RunPython(snapshot_skill_domains, noop),

        # 2) Schema changes. CRITICAL FIX: Explicitly set db_index=False here
        #    so Django does NOT queue a _like index creation in the deferred buffer!
        migrations.AlterModelOptions(
            name='skill',
            options={'ordering': ['-proficiency', 'name'], 'verbose_name': 'Skill', 'verbose_name_plural': 'Skills'},
        ),
        migrations.AlterModelOptions(
            name='technicaldomain',
            options={'ordering': ['order', 'name'], 'verbose_name': 'Technical Domain', 'verbose_name_plural': 'Technical Domains'},
        ),
        migrations.RemoveIndex(
            model_name='skill',
            name='core_skill_domain__9fdcdd_idx',
        ),
        migrations.RemoveIndex(
            model_name='skill',
            name='core_skill_is_feat_3312d8_idx',
        ),
        migrations.RemoveField(
            model_name='skill',
            name='domain',
        ),
        migrations.RemoveField(
            model_name='skill',
            name='is_featured',
        ),
        migrations.RemoveField(
            model_name='skill',
            name='sort_order',
        ),
        migrations.RemoveField(
            model_name='technicaldomain',
            name='sort_order',
        ),
        migrations.AddField(
            model_name='skill',
            name='slug',
            # db_index=False prevents duplicate CREATE INDEX queuing before backfill
            field=models.SlugField(blank=True, db_index=False, max_length=100, verbose_name='URL Slug'),
        ),
        migrations.AddField(
            model_name='technicaldomain',
            name='order',
            field=models.PositiveSmallIntegerField(db_index=True, default=0, help_text='Lower numbers appear first', verbose_name='Display Order'),
        ),
        migrations.AddField(
            model_name='technicaldomain',
            name='skills',
            field=models.ManyToManyField(blank=True, help_text='Select all skills that apply to this technical domain.', related_name='domains', to='core.skill', verbose_name='Skills'),
        ),
        migrations.AlterField(
            model_name='skill',
            name='name',
            field=models.CharField(max_length=100, unique=True, verbose_name='Skill Name'),
        ),
        migrations.AlterField(
            model_name='technicaldomain',
            name='name',
            field=models.CharField(max_length=100, unique=True, verbose_name='Domain Name'),
        ),
        migrations.AddIndex(
            model_name='skill',
            index=models.Index(fields=['-proficiency'], name='core_skill_profici_83b438_idx'),
        ),

        # 3) Backfill slug from name (with collision suffixes).
        migrations.RunPython(populate_skill_slugs, noop),

        # SAFETY VALVE: Force drop any buffered pattern-matching index right before AlterField
        migrations.RunSQL(
            sql="DROP INDEX IF EXISTS core_skill_slug_188a7af8_like CASCADE;",
            reverse_sql=migrations.RunSQL.noop
        ),

        # 4) Now safe: enforce uniqueness on slug (creates the index cleanly once).
        migrations.AlterField(
            model_name='skill',
            name='slug',
            field=models.SlugField(blank=True, max_length=100, unique=True, verbose_name='URL Slug'),
        ),

        # 5) Restore the M2M relations and drop the backup table.
        migrations.RunPython(restore_skill_domains, noop),
    ]
