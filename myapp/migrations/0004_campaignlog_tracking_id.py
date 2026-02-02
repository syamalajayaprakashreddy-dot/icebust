from django.db import migrations, models
import uuid


def generate_tracking_ids(apps, schema_editor):
    CampaignLog = apps.get_model('myapp', 'CampaignLog')
    for log in CampaignLog.objects.all():
        if not log.tracking_id:
            log.tracking_id = uuid.uuid4()
            log.save(update_fields=["tracking_id"])


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0003_auditlog'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaignlog',
            name='tracking_id',
            field=models.UUIDField(
                null=True,   # TEMPORARY
                editable=False,
                db_index=True
            ),
        ),
        migrations.RunPython(generate_tracking_ids),
        migrations.AlterField(
            model_name='campaignlog',
            name='tracking_id',
            field=models.UUIDField(
                default=uuid.uuid4,
                unique=True,
                editable=False,
                db_index=True
            ),
        ),
    ]
