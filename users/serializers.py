from django.core.cache import cache

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

import re

from .models import User


class PhoneSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    def validate_phone_number(self, phone):
        phone = re.sub(r'[^\d+]', '', phone)

        if phone.startswith('8'):
            phone = '+7' + phone[1:]

        if len(phone) != 12:
            raise serializers.ValidationError(
                "Format error, CIS region phones only")

        if not phone.startswith('+7'):
            raise serializers.ValidationError(
                "Must start with +7 or 8")

        return phone


class PhoneVerifySerializer(serializers.Serializer):
    code = serializers.CharField(max_length=4)
    phone_number = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    def validate_phone_number(self, phone):
        phone = re.sub(r'[^\d+]', '', phone)

        if phone.startswith('8'):
            phone = '+7' + phone[1:]

        if len(phone) != 12:
            raise serializers.ValidationError(
                "Format error, CIS region phones only")

        if not phone.startswith('+7'):
            raise serializers.ValidationError(
                "Must start with +7 or 8")

        return phone

    def validate_code(self, code):
        if len(code) != 4:
            raise serializers.ValidationError("Error with format code")
        return code

    def validate(self, attrs):
        phone_number = attrs['phone_number']
        code = attrs['code']
        if not self.verify_verification_code(phone_number, code):
            raise serializers.ValidationError(
                f"Invalid code, cached code {cache.get(phone_number)}")
        return attrs

    def verify_verification_code(self, phone_number, code):
        return code == cache.get(phone_number)


class ActivateUserSerializer(serializers.Serializer):
    invite_code = serializers.CharField(max_length=6)

    def validate_invite_code(self, value):
        if len(value) != 6:
            raise serializers.ValidationError("Format error")
        try:
            user = User.objects.get(invite_code=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "Invalid code")

        if user == self.context['request'].user:
            raise serializers.ValidationError(
                "Invalid code")

        if self.context['request'].user.activated_from:
            raise serializers.ValidationError(
                "You already activated"
            )

        return value


class UserSerializer(serializers.ModelSerializer):
    activated_by = serializers.SerializerMethodField()
    activated_from = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'phone_number', 'invite_code',
                  'activated_from', 'activated_by']

    def get_activated_by(self, obj):
        activated_by_users = obj.activated_by.all()
        return [user.phone_number for user in activated_by_users]

    def get_activated_from(self, obj):
        activated_from_user = obj.activated_from
        if activated_from_user:
            return activated_from_user.invite_code
        return None
