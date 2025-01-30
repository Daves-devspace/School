from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views
from django.contrib.auth import views as auth_views

from .views import CustomPasswordResetView, CustomPasswordResetDoneView, CustomPasswordResetConfirmView, \
    CustomPasswordResetCompleteView

urlpatterns = [

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # Login
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Refresh token
    path('', views.home, name='home'),
    path('teacher-dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('director-dashboard/', views.director_dashboard, name='director_dashboard'),

    path('signup/', views.signup, name='signup'),
    path('login', views.login_user, name='login'),
    path('sign-in', views.login_form, name='login_form'),
    path('logout/', views.logout_user, name='logout'),
    # path('login_form', views.login_form, name='login_form'),
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),

    path('password-reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('merryland', views.website_page, name='merry-land'),
    path('settings', views.settings_page, name='settings'),



]
