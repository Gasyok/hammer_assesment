from django.http import JsonResponse
from django.contrib.auth import login, authenticate
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt


from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from rest_framework.authtoken.models import Token


import random
import time
import string

from .serializers import UserSerializer, PhoneSerializer, PhoneVerifySerializer
from .serializers import ActivateUserSerializer
from .models import User


def generate_code(phone):
    time.sleep(random.uniform(1, 2))
    code = ''.join(random.choices('0123456789', k=4))
    cache.set(phone, code, timeout=300)
    return code


@csrf_exempt
@api_view(["POST"])
def request_code_view(request):
    """
    Sending POST and in response you will have SMS CODE
    """
    serializer = PhoneSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    phone_number = data['phone_number']
    verify_code = generate_code(phone_number)

    return JsonResponse(
        status=200,
        data={
            "message": "Verify code sent to your device",
            "code": verify_code
        }
    )


class VerifyCodeView(APIView):
    """
    Imitating verifying your SMS code
    """

    @csrf_exempt
    def post(self, request):
        """
        You need to specify CODE
        """
        serializer = PhoneVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        phone_number = data['phone_number']
        code = data['code']

        if code == cache.get(phone_number):
            user = User.objects.filter(phone_number=phone_number).first()
            if not user:
                invite_code = self.generate_invite_code()
                user = User.objects.create_user(
                    phone_number=phone_number, invite_code=invite_code)
                user.save()

            token, _ = Token.objects.get_or_create(user=user)
            return JsonResponse({'token': str(token)}, status=200)
        else:
            return JsonResponse({'message': 'Invalid code'}, status=400)

    def generate_invite_code(self):
        characters = string.ascii_letters + string.digits
        invite_code = ''.join(random.choices(characters, k=6))
        return invite_code


class UserProfileView(APIView):
    """
    Handling GET and PATCH requests. For PATCH you need to specify invite code
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Returns user's profile information
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        """
        You need to specify actual invite code
        """
        serializer = ActivateUserSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            invite_code = serializer.validated_data['invite_code']

            user_obj = User.objects.get(invite_code=invite_code)
            user.activated_from = user_obj
            user.save()

            return JsonResponse({'message': 'Activated'}, status=200)
        return JsonResponse(serializer.errors, status=400)
