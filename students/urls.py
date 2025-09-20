from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('students/', views.students_list, name='students_list'),
    path('students/create/', views.student_create, name='student_create'),
    path('students/<int:student_id>/', views.student_detail, name='student_detail'),
    path('students/<int:student_id>/edit/', views.student_update, name='student_update'),
    path('students/<int:student_id>/delete/', views.student_delete, name='student_delete'),
    path('students/<int:student_id>/admission/', views.admission_create, name='admission_create'),
    path('students/<int:student_id>/locker/', views.locker_create, name='locker_create'),
    path('students/<int:student_id>/payment/', views.payment_create, name='payment_create'),
    path('lockers/<int:locker_id>/edit/', views.locker_update, name='locker_update'),
    path('lockers/<int:locker_id>/delete/', views.locker_delete, name='locker_delete'),
    path('payments/<int:payment_id>/edit/', views.payment_update, name='payment_update'),
    path('payments/<int:payment_id>/delete/', views.payment_delete, name='payment_delete'),
    path('leads/', views.contact_leads, name='contact_leads'),
    path('finance/', views.finance_dashboard, name='finance_dashboard'),
    path('students/export-csv/', views.export_students_csv, name='export_students_csv'),
  
]