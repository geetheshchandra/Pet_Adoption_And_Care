# Generated by Django 5.1.1 on 2024-11-03 19:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pet_adoption_and_care', '0006_alter_adoptionrequest_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='availablepet',
            name='status',
            field=models.CharField(default='Available', max_length=10),
        ),
    ]
