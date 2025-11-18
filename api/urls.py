from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # Authentication
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    path('auth/login/', views.UserLoginView.as_view(), name='login'),
    path('auth/logout/', views.UserLogoutView.as_view(), name='logout'),
    path('auth/refresh/', views.refresh_token_view, name='refresh_token'),

    # User
    path('user/me/', views.user_me_view, name='user_me'),
    path('user/update/', views.UserProfileView.as_view(), name='user_update'),

    # AI
    path('ai/advice/', views.AINutritionAdviceView.as_view(), name='ai_advice'),

    # Meals (FIXED)
    path('meals/', views.MealListCreateView.as_view(), name='meals'),
    path('meals/today/', views.TodayMealsView.as_view(), name='meals_today'),
    path('meals/weekly/', views.WeeklyMealsView.as_view(), name='meals_weekly'),
    path('meals/<int:pk>/', views.MealDetailView.as_view(), name='meal_detail'),

    # Schedule (FIXED)
    path('schedule/', views.ScheduleListCreateView.as_view(), name='schedule_list'),
    path('schedule/<int:pk>/', views.ScheduleDetailView.as_view(), name='schedule_detail'),

    # Settings
    path('settings/', views.AppSettingsView.as_view(), name='settings'),

    # Dashboard
    path('stats/', views.DashboardStatsView.as_view(), name='dashboard_stats'),
]
