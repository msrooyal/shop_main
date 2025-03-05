from datetime import datetime, timedelta
import hashlib
import random

from django.utils import timezone
from django.db.models import Q
from django.template.context_processors import request
from django.contrib.auth import authenticate
from django.shortcuts import render
from rest_framework.views import APIView
from django.http import JsonResponse
from django.contrib.auth.models import User
from .models import User as MyUser, ForgetPassword
from .utils.constant import TOKEN_USER, SUBJECT_FOR_FORGET_PASSWORD
from .utils.utils import send_email, send_sms, template



class Register(APIView):
    @staticmethod
    def post(request):
        data = request.data

        # بررسی وجود کلیدهای مورد نیاز در داده‌های ورودی
        required_fields = ['user_name', 'password', 'email', 'phone', 'name', 'profile_image', 'token']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'error': f'فیلد {field} ارسال نشده است'}, status=400)

        username = data['user_name']
        password = data['password']
        email = data['email']
        phone = data['phone']
        name = data['name']
        profile_image = data['profile_image']
        token = data['token']

        # بررسی اعتبار توکن
        if token == 'TOKEN_USER':
            return JsonResponse({'error': 'توکن نامعتبر است'}, status=400)

        # بررسی تکراری نبودن نام کاربری، ایمیل و شماره تلفن
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'این نام کاربری قبلا ثبت شده است'}, status=400)
        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'این ایمیل قبلا ثبت شده است'}, status=400)
        if MyUser.objects.filter(phone=phone).exists():
            return JsonResponse({'error': 'این شماره همراه قبلا ثبت شده است'}, status=400)

        # ایجاد کاربر جدید
        try:
            user = User.objects.create_user(username=username, password=password, email=email)
            user2 = MyUser.objects.create(user_name=username, email=email, phone=phone, name=name, profile_image=profile_image)
            return JsonResponse({'success': 'کاربر با موفقیت اضافه شد'}, status=201)
        except Exception as e:
            return JsonResponse({'error': 'خطا در ایجاد کاربر'}, status=500)

class Login(APIView):
    @staticmethod
    def post(request):
        data = request.data
        if  data['token'] == TOKEN_USER:
            phone = data['phone'] if 'phone' in data else ''
            email = data['email'] if 'email' in data else ''
            password = data['password']
            if phone != "" and email == "":
                username = MyUser.objects.get(phone=phone).user_name
            else:
                username = MyUser.objects.get(email=email).user_name
            user = authenticate(request, username=username, password=password)

            if user is not None:
                user = MyUser.objects.get(user_name=username)

                mystring = username + str(datetime.now())
                sha1_object = hashlib.sha1()
                sha1_object.update(mystring.encode('utf-8'))
                sha1_hash = sha1_object.hexdigest()
                user.token = sha1_hash
                user.save()
                return JsonResponse({'status':'ورود موفقیت آمیز بود', 'token':user.token}, status=400)
            else:
                return JsonResponse({'status':'کاربری با این مشخصات وجود ندارد'}, status=400)
        else:
            return JsonResponse({'error':'token not valid'},status=400)


class ForegetPass(APIView):
    def post(self, request):
        data = request.data
        if data['token'] == TOKEN_USER:
            phone = data['phone'] if 'phone' in data else ''
            email = data['email'] if 'email' in data else ''
            random_code = str(random.randint(10000,999999))
            if not phone and not email:
                return JsonResponse({'error': "لطفاً شماره تلفن یا ایمیل وارد کنید"}, status=400)

                # بررسی اینکه آیا رکوردی برای این کاربر وجود دارد
            existing_record = ForgetPassword.objects.filter(email=email).first() or \
                              ForgetPassword.objects.filter(phone=phone).first()

            if existing_record:
                existing_record.code = random_code
                existing_record.save()
            else:
                ForgetPassword.objects.create(phone=phone, email=email, code=random_code)

            # ارسال پیامک یا ایمیل
            if phone:
                send_sms(phone, f"کد فراموشی شما: {random_code}")  # فرض می‌کنیم send_sms تعریف شده باشد
                return JsonResponse({'status': "پیامک کد فراموشی برای شما ارسال شد"}, status=200)
            else:
                send_email(email, SUBJECT_FOR_FORGET_PASSWORD, f"کد فراموشی شما برابر است با {random_code}")
                return JsonResponse({'status': "ایمیل فعالسازی برای شما ارسال شد"}, status=200)



        else:
            return JsonResponse({'error':'token not valid'},status=400)


