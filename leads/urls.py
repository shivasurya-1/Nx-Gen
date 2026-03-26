from django.urls import path
from .views import ContactUsView, ScheduleDemoView

urlpatterns = [
    path('contact-us/', ContactUsView.as_view()),
   
    path("schedule-demo/", ScheduleDemoView.as_view()),

]