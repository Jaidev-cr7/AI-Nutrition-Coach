from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import UserProfile, Meal, ScheduleItem, AppSettings, AIAnalysisCache


# ================================================================
#   USER (minimal, but used inside profile serializer)
# ================================================================
class NestedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


# ================================================================
#   USER PROFILE SERIALIZER
# ================================================================
class UserProfileSerializer(serializers.ModelSerializer):
    user = NestedUserSerializer(read_only=True)
    dietary_preferences_list = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )

    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'age', 'height', 'weight', 'gender', 'activity_level',
            'daily_calorie_goal', 'dietary_preferences', 'dietary_preferences_list',
            'allergies', 'medical_conditions', 'location', 'updated_at'
        ]
        read_only_fields = ['id', 'updated_at']

    # Convert list → string before saving
    def validate_dietary_preferences_list(self, value):
        return ', '.join(value) if value else ''

    # Convert string → list when returning to frontend
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.dietary_preferences:
            data['dietary_preferences_list'] = [
                pref.strip() for pref in instance.dietary_preferences.split(',')
                if pref.strip()
            ]
        else:
            data['dietary_preferences_list'] = []
        return data


# ================================================================
#   USER REGISTRATION SERIALIZER (FULL FIX)
# ================================================================
class UserRegistrationSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'profile'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        # Create user
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        # Create profile (with provided fields)
        UserProfile.objects.create(user=user, **profile_data)

        # Create default settings
        AppSettings.objects.create(user=user)

        return user


# ================================================================
#   LOGIN SERIALIZER
# ================================================================
class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


# ================================================================
#   MEAL SERIALIZER
# ================================================================
class MealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meal
        fields = [
            'id', 'name', 'meal_type', 'calories', 'protein', 'carbs', 'fats',
            'portion_size', 'notes', 'time', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ================================================================
#   SCHEDULE SERIALIZER
# ================================================================
class ScheduleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleItem
        fields = [
            'id', 'title', 'schedule_type', 'datetime', 'notes', 'is_completed',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ================================================================
#   SETTINGS SERIALIZER
# ================================================================
class AppSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppSettings
        fields = [
            'id', 'dark_mode', 'notifications', 'units', 'reminder_time',
            'weekly_goal', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ================================================================
#   AI CACHE SERIALIZER
# ================================================================
class AIAnalysisCacheSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIAnalysisCache
        fields = ['id', 'meal_description', 'analysis_data', 'created_at', 'expires_at']
        read_only_fields = ['id', 'created_at', 'expires_at']


# ================================================================
#   AI RESPONSE SERIALIZERS
# ================================================================
class AIAdviceRequestSerializer(serializers.Serializer):
    meal = serializers.CharField(max_length=500)


class AIAdviceResponseSerializer(serializers.Serializer):
    calories = serializers.IntegerField()
    protein = serializers.CharField()
    carbs = serializers.CharField()
    fat = serializers.CharField()
    health_score = serializers.IntegerField(min_value=1, max_value=10)
    advice = serializers.CharField()


# ================================================================
#   DASHBOARD STATS SERIALIZER
# ================================================================
class DashboardStatsSerializer(serializers.Serializer):
    total_calories_today = serializers.IntegerField()
    protein_today = serializers.FloatField()
    carbs_today = serializers.FloatField()
    fats_today = serializers.FloatField()
    meals_today = serializers.IntegerField()
    weekly_average_calories = serializers.FloatField()
    calories_goal_progress = serializers.FloatField()
    hydration_glasses = serializers.IntegerField(default=0)
    active_minutes = serializers.IntegerField(default=0)
    sleep_hours = serializers.FloatField(default=0)
    heart_rate = serializers.IntegerField(default=0)
