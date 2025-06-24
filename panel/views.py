# panel/views.py
from rest_framework import viewsets, permissions
from .models import Cliente, Dominio, DNSRecord
from .serializers import ClienteSerializer, DominioSerializer, DNSRecordSerializer

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [permissions.IsAuthenticated]

class DominioViewSet(viewsets.ModelViewSet):
    queryset = Dominio.objects.all()
    serializer_class = DominioSerializer
    permission_classes = [permissions.IsAuthenticated]

class DNSRecordViewSet(viewsets.ModelViewSet):
    queryset = DNSRecord.objects.all()
    serializer_class = DNSRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
