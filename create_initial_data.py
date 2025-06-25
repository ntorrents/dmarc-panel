#!/usr/bin/env python
"""
Script to create initial data for the DMARC Panel
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import User, Empresa, Role

def create_initial_data():
    print("Creating initial data...")
    
    # Create roles
    roles_data = [
        {
            'nombre': 'super_admin',
            'descripcion': 'Super administrator with full system access',
            'permisos': {
                'can_manage_all_companies': True,
                'can_view_audit_logs': True,
                'can_manage_system_settings': True,
                'can_manage_users': True,
                'can_manage_domains': True,
            }
        },
        {
            'nombre': 'company_admin',
            'descripcion': 'Company administrator with full company access',
            'permisos': {
                'can_manage_company_users': True,
                'can_manage_company_domains': True,
                'can_view_company_audit_logs': True,
                'can_edit_company_settings': True,
            }
        },
        {
            'nombre': 'config_user',
            'descripcion': 'User who can edit configurations but with limited scope',
            'permisos': {
                'can_edit_domains': True,
                'can_manage_dns_records': True,
                'can_view_company_data': True,
            }
        },
        {
            'nombre': 'read_only',
            'descripcion': 'Read-only user with view permissions only',
            'permisos': {
                'can_view_company_data': True,
            }
        },
    ]
    
    for role_data in roles_data:
        role, created = Role.objects.get_or_create(
            nombre=role_data['nombre'],
            defaults={
                'descripcion': role_data['descripcion'],
                'permisos': role_data['permisos']
            }
        )
        if created:
            print(f"✓ Created role: {role.get_nombre_display()}")
        else:
            print(f"- Role already exists: {role.get_nombre_display()}")
    
    # Create super admin user
    super_admin_role = Role.objects.get(nombre='super_admin')
    
    if not User.objects.filter(email='admin@dmarcpanel.com').exists():
        super_user = User.objects.create_user(
            username='superadmin',
            email='admin@dmarcpanel.com',
            password='admin123',
            first_name='Super',
            last_name='Admin',
            role=super_admin_role,
            is_staff=True,
            is_superuser=True
        )
        print(f"✓ Created super admin user: {super_user.email}")
        print("  Username: superadmin")
        print("  Email: admin@dmarcpanel.com")
        print("  Password: admin123")
    else:
        print("- Super admin user already exists")
    
    # Create sample company
    sample_company, created = Empresa.objects.get_or_create(
        nombre='Sample Company',
        defaults={
            'direccion': '123 Main St, Sample City, SC 12345'
        }
    )
    if created:
        print(f"✓ Created sample company: {sample_company.nombre}")
    else:
        print(f"- Sample company already exists: {sample_company.nombre}")
    
    # Create sample company admin
    company_admin_role = Role.objects.get(nombre='company_admin')
    
    if not User.objects.filter(email='admin@samplecompany.com').exists():
        company_admin = User.objects.create_user(
            username='companyadmin',
            email='admin@samplecompany.com',
            password='company123',
            first_name='Company',
            last_name='Admin',
            empresa=sample_company,
            role=company_admin_role
        )
        print(f"✓ Created company admin user: {company_admin.email}")
        print("  Username: companyadmin")
        print("  Email: admin@samplecompany.com")
        print("  Password: company123")
    else:
        print("- Company admin user already exists")
    
    # Create sample read-only user
    read_only_role = Role.objects.get(nombre='read_only')
    
    if not User.objects.filter(email='user@samplecompany.com').exists():
        read_only_user = User.objects.create_user(
            username='readonlyuser',
            email='user@samplecompany.com',
            password='user123',
            first_name='Read Only',
            last_name='User',
            empresa=sample_company,
            role=read_only_role
        )
        print(f"✓ Created read-only user: {read_only_user.email}")
        print("  Username: readonlyuser")
        print("  Email: user@samplecompany.com")
        print("  Password: user123")
    else:
        print("- Read-only user already exists")
    
    print("\n" + "="*50)
    print("Initial data creation completed!")
    print("="*50)
    print("\nYou can now log in with any of these accounts:")
    print("\n1. Super Admin:")
    print("   Email: admin@dmarcpanel.com")
    print("   Password: admin123")
    print("\n2. Company Admin:")
    print("   Email: admin@samplecompany.com")
    print("   Password: company123")
    print("\n3. Read-Only User:")
    print("   Email: user@samplecompany.com")
    print("   Password: user123")

if __name__ == '__main__':
    create_initial_data()