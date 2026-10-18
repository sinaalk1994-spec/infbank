from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('registry', '0005_settings_letterhead')]
    operations = [
        migrations.AddField('license','extra',models.JSONField(blank=True,default=dict,verbose_name='اطلاعات تکمیلی')),
        migrations.AddField('extrafield','target',models.CharField(choices=[('member','پرونده شخص'),('license','واحد صنفی / جواز')],default='member',max_length=12,verbose_name='محل نمایش')),
        migrations.AddField('extrafield','field_type',models.CharField(choices=[('text','متن'),('number','عدد'),('date','تاریخ شمسی'),('choice','انتخاب از فهرست'),('boolean','بله / خیر')],default='text',max_length=12,verbose_name='نوع فیلد')),
        migrations.AddField('extrafield','choices',models.JSONField(blank=True,default=list,verbose_name='گزینه‌ها')),
    ]
