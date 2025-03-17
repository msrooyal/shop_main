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
        required_fields = ['user_name', 'password', 'email', 'phone', 'name', 'profile_image', 'token', 'code']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'error': f'فیلد {field} ارسال نشده است. لطفاً تمام فیلدهای ضروری را پر کنید.'},
                                    status=400)

        username = data['user_name']
        password = data['password']
        email = data['email']
        phone = data['phone']
        name = data['name']
        profile_image = data['profile_image']
        token = data['token']
        code = data['code']

        # بررسی اعتبار توکن
        if token == 'TOKEN_USER':  # اصلاح شرط
            return JsonResponse({'error': 'توکن نامعتبر است. لطفاً از توکن معتبر استفاده کنید.'}, status=400)

        # بررسی زمان انقضای کد
        current_time = timezone.now()
        time_minuts_2 = current_time - timedelta(minutes=2)
        fp_user = ForgetPassword.objects.filter(
            (Q(phone=phone) | Q(email=email)) & Q(code=code) & Q(time_create__gt=time_minuts_2)
        ).first()

        if not fp_user:
            return JsonResponse({'error': 'کد فعالسازی نامعتبر یا منقضی شده است. لطفاً کد جدیدی دریافت کنید.'},
                                status=400)

        # بررسی تکراری نبودن نام کاربری، ایمیل و شماره تلفن
        if User.objects.filter(username=username).exists() and username !="":
            return JsonResponse({'error': 'این نام کاربری قبلاً ثبت شده است. لطفاً نام کاربری دیگری انتخاب کنید.'},
                                status=400)
        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'این ایمیل قبلاً ثبت شده است. لطفاً از ایمیل دیگری استفاده کنید.'},
                                status=400)
        if MyUser.objects.filter(phone=phone).exists() and phone !="":
            return JsonResponse({'error': 'این شماره همراه قبلاً ثبت شده است. لطفاً شماره دیگری وارد کنید.'},
                                status=400)

        # ایجاد کاربر جدید
        try:
            user = User.objects.create_user(username=username, password=password, email=email)
            if phone == "":
                phone=None
            if email=="":
                email=None
            # ایجاد توکن برای کاربر
            mystring = username + str(datetime.now())
            sha1_object = hashlib.sha1()
            sha1_object.update(mystring.encode('utf-8'))
            sha1_hash = sha1_object.hexdigest()

            # ذخیره توکن در مدل MyUser
            user2 = MyUser.objects.create(
                user_name=username,
                email=email,
                phone=phone,
                name=name,
                profile_image=profile_image,
                code=code,
                token=sha1_hash
            )
            fp_user.delete()
            return JsonResponse(
                {'success': 'کاربر با موفقیت اضافه شد. اکنون می‌توانید وارد شوید.', 'token_login': sha1_hash},
                status=200)

        except Exception as e:
            print("Error:", str(e))  # چاپ خطا برای دیباگ
            return JsonResponse({'error': 'خطا در ایجاد کاربر. لطفاً دوباره تلاش کنید.'}, status=500)

class Login(APIView):
    @staticmethod
    def post(request):
        data = request.data

        # بررسی اعتبار توکن
        if data['token'] != TOKEN_USER:
            return JsonResponse({'error': 'توکن نامعتبر است. لطفاً از توکن معتبر استفاده کنید.'}, status=400)

        phone = data['phone'] if 'phone' in data else ''
        email = data['email'] if 'email' in data else ''
        password = data['password']

        # بررسی اینکه آیا شماره تلفن یا ایمیل ارسال شده است
        if not phone and not email:
            return JsonResponse({'error': 'لطفاً شماره تلفن یا ایمیل خود را وارد کنید.'}, status=400)

        # پیدا کردن نام کاربری بر اساس شماره تلفن یا ایمیل
        try:
            if phone:
                username = MyUser.objects.get(phone=phone).user_name
            else:
                username = MyUser.objects.get(email=email).user_name
        except MyUser.DoesNotExist:
            return JsonResponse({'error': 'کاربری با این مشخصات وجود ندارد. لطفاً اطلاعات خود را بررسی کنید.'}, status=400)

        # احراز هویت کاربر
        user = authenticate(request, username=username, password=password)
        if user is not None:
            user = MyUser.objects.get(user_name=username)

            # تولید توکن ورود
            mystring = username + str(datetime.now())
            sha1_object = hashlib.sha1()
            sha1_object.update(mystring.encode('utf-8'))
            sha1_hash = sha1_object.hexdigest()
            user.token = sha1_hash
            user.save()
            return JsonResponse({'status': 'ورود موفقیت‌آمیز بود.', 'token': user.token}, status=200)
        else:
            return JsonResponse({'error': 'رمز عبور اشتباه است. لطفاً دوباره تلاش کنید.'}, status=400)


