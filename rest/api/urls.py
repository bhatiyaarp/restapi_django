from django.urls import path
from . import views

urlpatterns = [
    path('', views.start, name='home'),
    path('model/', views.model_call.as_view() ),
]
