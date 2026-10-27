from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import generic

from .models import Choice, Course, Enrollment, Lesson, Question, Submission


class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        courses = Course.objects.order_by('-total_enrollment')[:10]
        return courses


class CourseDetailsView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_details_bootstrap.html'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        lessons = course.lessons.all().prefetch_related('questions__choices')
        context['lessons'] = lessons
        
        # Check if current user is enrolled
        is_enrolled = False
        if self.request.user.is_authenticated:
            is_enrolled = Enrollment.objects.filter(
                user=self.request.user,
                course=course
            ).exists()
        context['is_enrolled'] = is_enrolled
        return context


@login_required
def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    enrollment, created = Enrollment.objects.get_or_create(
        user=request.user,
        course=course,
        defaults={'mode': 'audit'}
    )
    if created:
        course.total_enrollment += 1
        course.save()
        messages.success(request, f"You have enrolled in {course.name} successfully.")
    return redirect('onlinecourse:course_details', pk=course.id)


@login_required
def submit(request, course_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    course = get_object_or_404(Course, pk=course_id)
    enrollment, _ = Enrollment.objects.get_or_create(
        user=request.user,
        course=course,
        defaults={'mode': 'audit'}
    )

    questions = Question.objects.filter(lesson__course=course)
    if not questions.exists():
        questions = Question.objects.filter(courses=course)

    valid_choices = Choice.objects.filter(question__in=questions)
    valid_choice_map = {c.id: c for c in valid_choices}

    # Extract submitted choices from request.POST
    selected_choice_ids = set()

    for key, val in request.POST.items():
        if key.startswith('choice_') and val and str(val).isdigit():
            selected_choice_ids.add(int(val))

    for key in ['choice', 'choices', 'selected_choice', 'selected_choices']:
        for val in request.POST.getlist(key):
            if str(val).isdigit():
                selected_choice_ids.add(int(val))

    for key, val in request.POST.items():
        if key.isdigit() and val in ('on', '1', 'true', 'True'):
            selected_choice_ids.add(int(key))

    user_selected_choices = [
        valid_choice_map[cid] for cid in selected_choice_ids if cid in valid_choice_map
    ]

    last_submission = None

    for q in questions:
        q_choices = [c for c in user_selected_choices if c.question_id == q.id]
        if q_choices:
            chosen = q_choices[0]
            submission, _ = Submission.objects.update_or_create(
                user=request.user,
                question=q,
                defaults={
                    'choice': chosen,
                    'enrollment': enrollment,
                }
            )
            submission.choices.set([chosen])
            last_submission = submission
        else:
            Submission.objects.filter(user=request.user, question=q).delete()

    if last_submission:
        return redirect('onlinecourse:show_exam_result', course_id=course.id, submission_id=last_submission.id)
    return redirect('onlinecourse:show_exam_result_course', course_id=course.id)


@login_required
def show_exam_result(request, course_id, submission_id=None):
    course = get_object_or_404(Course, pk=course_id)
    questions = Question.objects.filter(lesson__course=course)
    if not questions.exists():
        questions = Question.objects.filter(courses=course)

    if submission_id is not None:
        target_sub = get_object_or_404(Submission, pk=submission_id)
        if target_sub.user != request.user and not request.user.is_staff:
            return HttpResponseForbidden("You are not authorized to view another user's private exam results.")

    user_submissions = Submission.objects.filter(user=request.user, question__in=questions)
    sub_map = {sub.question_id: sub for sub in user_submissions}

    total_questions = questions.count()
    correct_count = 0
    incorrect_count = 0
    unanswered_count = 0
    total_score = 0
    earned_score = 0
    results = []

    for q in questions:
        grade = q.grade if q.grade else 1
        total_score += grade
        sub = sub_map.get(q.id)
        selected_choice = sub.choice if sub else None

        is_correct = False
        if selected_choice:
            is_correct = selected_choice.is_correct
            if is_correct:
                correct_count += 1
                earned_score += grade
            else:
                incorrect_count += 1
        else:
            unanswered_count += 1

        results.append({
            'question': q,
            'selected_choice': selected_choice,
            'is_correct': is_correct,
            'choices': q.choices.all(),
            'grade': grade,
            'answered': selected_choice is not None
        })

    passing_threshold = 70.0
    percentage = (earned_score / total_score * 100.0) if total_score > 0 else 0.0
    passed = percentage >= passing_threshold

    if passed:
        message = f"Congratulations, {request.user.first_name or request.user.username}! You passed the exam with a score of {earned_score}/{total_score} ({percentage:.1f}%)."
    else:
        message = f"Unfortunately, you did not pass the exam. Your score is {earned_score}/{total_score} ({percentage:.1f}%). The passing threshold is {passing_threshold:.0f}%."

    context = {
        'course': course,
        'questions': questions,
        'results': results,
        'total_questions': total_questions,
        'correct_count': correct_count,
        'incorrect_count': incorrect_count,
        'unanswered_count': unanswered_count,
        'total_score': total_score,
        'earned_score': earned_score,
        'score': earned_score,
        'grade': earned_score,
        'percentage': round(percentage, 1),
        'passing_threshold': passing_threshold,
        'passed': passed,
        'message': message,
        'submission_id': submission_id,
        'user_submissions': user_submissions,
    }
    return render(request, 'onlinecourse/show_exam_result_bootstrap.html', context)


def login_request(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            messages.info(request, f"You are now logged in as {username}.")
            next_url = request.POST.get('next') or request.GET.get('next') or reverse('onlinecourse:index')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'onlinecourse/login.html')


def logout_request(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('onlinecourse:index')


def registration_request(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        password = request.POST.get('password')
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, 'onlinecourse/registration.html')
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password
        )
        login(request, user)
        messages.success(request, f"Account created for {username}!")
        return redirect('onlinecourse:index')
    return render(request, 'onlinecourse/registration.html')
