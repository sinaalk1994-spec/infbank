from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from registry.models import *
from registry.services import receive, discount

class Command(BaseCommand):
    help='Create fictitious demonstration records in a separate demo data directory only.'
    @transaction.atomic
    def handle(self,*args,**options):
        if settings.RUNTIME.name != 'demo': raise CommandError('Use APP_DATA_DIR=/path/to/demo; never seed the operational database.')
        if Member.objects.exists(): raise CommandError('Demo database already has members; no records changed.')
        user,created=User.objects.get_or_create(username='demo-review',defaults={'is_superuser':True,'is_staff':True,'first_name':'مدیر آزمایشی'})
        if created: user.set_unusable_password(); user.save()
        app=Settings.current(); app.title='اتحادیه اصناف · نسخه نمایشی'; app.current_year=1405; app.save()
        grades=[Grade.objects.get_or_create(name='درجه '+name)[0] for name in ['یک','دو','سه']]
        names=['علی محمدی','مریم رضایی','حسین احمدی','سارا کریمی','رضا موسوی','فاطمه حسینی','امیر صالحی','نرگس اکبری','مهدی رحیمی','الهام نادری','محمد مرادی','سمیه رستمی']
        shops=['فروشگاه سپهر','گالری آوید','پوشاک هیراد','خانه هنر آبان','کالای خانه مهر','فروشگاه ترنج','صنایع چوب چنار','گالری نارون','بازرگانی آریا','خانه آوا','فروشگاه بهار','گالری نیلوفر']
        for i,grade in enumerate(grades): Tariff.objects.create(grade=grade,year=1405,amount=6000000-i*1000000)
        for i,(name,shop) in enumerate(zip(names,shops)):
            member=Member.objects.create(name=name,national_id=f'000000{i:04d}',phone=f'0900000{i:04d}',father_name='آزمایشی',address='نشانی ساختگی برای نمایش سامانه')
            lic=License.objects.create(member=member,number=f'1405{i+1:05d}',business_name=shop,grade=grades[i%3],activity='خرده‌فروشی',issued_on='1403/02/15',expires_on='1408/02/15',address='خیابان نمونه، پلاک آزمایشی')
            GradeHistory.objects.create(license=lic,grade=lic.grade,actor=user)
            past=Due.objects.create(license=lic,year=1404,amount=3500000,basis='مانده نمونه سال ۱۴۰۴')
            current=Due.objects.create(license=lic,year=1405,amount=6000000-i%3*1000000,basis='تعرفه ۱۴۰۵ · '+lic.grade.name)
            if i%4 != 0: receive(user,lic,3500000,'transfer',f'DEMO-{i}','1405/01/10',due_id=past.pk)
            if i%3 == 0:
                discount(user,current,0,'تخفیف ساختگی برای نمایش',percent=10)
                receive(user,lic,current.balance,'card',f'DEMO-C-{i}','1405/02/18',due_id=current.pk)
            elif i%3 == 1: receive(user,lic,2000000,'card',f'DEMO-C-{i}','1405/03/02',due_id=current.pk)
        self.stdout.write(self.style.SUCCESS('12 fictitious members created. Demo user has no usable password.'))
