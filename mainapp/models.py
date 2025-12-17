from django.db import models, transaction
from django.contrib.auth.models import AbstractUser, BaseUserManager
from datetime import date

class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)
    

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()
    def __str__(self):
        return self.email

class Teacher(models.Model):
    TEACHER_TYPE_CHOICES = [
        ('admin', 'Admin'),
        ('principal', 'Principal'),
        ('class_teacher', 'Class Teacher'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TEACHER_TYPE_CHOICES)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    date_of_birth = models.DateField()
    school = models.CharField(max_length=100)
    school_id = models.CharField(max_length=100)
    class_assigned = models.CharField(max_length=50, null=True, blank=True)
    address = models.TextField()
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    mfa_enabled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.type})"


class EmailOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="email_otps")
    otp_encrypted = models.TextField()
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OTP for {self.user.email}"


class School(models.Model):
    name = models.CharField(max_length=100)
    school_type = models.CharField(max_length=50)
    board = models.CharField(max_length=50)
    medium = models.CharField(max_length=50)
    registration_number = models.CharField(max_length=50, unique=True)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.name}"
    

class Student(models.Model):
    full_name = models.CharField(max_length=100)
    student_id = models.CharField(max_length=50, unique=True)
    email = models.EmailField()
    school = models.CharField(max_length=100)
    school_id = models.CharField(max_length=100)
    class_assigned = models.CharField(max_length=20)
    phone = models.CharField(max_length=15)
    attendance_percentage = models.FloatField(default=0.0)
    parental_education = models.IntegerField()
    study_hours = models.IntegerField()
    failures = models.IntegerField()
    extracurricular = models.IntegerField()
    participation = models.IntegerField()
    rating = models.IntegerField()
    discipline = models.IntegerField()
    late_submissions = models.IntegerField()
    prev_grade1 = models.FloatField()
    prev_grade2 = models.FloatField()
    final_grade = models.FloatField()

    def __str__(self):
        return f"{self.full_name} - {self.student_id}"


class Class(models.Model):
    school = models.CharField(max_length=100)
    school_id = models.CharField(max_length=100)
    class_number = models.CharField(max_length=10, unique=True)
    total_working_days = models.IntegerField(default=0)
    threshold = models.IntegerField()
    start_date = models.DateField(default=date.today)

    def update_total_working_days(self):
        class_working_day = ClassWorkingDay.objects.filter(
            school_id=self.school_id,
            class_number=self.class_number
        ).first()

        total_working_days = 0

        if class_working_day:
            working_days_dict = class_working_day.working_days
            for date_str, is_working in working_days_dict.items():
                try:
                    day = date.fromisoformat(date_str)
                except ValueError:
                    continue

                if self.start_date <= day <= date.today() and is_working is True:
                    total_working_days += 1

        self.total_working_days = total_working_days
        self.save()

    def __str__(self):
        return f"Class {self.class_number} - {self.total_working_days} Working Days"


class ClassWorkingDay(models.Model):
    school = models.CharField(max_length=100)
    school_id = models.CharField(max_length=100)
    class_number = models.CharField(max_length=10)
    working_days = models.JSONField(default=dict)

    @property
    def total_working_days(self):
        return sum(1 for day in self.working_days.values() if day is True)

    class Meta:
        unique_together = ('school_id', 'class_number')
        indexes = [
            models.Index(fields=['school_id', 'class_number']),
        ]

    def __str__(self):
        return f"{self.school} - Class {self.class_number} - {self.total_working_days} Working Days"


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('not_marked', 'Not Marked'),
    ]

    school = models.CharField(max_length=100)
    school_id = models.CharField(max_length=100)
    class_number = models.CharField(max_length=20)
    date = models.DateField()

    students = models.JSONField(default=list)

    class Meta:
        unique_together = ('school_id', 'class_number', 'date')
        indexes = [
            models.Index(fields=['school_id', 'class_number', 'date']),
        ]
        verbose_name_plural = "Class Attendances"

    def __str__(self):
        return f"{self.school} - Class {self.class_number} - {self.date}"

    def save(self, *args, **kwargs):
        with transaction.atomic():
            attendance_records = Attendance.objects.filter(
                school_id=self.school_id,
                class_number=self.class_number
            )

            present_count_map = {}
            for record in attendance_records:
                for s in record.students:
                    if s['status'] == 'present':
                        sid = s['student_id']
                        present_count_map[sid] = present_count_map.get(sid, 0) + 1

            # Get total working days for percentage calc
            total_days = sum(
                1 for entry in ClassWorkingDay.objects.filter(
                    school_id=self.school_id,
                    class_number=self.class_number
                )
                for day in entry.working_days.values() if day is True
            )

            # Process each student
            for student in self.students:
                student.setdefault('status', 'not_marked')
                sid = student['student_id']
                student['present_count'] = present_count_map.get(sid, 0)
                student['percentage'] = (student['present_count'] / total_days * 100) if total_days else 0.0

                self._sync_to_student_model(student)

            super().save(*args, **kwargs)

    def _calculate_present_days(self, student_id):
        present_days = 0
        records = Attendance.objects.filter(
            school_id=self.school_id,
            class_number=self.class_number
        )

        for record in records:
            for s in record.students:
                if s['student_id'] == student_id and s.get('status') == 'present':
                    present_days += 1
        return present_days

    def _sync_to_student_model(self, student_data):
        try:
            student = Student.objects.get(student_id=student_data['student_id'])
            student.attendance_percentage = student_data['percentage']
            student.save()
        except Student.DoesNotExist:
            pass
        
