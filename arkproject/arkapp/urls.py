from django.urls import path
from arkapp import views

urlpatterns = [
  path('',views.home,name='home')
]