class ForgetPass(APIView):
    @staticmethod
    def post( request):
        data = request.data

        # بررسی اعتبار توکن
        if data['token'] != TOKEN_USER:
            return JsonResponse({'error': 'توکن نامعتبر است. لطفاً از توکن معتبر استفاده کنید.'}, status=400)

        phone = data['phone'] if 'phone' in data else ''
        email = data['email'] if 'email' in data else ''
        random_code = str(random.randint(10000, 999999))

        # بررسی اینکه آیا شماره تلفن یا ایمیل ارسال شده است
        if not phone and not email:
            return JsonResponse({'error': 'لطفاً شماره تلفن یا ایمیل خود را وارد کنید.'}, status=400)

        # بررسی وجود رکورد قبلی برای این کاربر
        existing_record = ForgetPassword.objects.filter(email=email).first() or \
                          ForgetPassword.objects.filter(phone=phone).first()

        if existing_record:
            existing_record.code = random_code
            existing_record.save()
        else:
            ForgetPassword.objects.create(phone=phone, email=email, code=random_code)

        # ارسال کد فراموشی از طریق پیامک یا ایمیل
        if phone:
            send_sms(phone, f"کد فراموشی شما: {random_code}")
            return JsonResponse({'status': 'پیامک حاوی کد فراموشی برای شما ارسال شد.'}, status=200)
        else:
            send_email(email, SUBJECT_FOR_FORGET_PASSWORD, f"کد فراموشی شما: {random_code}")
            return JsonResponse({'status': 'ایمیل حاوی کد فراموشی برای شما ارسال شد.'}, status=200)


class UpdatePass(APIView):
    @staticmethod
    def post(request):
        data = request.data

        # بررسی وجود کلیدهای مورد نیاز
        if 'token' not in data:
            return JsonResponse({'error': 'توکن ارسال نشده است. لطفاً توکن را وارد کنید.'}, status=400)

        if data['token'] != TOKEN_USER:
            return JsonResponse({'error': 'توکن نامعتبر است. لطفاً از توکن معتبر استفاده کنید.'}, status=400)

        if 'password' not in data or not data['password']:
            return JsonResponse({'error': 'رمز عبور جدید ارسال نشده است. لطفاً رمز عبور جدید را وارد کنید.'}, status=400)

        if 'code' not in data or not data['code']:
            return JsonResponse({'error': 'کد فعالسازی ارسال نشده است. لطفاً کد را وارد کنید.'}, status=400)

        # بررسی اینکه آیا شماره تلفن یا ایمیل ارسال شده است
        if 'phone' not in data and 'email' not in data:
            return JsonResponse({'error': 'شماره تلفن یا ایمیل ارسال نشده است. لطفاً یکی از آنها را وارد کنید.'}, status=400)

        phone = data.get('phone', '')
        email = data.get('email', '')
        password = data['password']
        code = data['code']

        # بررسی وجود کاربر
        if not MyUser.objects.filter(Q(phone=phone) | Q(email=email)).exists():
            return JsonResponse({'error': 'کاربری با این مشخصات یافت نشد. لطفاً اطلاعات خود را بررسی کنید.'}, status=400)

        # بررسی زمان انقضای کد
        current_time = timezone.now()
        time_minuts_2 = current_time - timedelta(minutes=2)
        fp_user = ForgetPassword.objects.filter(
            (Q(phone=phone) | Q(email=email)) & Q(code=code) & Q(time_create__gt=time_minuts_2)
        ).first()

        if not fp_user:
            return JsonResponse({'error': 'کد فعالسازی نامعتبر یا منقضی شده است. لطفاً کد جدیدی دریافت کنید.'}, status=400)

        # تغییر رمز عبور
        try:
            username = MyUser.objects.get(Q(phone=phone) | Q(email=email)).user_name
            user = User.objects.get(username=username)
            user.set_password(password)
            user.save()

            # حذف رکورد ForgetPassword
            fp_user.delete()

            return JsonResponse({'status': 'رمز عبور شما با موفقیت تغییر کرد.'}, status=200)
        except Exception as e:
            return JsonResponse({'error': 'خطا در تغییر رمز عبور. لطفاً دوباره تلاش کنید.'}, status=500)

