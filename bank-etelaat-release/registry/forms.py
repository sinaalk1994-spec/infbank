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
        for field in ExtraField.objects.filter(target='member'):
            self.fields['extra_'+field.key] = extra_form_field(field,self.instance.extra.get(field.key,'') if self.instance.pk else '')
    def clean_national_id(self):
        value = normalize(self.cleaned_data['national_id'])
        if not re.fullmatch(r'[0-9]{10}',value): raise ValidationError('کد ملی باید دقیقاً ۱۰ رقم باشد.')
        return value
    def clean_birth_date(self):
        value = self.cleaned_data['birth_date']
        return jalali_date(value) if value else ''
    def clean(self):
        cleaned=super().clean()
        for field in ExtraField.objects.filter(target='member',field_type='date'):
            name='extra_'+field.key; value=cleaned.get(name)
            if value:
                try: cleaned[name]=jalali_date(value)
                except ValidationError as error: self.add_error(name,error)
        return cleaned
    def save(self,commit=True):
        obj = super().save(commit=False)
        prior=obj.extra or {}
        obj.extra = {**prior,**{f.key:json_value(self.cleaned_data.get('extra_'+f.key,'')) for f in ExtraField.objects.filter(target='member')}}
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
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for field in ExtraField.objects.filter(target='license'):
            self.fields['extra_'+field.key]=extra_form_field(field,self.instance.extra.get(field.key,'') if self.instance.pk else '')
    def clean(self):
        cleaned=super().clean()
        for field in ExtraField.objects.filter(target='license',field_type='date'):
            name='extra_'+field.key; value=cleaned.get(name)
            if value:
                try: cleaned[name]=jalali_date(value)
                except ValidationError as error: self.add_error(name,error)
        return cleaned
    def save(self,commit=True):
        obj=super().save(commit=False); prior=obj.extra or {}
        obj.extra={**prior,**{f.key:json_value(self.cleaned_data.get('extra_'+f.key,'')) for f in ExtraField.objects.filter(target='license')}}
        if commit: obj.save()
        return obj

def extra_form_field(field,initial=''):
    common={'label':field.label,'required':field.required,'initial':initial}
    if field.field_type=='number': return forms.DecimalField(**common,max_digits=18,decimal_places=2)
    if field.field_type=='date': return forms.CharField(**common,help_text='مثلاً ۱۴۰۵/۰۱/۱۵')
    if field.field_type=='choice': return forms.ChoiceField(**common,choices=[('', 'انتخاب کنید')]+[(str(v),str(v)) for v in field.choices])
    if field.field_type=='boolean':
        common['initial']='true' if initial is True else 'false' if initial is False else ''
        return forms.TypedChoiceField(**common,choices=[('', 'انتخاب کنید'),('true','بله'),('false','خیر')],coerce=lambda v: v=='true',empty_value=None)
    return forms.CharField(**common,widget=forms.Textarea(attrs={'rows':2}) if field.field_type=='text' else forms.TextInput())

def json_value(value):
    from decimal import Decimal
    return str(value) if isinstance(value,Decimal) else value

class ExtraFieldForm(forms.Form):
    key=forms.SlugField(label='شناسه انگلیسی',max_length=50)
    label=forms.CharField(label='عنوان فارسی',max_length=100)
    target=forms.ChoiceField(label='محل نمایش',choices=ExtraField.TARGETS)
    field_type=forms.ChoiceField(label='نوع فیلد',choices=ExtraField.TYPES)
    choices=forms.CharField(label='گزینه‌ها (هر گزینه در یک خط)',required=False,widget=forms.Textarea(attrs={'rows':3}))
    required=forms.BooleanField(label='الزامی',required=False)
    def clean_key(self):
        value=self.cleaned_data['key'].lower()
        if ExtraField.objects.filter(key=value).exists(): raise ValidationError('این شناسه قبلاً استفاده شده است.')
        return value
    def clean(self):
        cleaned=super().clean()
        values=[v.strip() for v in cleaned.get('choices','').splitlines() if v.strip()]
        if cleaned.get('field_type')=='choice' and not values: self.add_error('choices','برای فیلد انتخابی دست‌کم یک گزینه بنویسید.')
        if len(values)>100 or any(len(v)>100 for v in values): self.add_error('choices','حداکثر ۱۰۰ گزینه و هر گزینه حداکثر ۱۰۰ نویسه باشد.')
        cleaned['choices_list']=values
        return cleaned

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
        fields=['logo','designer_logo','designer_name','partner_logo','letterhead_image','report_address','report_phone','report_footer',
                'report_margin_top','report_margin_right','report_margin_bottom','report_margin_left',
                'report_date_x','report_date_y','report_number_x','report_number_y','report_attachment_x','report_attachment_y']
        widgets={name:forms.FileInput(attrs={'accept':'image/png,image/jpeg,image/webp'}) for name in ['logo','partner_logo','designer_logo']}
        widgets.update({'letterhead_image':forms.FileInput(attrs={'accept':'image/png'})})
        for _name in ['report_margin_top','report_margin_right','report_margin_bottom','report_margin_left']:
            widgets[_name]=forms.NumberInput(attrs={'min':0,'max':40,'step':1})
        for _name in ['report_date_x','report_date_y','report_number_x','report_number_y','report_attachment_x','report_attachment_y']:
            widgets[_name]=forms.NumberInput(attrs={'min':0,'max':100,'step':1})
    def clean(self):
        cleaned=super().clean()
        for name in ['report_margin_top','report_margin_right','report_margin_bottom','report_margin_left']:
            value=cleaned.get(name)
            if value is not None and value>40: self.add_error(name,'حاشیه باید بین صفر تا ۴۰ میلی‌متر باشد.')
        for name in ['report_date_x','report_date_y','report_number_x','report_number_y','report_attachment_x','report_attachment_y']:
            value=cleaned.get(name)
            if value is not None and value>100: self.add_error(name,'جایگاه باید بین صفر تا ۱۰۰ درصد باشد.')
        upload=self.files.get('letterhead_image')
        if upload is not None:
            from django.core.files.base import ContentFile
            if upload.size>8*1024*1024:
                self.add_error('letterhead_image','حداکثر حجم سربرگ ۸ مگابایت است.')
            else:
                try:
                    picture=Image.open(upload)
                    if picture.format!='PNG' or picture.width*picture.height>25_000_000:
                        self.add_error('letterhead_image','فقط PNG با حداکثر ۲۵ میلیون پیکسل پذیرفته می‌شود.')
                    else:
                        picture.load(); data=BytesIO(); picture.convert('RGBA').save(data,format='PNG')
                        cleaned['letterhead_image']=ContentFile(data.getvalue(),name='letterhead.png')
                except (UnidentifiedImageError,OSError,Image.DecompressionBombError):
                    self.add_error('letterhead_image','فایل PNG معتبر نیست.')
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
