import hashlib
from datetime import timedelta
from django.contrib.auth import authenticate
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from .models import *

ROLE_LABELS = {'chair':'رئیس اتحادیه','accountant':'حسابدار','clerk':'کارشناس پرونده','viewer':'مشاهده‌گر'}

def allowed(user, capability):
    if not user.is_authenticated or not user.is_active: return False
    if user.is_superuser: return True
    role_map = {'edit':{'clerk','chair','accountant'},'finance':{'accountant','chair'},'discount':{'chair'},'export':{'chair','accountant'},'audit':{'chair'},'admin':set()}
    return user.groups.filter(name__in=role_map.get(capability,set())).exists()

def require(user, capability):
    if not allowed(user,capability): raise PermissionDenied('دسترسی لازم برای این عملیات را ندارید.')

def audit(user, action, target, before=None, after=None, reason=''):
    Audit.objects.create(actor=user,action=action,target=str(target),before=before or {},after=after or {},reason=reason)

def checked_auth(request, username, password, scope='login'):
    key = hashlib.sha256(f'{scope}:{username.strip().lower()}'.encode()).hexdigest()
    with transaction.atomic():
        throttle, _ = LoginThrottle.objects.get_or_create(key=key)
        if throttle.locked_until and throttle.locked_until > timezone.now():
            raise ValidationError('تلاش‌های ناموفق زیاد است. ۱۵ دقیقه دیگر تلاش کنید.')
        user = authenticate(request,username=username,password=password)
        if user is None:
            throttle.failures += 1
            if throttle.failures >= 5:
                throttle.locked_until = timezone.now() + timedelta(minutes=15)
                throttle.failures = 0
            throttle.save()
        else:
            throttle.delete()
    if user is None: raise ValidationError('نام کاربری یا رمز عبور صحیح نیست.')
    return user

@transaction.atomic
def bill_year(user, year):
    require(user,'finance')
    licenses = list(License.objects.filter(active=True).select_related('grade'))
    tariffs = {t.grade_id:t for t in Tariff.objects.filter(year=year)}
    missing = [l.grade.name for l in licenses if l.grade_id not in tariffs]
    if missing: raise ValidationError('تعرفه این درجه‌ها تعریف نشده: ' + '، '.join(sorted(set(missing))))
    count = 0
    for lic in licenses:
        t = tariffs[lic.grade_id]
        _, created = Due.objects.get_or_create(license=lic,year=year,defaults={'amount':t.amount,'basis':f'تعرفه {year} · {lic.grade.name}'})
        count += created
    audit(user,'صدور حق عضویت',year,after={'count':count})
    return count

@transaction.atomic
def receive(user, license, amount, method, reference, paid_on, due_id=None, receipt=None, request_id=None):
    require(user,'finance')
    License.objects.select_for_update().get(pk=license.pk)
    if receipt is None and request_id:
        existing = Receipt.objects.filter(request_id=request_id).first()
        if existing:
            if existing.license_id != license.pk or existing.amount != amount:
                raise ValidationError('شناسه درخواست قبلاً برای پرداخت دیگری استفاده شده است.')
            return existing
    if receipt is None:
        if amount <= 0: raise ValidationError('مبلغ باید مثبت باشد.')
        receipt = Receipt.objects.create(license=license,amount=amount,method=method,reference=reference,paid_on=paid_on,actor=user,**({'request_id':request_id} if request_id else {}))
    elif receipt.license_id != license.pk:
        raise ValidationError('رسید به این پرونده تعلق ندارد.')
    remaining = receipt.available
    dues = license.dues.prefetch_related('allocations','discounts').order_by('year','id')
    if due_id:
        dues = dues.filter(pk=due_id)
        if not dues.exists(): raise ValidationError('بدهی انتخاب‌شده معتبر نیست.')
    allocated = []
    for due in dues:
        part = min(max(due.balance,0),remaining)
        if part:
            Allocation.objects.create(receipt=receipt,due=due,amount=part)
            allocated.append({'due':due.pk,'amount':part})
            remaining -= part
    audit(user,'ثبت / تخصیص دریافت',f'license:{license.pk}',after={'receipt':receipt.pk,'amount':receipt.amount,'allocations':allocated,'credit':remaining})
    return receipt

@transaction.atomic
def discount(user, due, amount, reason, percent=None):
    require(user,'discount')
    due = Due.objects.select_for_update().get(pk=due.pk)
    if percent is not None:
        if not 1 <= percent <= 100: raise ValidationError('درصد باید بین ۱ تا ۱۰۰ باشد.')
        amount = due.amount * percent // 100
    if amount <= 0 or amount > due.balance: raise ValidationError('تخفیف باید مثبت و حداکثر برابر مانده بدهی باشد.')
    if not reason.strip(): raise ValidationError('دلیل تخفیف الزامی است.')
    obj = Discount.objects.create(due=due,amount=amount,percent=percent,reason=reason,approved_by=user)
    audit(user,'تأیید تخفیف',f'license:{due.license_id}',after={'discount':obj.pk,'due':due.pk,'amount':amount,'percent':percent},reason=reason)

@transaction.atomic
def reopen(actor, approver, due, reason):
    require(actor,'finance')
    if not approver.is_superuser or not approver.is_active: raise PermissionDenied('تأیید مدیر سامانه لازم است.')
    due = Due.objects.select_for_update().get(pk=due.pk)
    if not due.settled: raise ValidationError('این سال در وضعیت تسویه نیست.')
    if len(reason.strip()) < 5: raise ValidationError('دلیل اصلاح را کامل وارد کنید.')
    before = {'paid':due.paid,'discount':due.discount,'balance':due.balance}
    now = timezone.now()
    allocation_ids = list(due.allocations.filter(reversed_at=None).values_list('pk',flat=True))
    discount_ids = list(due.discounts.filter(reversed_at=None).values_list('pk',flat=True))
    due.allocations.filter(reversed_at=None).update(reversed_at=now)
    due.discounts.filter(reversed_at=None).update(reversed_at=now)
    audit(actor,'لغو تسویه با تأیید مدیر',f'license:{due.license_id}',before=before,after={'due':due.pk,'year':due.year,'approver':approver.username,'balance':due.balance,'reversed_allocations':allocation_ids,'reversed_discounts':discount_ids},reason=reason)
