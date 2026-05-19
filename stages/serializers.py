from rest_framework import serializers
from .models import Stage
from accounts.serializers import UserSerializer


# =========================================================
# READ SERIALIZER
# =========================================================

class StageSerializer(serializers.ModelSerializer):

    chairman = UserSerializer(read_only=True)

    secretary = UserSerializer(read_only=True)

    defense = UserSerializer(read_only=True)

    class Meta:

        model = Stage

        fields = '__all__'


# =========================================================
# CREATE / UPDATE SERIALIZER
# =========================================================

class StageCreateUpdateSerializer(serializers.ModelSerializer):

    class Meta:

        model = Stage

        fields = '__all__'