from django.urls import path

from . import views


urlpatterns = [
    path('auth', views.RequestCodeView.as_view()),
    path('auth/verify', views.VerifyCodeView.as_view()),
    path('', views.ListUserView.as_view()),
    path('<int:id>', views.UserProfileView.as_view()),
    path('activate', views.ActivateCodeView.as_view())
]
