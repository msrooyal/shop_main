from django.db import models
from django.utils import timezone
import uuid
from datetime import timedelta

class User(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=18, unique=True)
    user_name = models.CharField(max_length=50, unique=True)
    profile_image = models.CharField(max_length=50)
    token = models.CharField(max_length=200,null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateField(auto_now=True)

    def __str__(self):
        return self.email

    def generate_verification_code(self):
        # تولید یک کد تصادفی ۶ رقمی
        self.verification_code = str(uuid.uuid4().int)[:6]
        # تنظیم زمان انقضا (مثلاً ۱۰ دقیقه بعد)
        self.verification_code_expires = timezone.now() + timedelta(minutes=2)
        self.save()

    def is_verification_code_valid(self, code):
        # بررسی معتبر بودن کد و زمان انقضا
        if self.verification_code == code and timezone.now() < self.verification_code_expires:
            return True
        return False

class ForgetPassword(models.Model):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=18, unique=True)
    code = models.CharField(max_length=50, unique=True)
    def __str__(self):
        return self.email