from datetime import datetime
import hashlib
import random
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
        username = data['user_name']
        password = data['password']
        email = data['email']
        phone = data['phone']
        name = data['name']
        profile_image = data['profile_image']
        token = data['token']

        if token =='TOKEN_USER':
            if User.objects.filter(username=username).exists():
                return JsonResponse({'error': 'این نام کاربری قبلا ثبت شده است'},status=400)
            elif User.objects.filter(email=email).exists():
                return JsonResponse({'error': 'این ایمیل قبلا ثبت شده است'},status=400)
            elif MyUser.objects.filter(phone=phone).exists():
                return JsonResponse({'error': 'این شماره همراه قبلا ثبت شده است'},status=400)
            else:
                user = User.objects.create_user(username=username, password=password, email=email)
                user2 = MyUser.objects.create(user_name=username,  email=email, phone=phone, name=name, profile_image=profile_image)
                return JsonResponse({'success': 'کاربر با موفقیت اضافه شد'},status=201)
        else:
            return JsonResponse({'error':'token not valid'}, status=400)





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

class Logout(APIView):
    pass

class RegisterVerify(APIView):
    pass

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
class UpdateProfile(APIView):
    pass
