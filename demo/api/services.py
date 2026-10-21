from datetime import datetime, timedelta,timezone as datetime_timezone
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

from tasks.models import Task
from ..models import DemoSession

User= get_user_model()

def cap_tokens(tokens, expires_at):
    deadline= int(expires_at.timestamp())
    access= AccessToken(tokens["access"])
    access["exp"]= min(deadline, access["exp"])
    result= {"access": str(access)}

    if "refresh" in tokens:
        refresh= RefreshToken(tokens["refresh"])
        refresh["exp"]= min(deadline, refresh["exp"])
        result["refresh"] = str(refresh)

        OutstandingToken.objects.filter(
            jti= refresh[api_settings.JTI_CLAIM],
        ).update(
            token=result["refresh"],
            expires_at= datetime.fromtimestamp(refresh["exp"],tz=datetime_timezone.utc)
        )
    return result

@transaction.atomic
def create_demo():
    lifetime= int(getattr(settings, "DEMO_SESSION_MINUTES", 30))
    if lifetime < 1:
        raise ValueError("DEMO_SESSION_MINUTES must be positive.")
    expires_at = timezone.now() + timedelta(minutes=lifetime)
    unique= uuid4().hex
    user= User.objects.create_user(
        username=f"demo_{unique}",
        email=f"{unique}@example.com",
        password=None,
    )
    session= DemoSession.objects.create(
        user=user,
        expires_at=expires_at
    )
    today= timezone.localdate()


    examples = [
        (
            "تکمیل گزارش پروژه",
            "بخش نتایج را کامل کن، نمودارها را اضافه کن و نسخه نهایی گزارش را برای بازبینی آماده کن.",
            "in_progress",
            "high",
            0,
        ),
        (
            "پرداخت قبض اینترنت",
            "مبلغ قبض این ماه را بررسی کن و پرداخت را قبل از سررسید انجام بده.",
            "todo",
            "high",
            1,
        ),
        (
            "آماده‌کردن اسلایدهای ارائه",
            "اسلایدهای اصلی را آماده کن، تصاویر مرتبط را اضافه کن و متن ارائه را مرور کن.",
            "todo",
            "high",
            2,
        ),
        (
            "پاسخ به ایمیل‌های کاری",
            "ایمیل‌های دریافت‌شده را بررسی کن و به پیام‌هایی که نیاز به پاسخ دارند جواب بده.",
            "todo",
            "medium",
            0,
        ),
        (
            "خرید مواد غذایی هفته",
            "اقلام ضروری خانه را فهرست کن و خریدهای موردنیاز هفته را انجام بده.",
            "todo",
            "medium",
            2,
        ),
        (
            "مرتب‌کردن فایل‌های لپ‌تاپ",
            "فایل‌های پراکنده را دسته‌بندی کن، پوشه‌های اضافی را مرتب کن و موارد غیرضروری را حذف کن.",
            "in_progress",
            "low",
            4,
        ),
        (
            "مطالعه فصل سوم کتاب",
            "فصل سوم را مطالعه کن و نکات مهم را برای مرور بعدی یادداشت کن.",
            "todo",
            "medium",
            3,
        ),
        (
            "رزرو وقت دندان‌پزشکی",
            "زمان‌های آزاد را بررسی کن و برای معاینه دوره‌ای وقت بگیر.",
            "todo",
            "high",
            None,
        ),
        (
            "تحویل تمرین برنامه‌نویسی",
            "کد را بررسی کن، تست‌ها را اجرا کن و نسخه نهایی تمرین را ارسال کن.",
            "in_progress",
            "high",
            -1,
        ),
        (
            "تهیه فهرست هزینه‌های ماه",
            "هزینه‌های ثبت‌شده را دسته‌بندی کن و مجموع مخارج هر دسته را محاسبه کن.",
            "done",
            "medium",
            -1,
        ),
        (
            "به‌روزرسانی رزومه",
            "مهارت‌های جدید و پروژه‌های اخیر را به رزومه اضافه کن و اطلاعات قبلی را بازبینی کن.",
            "todo",
            "low",
            None,
        ),
        (
            "پشتیبان‌گیری از فایل‌های مهم",
            "از اسناد شخصی و فایل‌های پروژه نسخه پشتیبان تهیه کن و سالم‌بودن فایل‌ها را بررسی کن.",
            "done",
            "medium",
            -2,
        ),
        (
            "برنامه‌ریزی هفته آینده",
            "کارهای مهم هفته آینده را مشخص کن و برای هرکدام زمان تقریبی در نظر بگیر.",
            "done",
            "low",
            -3,
        ),
    ]

    for title, description, status, priority, days in reversed(examples):
        Task.objects.create(
            owner= user,
            title=title,
            description=description,
            status=status,
            priority=priority,
            due_date= None if days is None else today + timedelta(days=days),
        )
    refresh= RefreshToken.for_user(user)
    tokens= cap_tokens({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        }, expires_at)
    
    return session, tokens

def delete_demo_user(user_id):
    session= DemoSession.objects.filter(user_id=user_id).first()
    if not session:
        return False
    User.objects.filter(pk=session.user_id).delete()
    return True

def cleanup_expired(*, batch_size=100, now=None):
    now= now or timezone.now()
    ids= list(DemoSession.objects
            .filter(expires_at__lte=now)
            .values_list("user_id",flat=True)[:batch_size]
        )
    if not ids:
        return 0
    with transaction.atomic():
        guests = User.objects.filter(pk__in=ids, demo_session__expires_at__lte=now)
        count= guests.count()
        guests.delete()
    return count