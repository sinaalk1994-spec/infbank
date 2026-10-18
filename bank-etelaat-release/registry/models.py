import uuid
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q

def brand_path(instance, filename):
    return f'branding/{uuid.uuid4().hex}.png'

class Settings(models.Model):
    logo = models.FileField('لوگوی اتحادیه',upload_to=brand_path,blank=True)
    partner_logo = models.FileField('لوگوی نهاد بالادستی',upload_to=brand_path,blank=True)
    designer_logo = models.FileField('لوگوی طراح سامانه',upload_to=brand_path,blank=True)
    letterhead_image = models.FileField('تصویر کامل سربرگ PNG',upload_to=brand_path,blank=True)
    report_margin_top = models.PositiveSmallIntegerField('حاشیه بالای چاپ (میلی‌متر)',default=14)
    report_margin_right = models.PositiveSmallIntegerField('حاشیه راست چاپ (میلی‌متر)',default=14)
    report_margin_bottom = models.PositiveSmallIntegerField('حاشیه پایین چاپ (میلی‌متر)',default=14)
    report_margin_left = models.PositiveSmallIntegerField('حاشیه چپ چاپ (میلی‌متر)',default=14)
    report_date_x = models.PositiveSmallIntegerField('جای افقی تاریخ (درصد)',default=80)
    report_date_y = models.PositiveSmallIntegerField('جای عمودی تاریخ (درصد)',default=25)
    report_number_x = models.PositiveSmallIntegerField('جای افقی شماره (درصد)',default=80)
    report_number_y = models.PositiveSmallIntegerField('جای عمودی شماره (درصد)',default=50)
    report_attachment_x = models.PositiveSmallIntegerField('جای افقی پیوست (درصد)',default=80)
    report_attachment_y = models.PositiveSmallIntegerField('جای عمودی پیوست (درصد)',default=75)
    designer_name = models.CharField('نام طراح / مجموعه طراح',max_length=120,blank=True)
    report_address = models.CharField('نشانی سربرگ',max_length=250,blank=True)
    report_phone = models.CharField('تلفن سربرگ',max_length=30,blank=True)
    report_footer = models.CharField('متن پایین گزارش',max_length=250,blank=True)

    title = models.CharField(max_length=150, default='اتحادیه صنف سازندگان و فروشندگان باتری و خدمات برق تخصصی خودرو تهران')
    current_year = models.PositiveIntegerField(default=1405, validators=[MinValueValidator(1300),MaxValueValidator(1600)])
    currency = models.CharField(max_length=10, choices=[('تومان','تومان'),('ریال','ریال')], default='تومان')
    @classmethod
    def current(cls): return cls.objects.get_or_create(pk=1)[0]

class Grade(models.Model):
    name = models.CharField(max_length=80, unique=True)
    def __str__(self): return self.name

class Member(models.Model):
    name = models.CharField('نام و نام خانوادگی', max_length=150)
    national_id = models.CharField('کد ملی', max_length=10, unique=True)
    phone = models.CharField('تلفن همراه', max_length=20, blank=True)
    father_name = models.CharField('نام پدر', max_length=100, blank=True)
    birth_date = models.CharField('تاریخ تولد شمسی', max_length=10, blank=True)
    address = models.TextField('نشانی محل سکونت', blank=True)
    extra = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name

