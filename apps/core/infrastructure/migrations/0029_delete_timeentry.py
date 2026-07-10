from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_alter_registrationrequest_expires_at_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='TimeEntry',
        ),
    ]
