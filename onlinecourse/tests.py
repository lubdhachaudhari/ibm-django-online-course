from django.contrib.auth.models import User
from django.contrib import admin
from django.test import TestCase, Client
from django.urls import reverse, resolve
from onlinecourse.models import (
    Course,
    Lesson,
    Question,
    Choice,
    Submission,
    Enrollment,
    Instructor
)
from onlinecourse.admin import (
    QuestionInline,
    ChoiceInline,
    QuestionAdmin,
    LessonAdmin
)
from onlinecourse.views import submit, show_exam_result, CourseDetailsView


class OnlineCourseModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass123')
        self.course = Course.objects.create(name='Test Django Course', description='Test Description')
        self.lesson = Lesson.objects.create(title='Lesson 1', course=self.course, order=1, content='Content 1')
        self.question = Question.objects.create(
            lesson=self.lesson,
            question_text='What is Django?',
            grade=2
        )
        self.c1 = Choice.objects.create(question=self.question, choice_text='A web framework', is_correct=True)
        self.c2 = Choice.objects.create(question=self.question, choice_text='A database', is_correct=False)

    def test_model_relationships(self):
        """Verify models link properly through foreign keys."""
        self.assertEqual(self.lesson.course, self.course)
        self.assertIn(self.lesson, self.course.lessons.all())
        self.assertEqual(self.question.lesson, self.lesson)
        self.assertEqual(self.question.choices.count(), 2)
        self.assertEqual(self.c1.question, self.question)

    def test_question_is_get_score(self):
        """Verify Question.is_get_score scoring logic."""
        # Correct choice passed as list of ints
        self.assertTrue(self.question.is_get_score([self.c1.id]))
        # Correct choice passed as int
        self.assertTrue(self.question.is_get_score(self.c1.id))
        # Correct choice passed as string
        self.assertTrue(self.question.is_get_score(str(self.c1.id)))
        # Incorrect choice
        self.assertFalse(self.question.is_get_score([self.c2.id]))
        # Both choices (wrong answer included)
        self.assertFalse(self.question.is_get_score([self.c1.id, self.c2.id]))
        # Empty choices
        self.assertFalse(self.question.is_get_score([]))

    def test_submission_model(self):
        """Verify Submission model fields and properties."""
        sub = Submission.objects.create(
            user=self.user,
            question=self.question,
            choice=self.c1
        )
        self.assertEqual(sub.user, self.user)
        self.assertEqual(sub.question, self.question)
        self.assertEqual(sub.choice, self.c1)
        self.assertIsNotNone(sub.submitted_at)


class AdminConfigurationTests(TestCase):
    def test_admin_classes_and_inlines(self):
        """Verify admin inline and model admin classes."""
        self.assertTrue(issubclass(QuestionInline, admin.StackedInline))
        self.assertTrue(issubclass(ChoiceInline, admin.TabularInline))
        self.assertTrue(issubclass(QuestionAdmin, admin.ModelAdmin))
        self.assertTrue(issubclass(LessonAdmin, admin.ModelAdmin))

        self.assertIn(ChoiceInline, QuestionAdmin.inlines)
        self.assertIn(QuestionInline, LessonAdmin.inlines)

    def test_admin_registration(self):
        """Verify Question, Lesson, Course, Choice, Submission are registered in admin.site."""
        self.assertIn(Question, admin.site._registry)
        self.assertIn(Lesson, admin.site._registry)
        self.assertIn(Course, admin.site._registry)
        self.assertIn(Choice, admin.site._registry)
        self.assertIn(Submission, admin.site._registry)
        # Authentication and authorization registered
        self.assertIn(User, admin.site._registry)


class URLResolutionTests(TestCase):
    def test_url_patterns_resolve(self):
        """Verify unique route names resolve to expected view functions."""
        self.assertEqual(resolve('/onlinecourse/course/1/submit/').func, submit)
        self.assertEqual(resolve('/onlinecourse/course/1/submission/1/result/').func, show_exam_result)
        self.assertEqual(resolve('/onlinecourse/course/1/result/').func, show_exam_result)

        # Check reverse resolution
        self.assertEqual(reverse('onlinecourse:submit', args=[1]), '/onlinecourse/course/1/submit/')
        self.assertEqual(
            reverse('onlinecourse:show_exam_result', args=[1, 10]),
            '/onlinecourse/course/1/submission/10/result/'
        )
        self.assertEqual(
            reverse('onlinecourse:show_exam_result_course', args=[1]),
            '/onlinecourse/course/1/result/'
        )


class ExamSubmissionAndGradingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='exam_taker',
            password='mypassword',
            first_name='John'
        )
        self.other_user = User.objects.create_user(
            username='intruder',
            password='mypassword',
            first_name='Sneaky'
        )
        self.course = Course.objects.create(name='Test Exam Course')
        self.lesson = Lesson.objects.create(course=self.course, title='Lesson A', order=1)

        # 4 Questions with 1 grade point each -> Total 4 points, pass threshold 70% (needs >= 3 correct)
        self.q1 = Question.objects.create(lesson=self.lesson, question_text='Q1', grade=1, order=1)
        self.q1_c1 = Choice.objects.create(question=self.q1, choice_text='Q1 C1 Correct', is_correct=True)
        self.q1_c2 = Choice.objects.create(question=self.q1, choice_text='Q1 C2 False', is_correct=False)

        self.q2 = Question.objects.create(lesson=self.lesson, question_text='Q2', grade=1, order=2)
        self.q2_c1 = Choice.objects.create(question=self.q2, choice_text='Q2 C1 Correct', is_correct=True)
        self.q2_c2 = Choice.objects.create(question=self.q2, choice_text='Q2 C2 False', is_correct=False)

        self.q3 = Question.objects.create(lesson=self.lesson, question_text='Q3', grade=1, order=3)
        self.q3_c1 = Choice.objects.create(question=self.q3, choice_text='Q3 C1 Correct', is_correct=True)
        self.q3_c2 = Choice.objects.create(question=self.q3, choice_text='Q3 C2 False', is_correct=False)

        self.q4 = Question.objects.create(lesson=self.lesson, question_text='Q4', grade=1, order=4)
        self.q4_c1 = Choice.objects.create(question=self.q4, choice_text='Q4 C1 Correct', is_correct=True)
        self.q4_c2 = Choice.objects.create(question=self.q4, choice_text='Q4 C2 False', is_correct=False)

    def test_successful_exam_submission_congratulations(self):
        """Submitting all correct answers should pass and display Congratulations."""
        self.client.login(username='exam_taker', password='mypassword')
        post_data = {
            f'choice_{self.q1.id}': self.q1_c1.id,
            f'choice_{self.q2.id}': self.q2_c1.id,
            f'choice_{self.q3.id}': self.q3_c1.id,
            f'choice_{self.q4.id}': self.q4_c1.id,
        }
        response = self.client.post(
            reverse('onlinecourse:submit', args=[self.course.id]),
            data=post_data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'onlinecourse/show_exam_result_bootstrap.html')
        self.assertTrue(response.context['passed'])
        self.assertEqual(response.context['correct_count'], 4)
        self.assertEqual(response.context['earned_score'], 4)
        self.assertEqual(response.context['percentage'], 100.0)
        self.assertContains(response, 'Congratulations')

    def test_failed_exam_submission(self):
        """Submitting 1 correct out of 4 (25%) fails passing threshold (70%)."""
        self.client.login(username='exam_taker', password='mypassword')
        post_data = {
            f'choice_{self.q1.id}': self.q1_c1.id,  # Correct (1)
            f'choice_{self.q2.id}': self.q2_c2.id,  # Wrong
            f'choice_{self.q3.id}': self.q3_c2.id,  # Wrong
            f'choice_{self.q4.id}': self.q4_c2.id,  # Wrong
        }
        response = self.client.post(
            reverse('onlinecourse:submit', args=[self.course.id]),
            data=post_data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['passed'])
        self.assertEqual(response.context['correct_count'], 1)
        self.assertEqual(response.context['percentage'], 25.0)
        self.assertContains(response, 'Exam Attempt Failed')
        self.assertNotContains(response, 'Congratulations')

    def test_unanswered_questions_handling(self):
        """Submitting only 2 out of 4 questions handles unanswered questions."""
        self.client.login(username='exam_taker', password='mypassword')
        post_data = {
            f'choice_{self.q1.id}': self.q1_c1.id,  # Correct
            f'choice_{self.q2.id}': self.q2_c1.id,  # Correct
            # q3 and q4 left unanswered
        }
        response = self.client.post(
            reverse('onlinecourse:submit', args=[self.course.id]),
            data=post_data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['correct_count'], 2)
        self.assertEqual(response.context['unanswered_count'], 2)
        self.assertEqual(response.context['earned_score'], 2)
        self.assertEqual(response.context['percentage'], 50.0)
        self.assertFalse(response.context['passed'])

    def test_invalid_choice_id_ignored(self):
        """Invalid choice IDs outside this exam are rejected and do not inflate score."""
        self.client.login(username='exam_taker', password='mypassword')
        post_data = {
            f'choice_{self.q1.id}': 999999,  # Nonexistent choice
            f'choice_{self.q2.id}': self.q2_c1.id,  # Correct
        }
        response = self.client.post(
            reverse('onlinecourse:submit', args=[self.course.id]),
            data=post_data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['correct_count'], 1)

    def test_duplicate_submission_does_not_inflate_score(self):
        """Re-submitting the exam updates answers rather than duplicating submissions."""
        self.client.login(username='exam_taker', password='mypassword')
        post_data = {
            f'choice_{self.q1.id}': self.q1_c1.id,
            f'choice_{self.q2.id}': self.q2_c1.id,
            f'choice_{self.q3.id}': self.q3_c1.id,
            f'choice_{self.q4.id}': self.q4_c1.id,
        }
        self.client.post(reverse('onlinecourse:submit', args=[self.course.id]), data=post_data)
        count_first = Submission.objects.filter(user=self.user, question__lesson__course=self.course).count()
        self.assertEqual(count_first, 4)

        # Submit again
        self.client.post(reverse('onlinecourse:submit', args=[self.course.id]), data=post_data)
        count_second = Submission.objects.filter(user=self.user, question__lesson__course=self.course).count()
        self.assertEqual(count_second, 4)  # Score and rows not inflated!

    def test_unauthorized_user_cannot_view_private_result(self):
        """Prevent user B from accessing user A's private exam result."""
        # Create submission for user A
        sub = Submission.objects.create(user=self.user, question=self.q1, choice=self.q1_c1)

        # Log in as user B
        self.client.login(username='intruder', password='mypassword')
        url = reverse('onlinecourse:show_exam_result', args=[self.course.id, sub.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_course_details_template_and_name(self):
        """Verify course template is named exactly 'course_details_bootstrap.html' with plural 'details'."""
        self.assertEqual(CourseDetailsView.template_name, 'onlinecourse/course_details_bootstrap.html')
        response = self.client.get(reverse('onlinecourse:course_details', args=[self.course.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'onlinecourse/course_details_bootstrap.html')
        self.assertContains(response, self.course.name)
        self.assertContains(response, self.lesson.title)
