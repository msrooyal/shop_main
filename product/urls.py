from django.contrib import admin
from django.urls import path

from product import views
from product.views import HomeView

app_name = 'product'
urlpatterns = [
    path('home/',views.HomeView.as_view(),name='home'),
    path("add_category",views.AddCategory.as_view(),name='add_category'),
    path('add_product',views.AddProduct.as_view(),name='add_product'),
    path('update_product',views.UpdateProduct.as_view(),name='update_product'),
    path('delete_product',views.DeleteProduct.as_view(),name='delete_product'),
    path('add_comment',views.AddCommentProduct.as_view(),name='add_comment'),



]