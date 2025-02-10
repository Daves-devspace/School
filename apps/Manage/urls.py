from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views
from django.contrib.auth import views as auth_views

from .views import CustomPasswordResetView, CustomPasswordResetDoneView, CustomPasswordResetConfirmView, \
    CustomPasswordResetCompleteView, SettingsView, teacher_dashboard

urlpatterns = [

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # Login
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Refresh token
    path('dashboard/', views.home, name='home'),
    path('', views.website_page, name='merry-land'),
    path('teacher-dashboard/', teacher_dashboard.as_view(), name='teacher_dashboard'),
    path('director-dashboard/', views.director_dashboard, name='director_dashboard'),
    path('inbox/', views.notifications_inbox_view, name='inbox_page'),
    path('get-appointment/<int:appointment_id>/', views.get_appointment_details, name='get_appointment_details'),
    path('reply-appointment/<int:appointment_id>/', views.reply_appointment, name='reply_appointment'),

    path('settings/', SettingsView.as_view(), name='settings_page'),

    path('signup/', views.signup, name='signup'),
    path('login', views.login_user, name='login'),
    path('sign-in', views.login_form, name='login_form'),
    path('logout/', views.logout_user, name='logout'),
    # path('login_form', views.login_form, name='login_form'),

    path('add_user/', views.add_user, name='add_user'),
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),

    path('password-reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # path('settings', views.settings_page, name='settings'),

]
