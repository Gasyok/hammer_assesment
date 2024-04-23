from django.http import JsonResponse
from django.contrib.auth import login
from django.core.cache import cache

from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication


import random
import time
import string

from .serializers import UserSerializer, PhoneSerializer, PhoneVerifySerializer
from .serializers import ActivateUserSerializer
from .models import User


class RequestCodeView(APIView):

    def post(self, request):
        serializer = PhoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        phone_number = data['phone_number']
        verify_code = self.generate_code(phone_number)

        return JsonResponse(
            status=200,
            data={
                "message": "Verify code sent to your device",
                "code": verify_code
            }
        )

    def generate_code(self, phone):
        time.sleep(random.uniform(1, 2))
        code = ''.join(random.choices('0123456789', k=4))
        cache.set(phone, code, timeout=300)
        return code


class VerifyCodeView(APIView):

    def post(self, request):
        serializer = PhoneVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        phone_number = data['phone_number']
        code = data['code']

        if code == cache.get(phone_number):
            # user, created = User.objects.get_or_create(
            #     phone_number=phone_number)

            user = User.objects.filter(phone_number=phone_number).first()

            # print(user)
            # print(created)

            if not user:
                invite_code = self.generate_invite_code()
                user = User.objects.create_user(
                    phone_number=phone_number, invite_code=invite_code)
                user.save()

            login(request, user)

            return JsonResponse(
                status=200,
                data={
                    "message": "Verification Success"
                }
            )

        return JsonResponse(
            status=400,
            data={
                "message": "Invalid code",
                "code": cache.get(phone_number)
            }
        )

    def generate_invite_code(self):
        characters = string.ascii_letters + string.digits
        invite_code = ''.join(random.choices(characters, k=6))
        return invite_code


class ListUserView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class ActivateCodeView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = ActivateUserSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            invite_code = serializer.validated_data.get('invite_code')

            user_obj = User.objects.get(invite_code=invite_code)
            user.activated_from = user_obj
            user.save()

            return Response({'message': 'Activated'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message': 'Вы аутентифицированы'})
