from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('homepage/', views.homepage, name="homepage"),
    path('send', views.send, name="send"),
    path('product/<slug:productName>/', views.product, name="product"),
    path('analysis/<userName>/', views.analysis, name="analysis"),
    path('posts-requested/', views.JSView.as_view(), name="posts-requested"),
]