class UpdateProfile(APIView):
    @staticmethod
    def post(request):
        data = request.data

        # بررسی وجود کلیدهای مورد نیاز
        if 'token' not in data:
            return JsonResponse({'error': 'توکن ارسال نشده است. لطفاً توکن را وارد کنید.'}, status=400)

        if data['token'] != TOKEN_USER:
            return JsonResponse({'error': 'توکن نامعتبر است. لطفاً از توکن معتبر استفاده کنید.'}, status=400)

        if 'token_login' not in data:
            return JsonResponse({'error': 'توکن ورود ارسال نشده است. لطفاً مجدداً وارد شوید.'}, status=400)

        username = data['user_name']
        name = data['name']
        profile_image = data['profile_image']
        token_login = data['token_login']

        # بررسی اعتبار توکن ورود
        user = MyUser.objects.filter(token=token_login)
        if not user.exists():
            return JsonResponse({'error': 'توکن ورود نامعتبر است. لطفاً مجدداً وارد شوید.'}, status=400)

        # به‌روزرسانی پروفایل
        user.update(name=name, profile_image=profile_image, user_name=username)
        return JsonResponse({'status': 'تغییرات با موفقیت اعمال شد.'}, status=200)

class Logout(APIView):
    pass



class RegisterVerify(APIView):
    @staticmethod
    def post(request):
        data = request.data

        # بررسی اعتبار توکن
        if data.get('token') != TOKEN_USER:
            return JsonResponse({'error': 'توکن نامعتبر است. لطفاً از توکن معتبر استفاده کنید.'}, status=400)

        phone = data.get('phone', '')
        email = data.get('email', '')
        random_code = str(random.randint(10000, 999999))

        # بررسی اینکه آیا شماره تلفن یا ایمیل ارسال شده است
        if not phone and not email:
            return JsonResponse({'error': 'لطفاً شماره تلفن یا ایمیل خود را وارد کنید.'}, status=400)

        # بررسی وجود رکورد قبلی برای این کاربر
        existing_record = ForgetPassword.objects.filter(email=email).first() or \
                          ForgetPassword.objects.filter(phone=phone).first()

        if existing_record:
            existing_record.code = random_code
            existing_record.save()
        else:
            ForgetPassword.objects.create(phone=phone, email=email, code=random_code)

        # ارسال کد فراموشی از طریق پیامک یا ایمیل
        if phone:
            send_sms(phone, f"کد فراموشی شما: {random_code}")
            return JsonResponse({'status': 'پیامک حاوی کد فراموشی برای شما ارسال شد.'}, status=201)  # تغییر کد وضعیت به 201

        else:
            send_email(email, SUBJECT_FOR_FORGET_PASSWORD, f"کد فراموشی شما: {random_code}")
            return JsonResponse({'status': 'ایمیل حاوی کد فراموشی برای شما ارسال شد.'}, status=201)  # تغییر کد وضعیت به 201