from rest_framework import status, permissions, generics, throttling
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum, Avg
from datetime import timedelta
import logging

from .models import UserProfile, Meal, ScheduleItem, AppSettings
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    MealSerializer, ScheduleItemSerializer, AppSettingsSerializer,
    AIAdviceRequestSerializer, AIAdviceResponseSerializer, DashboardStatsSerializer
)
from .services.ai_service import ai_service

logger = logging.getLogger(__name__)


# ================================================================
#   USER REGISTRATION  (NOW RETURNS FULL PROFILE)
# ================================================================
class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Create tokens
        refresh = RefreshToken.for_user(user)

        # Always return FULL profile
        profile = user.profile

        return Response({
            "user": UserProfileSerializer(profile).data,
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


# ================================================================
#   LOGIN (NOW RETURNS FULL PROFILE)
# ================================================================
class UserLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"]
        )

        if user is None:
            return Response({"error": "Invalid credentials"}, status=401)

        refresh = RefreshToken.for_user(user)

        # Always return full profile
        profile, created = UserProfile.objects.get_or_create(user=user)

        return Response({
            "user": UserProfileSerializer(profile).data,
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            }
        })


# ================================================================
#   LOGOUT
# ================================================================
class UserLogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                RefreshToken(refresh_token).blacklist()
            return Response({"message": "Logged out"})
        except Exception:
            return Response({"error": "Invalid token"}, status=400)


# ================================================================
#   PROFILE GET + UPDATE
# ================================================================
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Always ensure the profile exists
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


# ================================================================
#   GET CURRENT USER WITH PROFILE
# ================================================================
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def user_me_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    return Response(UserProfileSerializer(profile).data)


# ================================================================
#   MEALS
# ================================================================
class MealListCreateView(generics.ListCreateAPIView):
    serializer_class = MealSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Meal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MealDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MealSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Meal.objects.filter(user=self.request.user)


class TodayMealsView(generics.ListAPIView):
    serializer_class = MealSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        today = timezone.now().date()
        return Meal.objects.filter(
            user=self.request.user,
            time__date=today
        ).order_by("-time")


class WeeklyMealsView(generics.ListAPIView):
    serializer_class = MealSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        return Meal.objects.filter(
            user=self.request.user,
            time__date__gte=week_ago
        ).order_by("-time")


# ================================================================
#   SCHEDULE
# ================================================================
class ScheduleListCreateView(generics.ListCreateAPIView):
    serializer_class = ScheduleItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ScheduleItem.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ScheduleItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ScheduleItem.objects.filter(user=self.request.user)


# ================================================================
#   SETTINGS
# ================================================================
class AppSettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = AppSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        settings, created = AppSettings.objects.get_or_create(user=self.request.user)
        return settings


# ================================================================
#   AI ADVICE
# ================================================================
class AINutritionAdviceView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [throttling.UserRateThrottle]
    throttle_scope = "ai"

    def post(self, request):
        serializer = AIAdviceRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            analysis = ai_service.get_nutrition_advice(serializer.validated_data["meal"])
            response = AIAdviceResponseSerializer(data=analysis)
            response.is_valid(raise_exception=True)
            return Response(response.data)

        except Exception as e:
            logger.error(f"AI error: {e}")
            return Response({"error": "AI failed"}, status=500)


# ================================================================
#   DASHBOARD
# ================================================================
class DashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)

        today_meals = Meal.objects.filter(user=user, time__date=today)
        weekly_meals = Meal.objects.filter(user=user, time__date__gte=week_ago)

        totals = today_meals.aggregate(
            total_calories=Sum("calories"),
            protein=Sum("protein"),
            carbs=Sum("carbs"),
            fats=Sum("fats"),
        )

        weekly_avg = weekly_meals.aggregate(avg_calories=Avg("calories"))

        try:
            daily_goal = user.profile.daily_calorie_goal
        except UserProfile.DoesNotExist:
            daily_goal = 2000

        calories_today = totals["total_calories"] or 0
        progress = (calories_today / daily_goal * 100) if daily_goal > 0 else 0

        stats = {
            "total_calories_today": calories_today,
            "protein_today": float(totals["protein"] or 0),
            "carbs_today": float(totals["carbs"] or 0),
            "fats_today": float(totals["fats"] or 0),
            "meals_today": today_meals.count(),
            "weekly_average_calories": float(weekly_avg["avg_calories"] or 0),
            "calories_goal_progress": round(progress, 1),
            "hydration_glasses": 6,
            "active_minutes": 45,
            "sleep_hours": 7.5,
            "heart_rate": 72,
        }

        serializer = DashboardStatsSerializer(data=stats)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
# ================================================================
#   REFRESH TOKEN (NECESSARY FOR AUTH)
# ================================================================
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def refresh_token_view(request):
    """Refresh JWT access token"""
    try:
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token required"}, status=400)

        token = RefreshToken(refresh_token)
        access = str(token.access_token)

        return Response({"access": access})

    except Exception:
        return Response({"error": "Invalid refresh token"}, status=401)