class UpdatePass(APIView):
    @staticmethod
    def post(request):
        data = request.data

        # بررسی وجود کلیدهای مورد نیاز در داده‌های ورودی
        if 'token' not in data:
            return JsonResponse({'error': 'توکن ارسال نشده است'}, status=400)

        if data['token'] != TOKEN_USER:
            return JsonResponse({'error': 'توکن نامعتبر است'}, status=400)

        if 'password' not in data or not data['password']:
            return JsonResponse({'error': 'رمز عبور جدید ارسال نشده است'}, status=400)

        if 'code' not in data or not data['code']:
            return JsonResponse({'error': 'کد فعالسازی ارسال نشده است'}, status=400)

        # حداقل یکی از phone یا email باید ارسال شده باشد
        if 'phone' not in data and 'email' not in data:
            return JsonResponse({'error': 'شماره تلفن یا ایمیل ارسال نشده است'}, status=400)

        phone = data.get('phone', '')
        email = data.get('email', '')
        password = data['password']
        code = data['code']

        # بررسی وجود کاربر با شماره تلفن یا ایمیل داده شده
        if not MyUser.objects.filter(Q(phone=phone) | Q(email=email)).exists():
            return JsonResponse({'error': 'کاربری با این مشخصات یافت نشد'}, status=400)

        # زمان فعلی و زمان انقضا (۲ دقیقه قبل)
        current_time = timezone.now()
        time_minuts_2 = current_time - timedelta(minutes=2)

        # بررسی وجود رکورد ForgetPassword با کد و شماره تلفن یا ایمیل داده شده و زمان انقضا
        fp_user = ForgetPassword.objects.filter(
            (Q(phone=phone) | Q(email=email)) & Q(code=code) & Q(time_create__gt=time_minuts_2)
        ).first()

        if not fp_user:
            return JsonResponse({'error': 'کد فعالسازی نامعتبر یا منقضی شده است'}, status=400)

        # تغییر رمز عبور کاربر
        try:
            username = MyUser.objects.get(Q(phone=phone) | Q(email=email)).user_name
            user = User.objects.get(username=username)
            user.set_password(password)
            user.save()

            # حذف رکورد ForgetPassword بعد از تأیید کد
            fp_user.delete()

            return JsonResponse({'status': 'رمز عبور شما با موفقیت تغییر کرد'}, status=200)
        except Exception as e:
            return JsonResponse({'error': 'خطا در تغییر رمز عبور'}, status=500)

class UpdateProfile(APIView):
    @staticmethod
    def post(request):
        data = request.data
        username = data['user_name']
        name = data['name']
        profile_image = data['profile_image']
        token = data['token']
        token_login = data['token_login'] if 'token_login' in data else ""
        if token == TOKEN_USER:
            user = MyUser.objects.filter(token=token_login)
            if user.exists():
                user.update(name=name, profile_image=profile_image,user_name=username)
                return JsonResponse({'status':"تغییرات با موفقیت اعمال شد"}, status=200)
            else:
                return JsonResponse({'error':"خطا در اعتبار سنجی لطفا مجددا دوباره وارد شوید"},status=400)


        else:
            return JsonResponse({'error':"token not valid"},status=400)

class Logout(APIView):
    pass

class RegisterVerify(APIView):
    pass


