from django.contrib import admin
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static


def auto_admin(request):
    if not settings.DEBUG:
        return redirect('/admin/')
    user = User.objects.get(username='admin')
    login(request, user)
    return redirect('/admin/')


def auto_student(request, course_id, submission_id):
    if not settings.DEBUG:
        return redirect('onlinecourse:course_details', pk=course_id)
    user = User.objects.get(username='student1')
    login(request, user)
    return redirect('onlinecourse:show_exam_result', course_id=course_id, submission_id=submission_id)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('onlinecourse/', include('onlinecourse.urls')),
    path('', lambda request: redirect('onlinecourse:index', permanent=False)),
]

if settings.DEBUG:
    urlpatterns += [
        path('auto-admin/', auto_admin, name='auto_admin'),
        path('auto-student/<int:course_id>/<int:submission_id>/', auto_student, name='auto_student'),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
