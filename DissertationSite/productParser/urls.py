from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('homepage/', views.homepage, name="homepage"),
    path('send', views.send, name="send"),
    path('product/<slug:productName>/', views.product, name="product"),
    path('product/None', views.noTwitter, name="noTwitter"),
    path('analysis/<userName>/', views.analysis, name="analysis"),
]