class License(models.Model):
    member = models.ForeignKey(Member,on_delete=models.PROTECT,related_name='licenses')
    number = models.CharField('شماره جواز',max_length=50,unique=True)
    business_name = models.CharField('نام واحد صنفی',max_length=150)
    activity = models.CharField('رسته فعالیت',max_length=100,blank=True)
    grade = models.ForeignKey(Grade,on_delete=models.PROTECT,verbose_name='درجه واحد')
    address = models.TextField('نشانی واحد صنفی',blank=True)
    postal_code = models.CharField('کد پستی',max_length=10,blank=True)
    issued_on = models.CharField('تاریخ صدور شمسی',max_length=10,blank=True)
    expires_on = models.CharField('تاریخ انقضا شمسی',max_length=10,blank=True)
    active = models.BooleanField('فعال',default=True)
    extra = models.JSONField('اطلاعات تکمیلی',default=dict,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.business_name

class GradeHistory(models.Model):
    license = models.ForeignKey(License,on_delete=models.PROTECT)
    grade = models.ForeignKey(Grade,on_delete=models.PROTECT)
    changed_at = models.DateTimeField(auto_now_add=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)

class Tariff(models.Model):
    year = models.PositiveIntegerField('سال', validators=[MinValueValidator(1300),MaxValueValidator(1600)])
    grade = models.ForeignKey(Grade,on_delete=models.PROTECT,verbose_name='درجه')
    amount = models.PositiveBigIntegerField('مبلغ',validators=[MinValueValidator(1)])
    class Meta:
        constraints = [models.UniqueConstraint(fields=['year','grade'],name='unique_tariff')]

class FeeHead(models.Model):
    name = models.CharField('عنوان سرفصل',max_length=100,unique=True)
    description = models.CharField('توضیح',max_length=250,blank=True)
    active = models.BooleanField('فعال',default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name

class FeeTariff(models.Model):
    year = models.PositiveIntegerField('سال',validators=[MinValueValidator(1300),MaxValueValidator(1600)])
    head = models.ForeignKey(FeeHead,on_delete=models.PROTECT,related_name='tariffs',verbose_name='سرفصل')
    grade = models.ForeignKey(Grade,on_delete=models.PROTECT,verbose_name='درجه')
    amount = models.PositiveBigIntegerField('مبلغ',validators=[MinValueValidator(1)])
    class Meta:
        constraints=[models.UniqueConstraint(fields=['year','head','grade'],name='unique_fee_tariff')]

class Due(models.Model):
    license = models.ForeignKey(License,on_delete=models.PROTECT,related_name='dues')
    fee_head = models.ForeignKey(FeeHead,on_delete=models.PROTECT,null=True,blank=True,related_name='dues',verbose_name='سرفصل دریافت')
    fee_head_label = models.CharField('عنوان سرفصل هنگام صدور',max_length=100,blank=True)
    year = models.PositiveIntegerField(null=True,blank=True,validators=[MinValueValidator(1300),MaxValueValidator(1600)])
    basis = models.CharField(max_length=150)
    amount = models.PositiveBigIntegerField(validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['year','id']
        constraints = [models.UniqueConstraint(fields=['license','year'],condition=Q(year__isnull=False,fee_head__isnull=True),name='unique_annual_due'),models.UniqueConstraint(fields=['license','year','fee_head'],condition=Q(year__isnull=False,fee_head__isnull=False),name='unique_head_due'),models.UniqueConstraint(fields=['license'],condition=Q(year__isnull=True),name='unique_opening_due'),models.CheckConstraint(condition=Q(amount__gt=0),name='positive_due')]
    @property
    def paid(self): return sum(a.amount for a in self.allocations.all() if not a.reversed_at)
    @property
    def discount(self): return sum(d.amount for d in self.discounts.all() if not d.reversed_at)
    @property
    def balance(self): return self.amount - self.paid - self.discount
    @property
    def settled(self): return self.balance == 0
    @property
    def label(self):
        if not self.year: return 'مانده پیش از سامانه'
        return f'{self.year} · {self.fee_head_label}' if self.fee_head_label else str(self.year)

class Receipt(models.Model):
    request_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    license = models.ForeignKey(License,on_delete=models.PROTECT,related_name='receipts')
    amount = models.PositiveBigIntegerField(validators=[MinValueValidator(1)])
    method = models.CharField(max_length=20,choices=[('card','کارت‌خوان'),('transfer','واریز بانکی'),('cash','نقدی')])
    reference = models.CharField(max_length=100,blank=True)
    paid_on = models.CharField(max_length=10)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.CheckConstraint(condition=Q(amount__gt=0),name='positive_receipt')]
    @property
    def available(self): return self.amount - sum(a.amount for a in self.allocations.all() if not a.reversed_at)

class Allocation(models.Model):
    receipt = models.ForeignKey(Receipt,on_delete=models.PROTECT,related_name='allocations')
    due = models.ForeignKey(Due,on_delete=models.PROTECT,related_name='allocations')
    amount = models.PositiveBigIntegerField()
    reversed_at = models.DateTimeField(null=True,blank=True)
    class Meta:
        constraints = [models.CheckConstraint(condition=Q(amount__gt=0),name='positive_allocation')]

class Discount(models.Model):
    due = models.ForeignKey(Due,on_delete=models.PROTECT,related_name='discounts')
    amount = models.PositiveBigIntegerField()
    percent = models.PositiveSmallIntegerField(null=True,blank=True)
    reason = models.TextField()
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    reversed_at = models.DateTimeField(null=True,blank=True)
    class Meta:
        constraints = [models.CheckConstraint(condition=Q(amount__gt=0),name='positive_discount')]

def document_path(instance, filename):
    return f'{instance.license_id}/{uuid.uuid4().hex}'

class Document(models.Model):
    license = models.ForeignKey(License,on_delete=models.PROTECT,related_name='documents')
    title = models.CharField('عنوان مدرک',max_length=150)
    kind = models.CharField('نوع مدرک',max_length=20,choices=[('license','جواز کسب'),('id','مدرک هویتی'),('photo','عکس صاحب جواز'),('other','سایر مدارک')])
    file = models.FileField('فایل',upload_to=document_path)
    mime = models.CharField(max_length=50)
    original_name = models.CharField(max_length=200)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

class ExtraField(models.Model):
    TARGETS=[('member','پرونده شخص'),('license','واحد صنفی / جواز')]
    TYPES=[('text','متن'),('number','عدد'),('date','تاریخ شمسی'),('choice','انتخاب از فهرست'),('boolean','بله / خیر')]
    key = models.SlugField('شناسه انگلیسی',unique=True)
    label = models.CharField('عنوان فارسی',max_length=100)
    target = models.CharField('محل نمایش',max_length=12,choices=TARGETS,default='member')
    field_type = models.CharField('نوع فیلد',max_length=12,choices=TYPES,default='text')
    choices = models.JSONField('گزینه‌ها',default=list,blank=True)
    required = models.BooleanField('الزامی',default=False)

class Audit(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,null=True)
    action = models.CharField(max_length=100)
    target = models.CharField(max_length=100)
    before = models.JSONField(default=dict)
    after = models.JSONField(default=dict)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-created_at']

class ImportMapping(models.Model):
    name = models.CharField(max_length=100,unique=True)
    mapping = models.JSONField(default=dict)

class ImportBatch(models.Model):
    token = models.UUIDField(default=uuid.uuid4,unique=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    rows = models.JSONField(default=list)
    committed_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class LoginThrottle(models.Model):
    key = models.CharField(max_length=64,unique=True)
    failures = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True)


class UserPermission(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='custom_access')
    permissions = models.JSONField('دسترسی‌های انتخاب‌شده',default=list,blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return f'دسترسی‌های {self.user.username}'
