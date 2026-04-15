from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_alter_studentprofile_id_alter_user_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="studentprofile",
            name="is_first_login",
            field=models.BooleanField(default=True),
        ),
    ]
