from django.db import models
from django.utils import timezone
import uuid
from datetime import timedelta

class User(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField(unique=True,null=True)
    phone = models.CharField(max_length=18, unique=True, null=True)
    user_name = models.CharField(max_length=50, unique=True, null=True)
    profile_image = models.CharField(max_length=50,null=True)
    token = models.CharField(max_length=200,null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateField(auto_now=True)
    code = models.CharField(max_length=50,unique=True,null=True)

    def __str__(self):
        return self.email



class ForgetPassword(models.Model):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=18, unique=True)
    code = models.CharField(max_length=50, unique=True,null=True)
    time_create = models.DateTimeField(auto_now=True,unique=True,null=True)  # زمان ایجاد کد

    def __str__(self):
        return self.email

