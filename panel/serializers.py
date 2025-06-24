# panel/serializers.py
from rest_framework import serializers
from .models import Cliente, Dominio, DNSRecord

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'

class DominioSerializer(serializers.ModelSerializer):
    cliente = ClienteSerializer(read_only=True)

    class Meta:
        model = Dominio
        fields = '__all__'

class DNSRecordSerializer(serializers.ModelSerializer):
    dominio = DominioSerializer(read_only=True)

    class Meta:
        model = DNSRecord
        fields = '__all__'
