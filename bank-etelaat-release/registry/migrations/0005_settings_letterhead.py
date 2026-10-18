from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('registry', '0004_settings_designer_logo_settings_designer_name_and_more')]
    operations = [
        migrations.AddField('settings','letterhead_image',models.FileField(blank=True,upload_to='registry.models.brand_path',verbose_name='تصویر کامل سربرگ PNG')),
        migrations.AddField('settings','report_margin_top',models.PositiveSmallIntegerField(default=14,verbose_name='حاشیه بالای چاپ (میلی‌متر)')),
        migrations.AddField('settings','report_margin_right',models.PositiveSmallIntegerField(default=14,verbose_name='حاشیه راست چاپ (میلی‌متر)')),
        migrations.AddField('settings','report_margin_bottom',models.PositiveSmallIntegerField(default=14,verbose_name='حاشیه پایین چاپ (میلی‌متر)')),
        migrations.AddField('settings','report_margin_left',models.PositiveSmallIntegerField(default=14,verbose_name='حاشیه چپ چاپ (میلی‌متر)')),
        migrations.AddField('settings','report_date_x',models.PositiveSmallIntegerField(default=80,verbose_name='جای افقی تاریخ (درصد)')),
        migrations.AddField('settings','report_date_y',models.PositiveSmallIntegerField(default=25,verbose_name='جای عمودی تاریخ (درصد)')),
        migrations.AddField('settings','report_number_x',models.PositiveSmallIntegerField(default=80,verbose_name='جای افقی شماره (درصد)')),
        migrations.AddField('settings','report_number_y',models.PositiveSmallIntegerField(default=50,verbose_name='جای عمودی شماره (درصد)')),
        migrations.AddField('settings','report_attachment_x',models.PositiveSmallIntegerField(default=80,verbose_name='جای افقی پیوست (درصد)')),
        migrations.AddField('settings','report_attachment_y',models.PositiveSmallIntegerField(default=75,verbose_name='جای عمودی پیوست (درصد)')),
    ]
