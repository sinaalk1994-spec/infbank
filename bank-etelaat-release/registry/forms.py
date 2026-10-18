import re
from io import BytesIO
from PIL import Image, UnidentifiedImageError
from django import forms
from django.core.exceptions import ValidationError
from .models import *

DIGITS = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩','01234567890123456789')
def normalize(value): return str(value or '').translate(DIGITS).strip()
def jalali_date(value):
    value = normalize(value).replace('-','/')
    if not re.fullmatch(r'1[3-5]\d{2}/(0[1-9]|1[0-2])/(0[1-9]|[12]\d|3[01])',value):
        raise ValidationError('تاریخ را به صورت ۱۴۰۵/۰۱/۱۵ وارد کنید.')
    y,m,d = map(int,value.split('/'))
    if m > 6 and d > 30: raise ValidationError('روز این ماه معتبر نیست.')
    if m == 12 and d == 30:
        # Persian arithmetic calendar leap calculation.
        epyear = 474 + ((y - 474) % 2820)
        if ((epyear + 38) * 682) % 2816 >= 682:
            raise ValidationError('اسفند این سال ۲۹ روز دارد.')
    return value

class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['name','national_id','phone','father_name','birth_date','address']
        widgets = {'address':forms.Textarea(attrs={'rows':2})}
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for field in ExtraField.objects.all():
            self.fields['extra_'+field.key] = forms.CharField(label=field.label,required=field.required,initial=self.instance.extra.get(field.key,'') if self.instance.pk else '')
    def clean_national_id(self):
        value = normalize(self.cleaned_data['national_id'])
        if not re.fullmatch(r'[0-9]{10}',value): raise ValidationError('کد ملی باید دقیقاً ۱۰ رقم باشد.')
        return value
    def clean_birth_date(self):
        value = self.cleaned_data['birth_date']
        return jalali_date(value) if value else ''
    def save(self,commit=True):
        obj = super().save(commit=False)
        obj.extra = {f.key:self.cleaned_data.get('extra_'+f.key,'') for f in ExtraField.objects.all()}
        if commit: obj.save()
        return obj

class LicenseForm(forms.ModelForm):
    class Meta:
        model = License
        fields = ['number','business_name','activity','grade','address','postal_code','issued_on','expires_on','active']
        widgets = {'address':forms.Textarea(attrs={'rows':2})}
    def clean_number(self): return normalize(self.cleaned_data['number'])
    def clean_issued_on(self):
        v=self.cleaned_data['issued_on']; return jalali_date(v) if v else ''
    def clean_expires_on(self):
        v=self.cleaned_data['expires_on']; return jalali_date(v) if v else ''
    def clean_postal_code(self):
        v=normalize(self.cleaned_data['postal_code'])
        if v and not re.fullmatch(r'[0-9]{10}',v): raise ValidationError('کد پستی باید ۱۰ رقم باشد.')
        return v

class PaymentForm(forms.Form):
    request_id = forms.UUIDField(widget=forms.HiddenInput, initial=uuid.uuid4)
    amount = forms.IntegerField(label='مبلغ دریافت',min_value=1,max_value=10**12)
    method = forms.ChoiceField(label='روش پرداخت',choices=Receipt._meta.get_field('method').choices)
    reference = forms.CharField(label='شماره رسید / پیگیری',max_length=100,required=False)
    paid_on = forms.CharField(label='تاریخ پرداخت شمسی',validators=[jalali_date],help_text='مثلاً ۱۴۰۵/۰۱/۱۵')
    due = forms.ChoiceField(label='تخصیص پرداخت',required=False)
    def __init__(self,license,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['due'].choices = [('', 'خودکار؛ از قدیمی‌ترین بدهی')] + [(d.pk,d.label) for d in license.dues.all() if d.balance > 0]

class DebtForm(forms.Form):
    year = forms.IntegerField(label='سال بدهی',min_value=1300,max_value=1600,required=False,help_text='برای مانده تجمیعی نامشخص، خالی بگذارید.')
    amount = forms.IntegerField(label='مانده واقعی بدهی',min_value=1,max_value=10**12)
    basis = forms.CharField(label='شرح و تاریخ مبنای مانده',max_length=150)

class DocumentForm(forms.ModelForm):
    class Meta:
        model=Document
        fields=['title','kind','file']
    def clean_file(self):
        f = self.cleaned_data['file']
        if f.size > 10*1024*1024: raise ValidationError('حداکثر حجم فایل ۱۰ مگابایت است.')
        head=f.read(8); f.seek(0)
        if head.startswith(b'%PDF-'):
            self.mime='application/pdf'
        else:
            try:
                img=Image.open(f)
                if img.format not in ['JPEG','PNG','WEBP']: raise ValidationError('فقط PDF، JPG، PNG و WebP مجاز است.')
                if img.width*img.height > 25_000_000: raise ValidationError('ابعاد تصویر بیش از حد مجاز است.')
                self.mime=Image.MIME[img.format]; img.verify()
            except (UnidentifiedImageError,OSError,Image.DecompressionBombError):
                raise ValidationError('فایل تصویر معتبر نیست.')
            finally: f.seek(0)
        if self.cleaned_data.get('kind') == 'photo' and self.mime == 'application/pdf':
            raise ValidationError('برای عکس صاحب جواز، تصویر انتخاب کنید.')
        return f

class BrandingForm(forms.ModelForm):
    class Meta:
        model=Settings
        fields=['logo','designer_logo','designer_name','partner_logo','report_address','report_phone','report_footer']
        widgets={name:forms.FileInput(attrs={'accept':'image/png,image/jpeg,image/webp'}) for name in ['logo','partner_logo','designer_logo']}
    def clean(self):
        cleaned=super().clean()
        from django.core.files.base import ContentFile
        for name in ['logo','partner_logo','designer_logo']:
            upload=self.files.get(name)
            if upload is None: continue
            if upload.size>2*1024*1024:
                self.add_error(name,'حداکثر حجم لوگو ۲ مگابایت است.'); continue
            try:
                picture=Image.open(upload)
                if picture.format not in ['PNG','JPEG','WEBP'] or picture.width*picture.height>4_000_000:
                    self.add_error(name,'تصویر PNG، JPEG یا WebP با حداکثر ۴ میلیون پیکسل انتخاب کنید.'); continue
                picture.load(); picture=picture.convert('RGBA'); picture.thumbnail((800,800))
                data=BytesIO(); picture.save(data,format='PNG')
                cleaned[name]=ContentFile(data.getvalue(),name='logo.png')
            except (UnidentifiedImageError,OSError,Image.DecompressionBombError):
                self.add_error(name,'فایل تصویر معتبر نیست.')
        return cleaned
