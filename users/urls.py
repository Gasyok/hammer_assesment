from django.urls import path

from . import views


urlpatterns = [
    path('auth', views.request_code_view),
    path('auth/verify', views.VerifyCodeView.as_view()),
    path('users', views.ListUserView.as_view()),
    path('user-profile', views.UserProfileView.as_view()),
]
