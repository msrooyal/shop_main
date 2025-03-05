from django.contrib import admin
from django.urls import path
from user.views import Register, Login, Logout, ForegetPass, UpdatePass, UpdateProfile

app_name = 'user'
urlpatterns = [
    path('register', Register.as_view(), name='register'),
    path('login', Login.as_view(), name='login'),
    path('logout', Logout.as_view(), name='logout'),
    path('register_verify', Register.as_view(), name='register_verify'),
    path('forget_pass',ForegetPass.as_view(), name='forget_pass'),
    path('update_pass',UpdatePass.as_view(),name='update_pass'),
    path('update_profile',UpdateProfile.as_view(),name='update_profile'),


]