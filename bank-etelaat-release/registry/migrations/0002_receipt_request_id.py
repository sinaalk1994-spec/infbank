import uuid
from django.db import migrations, models

def assign_ids(apps, schema_editor):
    Receipt = apps.get_model('registry', 'Receipt')
    for receipt in Receipt.objects.filter(request_id__isnull=True).iterator():
        receipt.request_id = uuid.uuid4()
        receipt.save(update_fields=['request_id'])

class Migration(migrations.Migration):
    dependencies = [('registry', '0001_initial')]
    operations = [
        migrations.AddField(model_name='receipt',name='request_id',field=models.UUIDField(null=True,unique=True,editable=False)),
        migrations.RunPython(assign_ids,migrations.RunPython.noop),
        migrations.AlterField(model_name='receipt',name='request_id',field=models.UUIDField(default=uuid.uuid4,unique=True,editable=False)),
    ]
