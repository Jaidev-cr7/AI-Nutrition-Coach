from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    age = models.PositiveIntegerField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True, help_text="Height in cm")
    weight = models.FloatField(null=True, blank=True, help_text="Weight in kg")
    gender = models.CharField(
        max_length=10,
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        default='other'
    )
    activity_level = models.PositiveIntegerField(
        default=3,
        help_text="Activity level from 1 (sedentary) to 5 (very active)"
    )
    daily_calorie_goal = models.PositiveIntegerField(default=2000)
    dietary_preferences = models.TextField(blank=True, help_text="Comma-separated dietary preferences")
    allergies = models.TextField(blank=True, help_text="Comma-separated allergies")
    medical_conditions = models.TextField(blank=True, help_text="Comma-separated medical conditions")
    location = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    class Meta:
        db_table = 'user_profiles'


class Meal(models.Model):
    MEAL_TYPES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meals')
    name = models.CharField(max_length=255)
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES)
    calories = models.PositiveIntegerField(null=True, blank=True)
    protein = models.FloatField(null=True, blank=True, help_text="Protein in grams")
    carbs = models.FloatField(null=True, blank=True, help_text="Carbs in grams")
    fats = models.FloatField(null=True, blank=True, help_text="Fats in grams")
    portion_size = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    time = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s {self.meal_type}: {self.name}"

    class Meta:
        db_table = 'meals'
        ordering = ['-time']


class ScheduleItem(models.Model):
    SCHEDULE_TYPES = [
        ('meal', 'Meal'),
        ('workout', 'Workout'),
        ('reminder', 'Reminder'),
        ('appointment', 'Appointment'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='schedule_items')
    title = models.CharField(max_length=255)
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_TYPES)
    datetime = models.DateTimeField()
    notes = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s {self.schedule_type}: {self.title}"

    class Meta:
        db_table = 'schedule_items'
        ordering = ['datetime']


class AppSettings(models.Model):
    UNITS_CHOICES = [
        ('metric', 'Metric'),
        ('imperial', 'Imperial'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    dark_mode = models.BooleanField(default=False)
    notifications = models.BooleanField(default=True)
    units = models.CharField(max_length=10, choices=UNITS_CHOICES, default='metric')
    reminder_time = models.TimeField(null=True, blank=True, help_text="Daily reminder time")
    weekly_goal = models.PositiveIntegerField(default=7, help_text="Weekly workout goal")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Settings"

    class Meta:
        db_table = 'app_settings'


class AIAnalysisCache(models.Model):
    meal_description = models.CharField(max_length=500, unique=True)
    analysis_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"Cache for: {self.meal_description[:50]}..."

    class Meta:
        db_table = 'ai_analysis_cache'
        indexes = [
            models.Index(fields=['meal_description']),
            models.Index(fields=['expires_at']),
        ]
