from datetime import date
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from onlinecourse.models import (
    Course,
    Lesson,
    Instructor,
    Question,
    Choice,
    Enrollment
)


class Command(BaseCommand):
    help = 'Create development sample data for courses, lessons, questions, and choices.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Setting up development sample data..."))

        # 1. Create or get Admin superuser
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'first_name': 'Django',
                'last_name': 'Admin',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created or not admin_user.check_password('admin123'):
            admin_user.set_password('admin123')
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Superuser 'admin' created/updated with password 'admin123'."))

        # 2. Create or get standard Student user
        student_user, s_created = User.objects.get_or_create(
            username='student1',
            defaults={
                'email': 'student1@example.com',
                'first_name': 'Alex',
                'last_name': 'Developer',
            }
        )
        if s_created or not student_user.check_password('password123'):
            student_user.set_password('password123')
            student_user.save()
            self.stdout.write(self.style.SUCCESS("Sample user 'student1' created/updated with password 'password123'."))

        # 3. Create or get Instructor
        inst_user, i_created = User.objects.get_or_create(
            username='instructor_jane',
            defaults={
                'email': 'jane@example.com',
                'first_name': 'Jane',
                'last_name': 'Doe',
            }
        )
        if i_created:
            inst_user.set_password('instructor123')
            inst_user.save()

        instructor, _ = Instructor.objects.get_or_create(
            user=inst_user,
            defaults={'full_time': True, 'total_learners': 150}
        )

        # 4. Create or get Sample Course
        course, c_created = Course.objects.get_or_create(
            name="Cloud App Development with Django and Databases",
            defaults={
                'description': "Comprehensive IBM professional course covering Django MVT architecture, ORM models, administration portal, user authentication, and online examination workflows.",
                'pub_date': date.today(),
                'total_enrollment': 25
            }
        )
        course.instructors.add(instructor)
        if c_created:
            self.stdout.write(self.style.SUCCESS(f"Created Course: {course.name}"))
        else:
            self.stdout.write(self.style.NOTICE(f"Course already exists: {course.name}"))

        # 5. Enroll student1 in the course
        Enrollment.objects.get_or_create(
            user=student_user,
            course=course,
            defaults={'mode': 'audit', 'rating': 5.0}
        )

        # 6. Create or get Lessons
        lesson_data = [
            (
                "Django Architecture & ORM Models",
                1,
                "In this lesson, you will learn about the Django Model-View-Template pattern, setting up relational database tables using Python classes, and performing database migrations."
            ),
            (
                "Django Administration & Inlines",
                2,
                "Explore Django's powerful built-in admin site. Learn how to register models, customize list displays, and use TabularInline and StackedInline to manage related records in a single view."
            ),
            (
                "Exam Engineering & HTTP POST Submissions",
                3,
                "Learn how to process exam submissions safely using HTTP POST, validate CSRF tokens, evaluate selected choices, calculate grades, and render student report cards."
            ),
        ]

        lessons = {}
        for title, order, content in lesson_data:
            lesson, _ = Lesson.objects.get_or_create(
                course=course,
                title=title,
                defaults={'order': order, 'content': content}
            )
            lessons[order] = lesson

        # 7. Create Questions and Choices
        # Question 1 (Lesson 1)
        q1, _ = Question.objects.get_or_create(
            lesson=lessons[1],
            question_text="Which Django file is used to define database models and schema relationships?",
            defaults={'question_type': 'single', 'grade': 1, 'order': 1}
        )
        q1.courses.add(course)
        q1_choices = [
            ("views.py", False),
            ("models.py", True),
            ("urls.py", False),
            ("admin.py", False),
        ]
        for c_text, is_corr in q1_choices:
            Choice.objects.get_or_create(
                question=q1,
                choice_text=c_text,
                defaults={'is_correct': is_corr}
            )

        # Question 2 (Lesson 2)
        q2, _ = Question.objects.get_or_create(
            lesson=lessons[2],
            question_text="Which inline class should you use to display child records in a compact tabular grid in Django Admin?",
            defaults={'question_type': 'single', 'grade': 1, 'order': 2}
        )
        q2.courses.add(course)
        q2_choices = [
            ("admin.TabularInline", True),
            ("admin.StackedInline", False),
            ("admin.GridInline", False),
            ("admin.RowInline", False),
        ]
        for c_text, is_corr in q2_choices:
            Choice.objects.get_or_create(
                question=q2,
                choice_text=c_text,
                defaults={'is_correct': is_corr}
            )

        # Question 3 (Lesson 3)
        q3, _ = Question.objects.get_or_create(
            lesson=lessons[3],
            question_text="Which HTTP request method should be used to process exam submissions securely?",
            defaults={'question_type': 'single', 'grade': 1, 'order': 3}
        )
        q3.courses.add(course)
        q3_choices = [
            ("POST", True),
            ("GET", False),
            ("PUT", False),
            ("DELETE", False),
        ]
        for c_text, is_corr in q3_choices:
            Choice.objects.get_or_create(
                question=q3,
                choice_text=c_text,
                defaults={'is_correct': is_corr}
            )

        # Question 4 (Lesson 3)
        q4, _ = Question.objects.get_or_create(
            lesson=lessons[3],
            question_text="Which template tag is essential inside every Django HTML POST form to prevent CSRF attacks?",
            defaults={'question_type': 'single', 'grade': 1, 'order': 4}
        )
        q4.courses.add(course)
        q4_choices = [
            ("{% csrf_token %}", True),
            ("{% secure_token %}", False),
            ("{% form_protect %}", False),
            ("{% auth_check %}", False),
        ]
        for c_text, is_corr in q4_choices:
            Choice.objects.get_or_create(
                question=q4,
                choice_text=c_text,
                defaults={'is_correct': is_corr}
            )

        self.stdout.write(self.style.SUCCESS("Sample data setup successfully completed!"))
