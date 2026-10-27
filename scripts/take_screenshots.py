import os
import sys
import time
import shutil
import urllib.request
import subprocess
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from onlinecourse.models import Course, Question, Submission, Enrollment

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
User = get_user_model()


def setup_submission():
    student_user = User.objects.get(username='student1')
    course = Course.objects.first()
    enrollment, _ = Enrollment.objects.get_or_create(user=student_user, course=course)
    questions = Question.objects.filter(lesson__course=course)

    last_sub = None
    for q in questions:
        correct_choice = q.choices.filter(is_correct=True).first()
        sub, _ = Submission.objects.update_or_create(
            user=student_user,
            question=q,
            defaults={'choice': correct_choice, 'enrollment': enrollment}
        )
        sub.choices.set([correct_choice])
        last_sub = sub
    return course.id, last_sub.id


def wait_for_server(url, timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status in (200, 302):
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def main():
    course_id, submission_id = setup_submission()
    print(f"Verified submission {submission_id} for Course {course_id}")

    temp_dir = Path(r"C:\Users\digit\AppData\Local\Temp")
    temp_admin_shot = temp_dir / "03-admin-site.png"
    temp_final_shot = temp_dir / "07-final.png"

    # Start Django runserver
    server_proc = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", "127.0.0.1:8000", "--noreload"],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    print("Started Django runserver on 127.0.0.1:8000")

    try:
        if not wait_for_server("http://127.0.0.1:8000/"):
            print("Server failed to respond in time.")
            return

        print("Server is responsive!")

        # 1. Capture Admin Site Screenshot
        admin_url = "http://127.0.0.1:8000/auto-admin/"
        print(f"Capturing Admin screenshot from {admin_url}...")
        r1 = subprocess.run([
            CHROME_PATH,
            "--headless=new",
            "--disable-gpu",
            "--window-size=1440,950",
            f"--screenshot={temp_admin_shot}",
            admin_url
        ], capture_output=True, text=True)
        print(f"Admin capture exit code: {r1.returncode}, stderr: {r1.stderr}")

        # 2. Capture Final Exam Result Screenshot
        student_url = f"http://127.0.0.1:8000/auto-student/{course_id}/{submission_id}/"
        print(f"Capturing Final Result screenshot from {student_url}...")
        r2 = subprocess.run([
            CHROME_PATH,
            "--headless=new",
            "--disable-gpu",
            "--window-size=1440,950",
            f"--screenshot={temp_final_shot}",
            student_url
        ], capture_output=True, text=True)
        print(f"Final capture exit code: {r2.returncode}, stderr: {r2.stderr}")

        # Convert/save to JPEG files in project directory
        out_admin = PROJECT_ROOT / "03-admin-site.jpeg"
        out_final = PROJECT_ROOT / "07-final.jpeg"

        if temp_admin_shot.exists():
            img_admin = Image.open(temp_admin_shot)
            img_admin.convert("RGB").save(out_admin, "JPEG", quality=95)
            print(f"SUCCESS: Saved {out_admin} | Size: {img_admin.size} | Format: JPEG")

        if temp_final_shot.exists():
            img_final = Image.open(temp_final_shot)
            img_final.convert("RGB").save(out_final, "JPEG", quality=95)
            print(f"SUCCESS: Saved {out_final} | Size: {img_final.size} | Format: JPEG")

    finally:
        server_proc.terminate()
        try:
            server_proc.wait(timeout=3)
        except Exception:
            server_proc.kill()
        print("Server stopped.")


if __name__ == '__main__':
    main()
