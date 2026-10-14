from django.urls import path
from . import views

urlpatterns = [
    path('availability/slots/', views.available_appointment_slots, name='available_appointment_slots'),
    path('book/', views.book_appointment, name='book_appointment'),
    path('', views.appointment_list, name='appointment_list'),
    path('<int:pk>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('<int:pk>/status/', views.update_status, name='update_appointment_status'),
]
