from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0017_appraisalscore_verified_grade"),
    ]

    operations = [
        migrations.AddField(
            model_name="facultyprofile",
            name="profile_image",
            field=models.ImageField(blank=True, null=True, upload_to="profile_images/"),
        ),
        migrations.AddField(
            model_name="hodprofile",
            name="profile_image",
            field=models.ImageField(blank=True, null=True, upload_to="profile_images/"),
        ),
    ]
