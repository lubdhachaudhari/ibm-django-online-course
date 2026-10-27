from django.contrib import admin
from .models import (
    Course,
    Lesson,
    Instructor,
    Learner,
    Enrollment,
    Question,
    Choice,
    Submission
)


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3
    fields = ('choice_text', 'is_correct')


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 2
    fields = ('question_text', 'grade', 'question_type', 'order')


class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 1
    fields = ('title', 'order', 'content')


class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]
    list_display = ('question_text', 'lesson', 'grade', 'question_type')
    list_filter = ('lesson', 'question_type', 'grade')
    search_fields = ('question_text',)


class LessonAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    search_fields = ('title', 'content')


class CourseAdmin(admin.ModelAdmin):
    inlines = [LessonInline]
    list_display = ('name', 'pub_date', 'total_enrollment')
    list_filter = ('pub_date',)
    search_fields = ('name', 'description')


class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'question', 'choice', 'submitted_at')
    list_filter = ('submitted_at', 'user')
    search_fields = ('user__username', 'question__question_text')


class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'mode', 'rating', 'date_enrolled')
    list_filter = ('mode', 'course')
    search_fields = ('user__username', 'course__name')


class LearnerAdmin(admin.ModelAdmin):
    list_display = ('user', 'occupation', 'social_link')
    list_filter = ('occupation',)
    search_fields = ('user__username',)


class InstructorAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_time', 'total_learners')
    list_filter = ('full_time',)
    search_fields = ('user__username',)


admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Instructor, InstructorAdmin)
admin.site.register(Learner, LearnerAdmin)
admin.site.register(Enrollment, EnrollmentAdmin)
