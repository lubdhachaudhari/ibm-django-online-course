from django.urls import path
from . import views

app_name = 'onlinecourse'

urlpatterns = [
    # Course list and details
    path('', views.CourseListView.as_view(), name='index'),
    path('course/<int:pk>/', views.CourseDetailsView.as_view(), name='course_details'),
    path('course/<int:course_id>/enroll/', views.enroll, name='enroll'),

    # Exam submission and result routes
    path('course/<int:course_id>/submit/', views.submit, name='submit'),
    path(
        'course/<int:course_id>/submission/<int:submission_id>/result/',
        views.show_exam_result,
        name='show_exam_result'
    ),
    path(
        'course/<int:course_id>/result/',
        views.show_exam_result,
        name='show_exam_result_course'
    ),

    # Authentication routes
    path('login/', views.login_request, name='login'),
    path('logout/', views.logout_request, name='logout'),
    path('registration/', views.registration_request, name='registration'),
]
