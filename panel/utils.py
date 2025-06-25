from django.contrib.contenttypes.models import ContentType
from .models import AuditLog

def get_client_ip(request):
    """Get the client IP address from the request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_audit_event(user, action, content_object=None, changes=None, ip_address=None, user_agent=None):
    """
    Create an audit log entry
    """
    audit_data = {
        'user': user,
        'action': action,
        'ip_address': ip_address,
        'user_agent': user_agent,
        'changes': changes or {}
    }
    
    # Set empresa from user or content_object
    if user and user.empresa:
        audit_data['empresa'] = user.empresa
    elif content_object and hasattr(content_object, 'empresa'):
        audit_data['empresa'] = content_object.empresa
    
    if content_object:
        audit_data.update({
            'content_type': ContentType.objects.get_for_model(content_object),
            'object_id': str(content_object.pk),  # Convert to string for UUID support
            'object_repr': str(content_object)
        })
    
    AuditLog.objects.create(**audit_data)

def validate_domain_name(domain_name):
    """
    Validate domain name format
    """
    import re
    
    # Basic domain name validation
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    
    if not re.match(domain_pattern, domain_name):
        return False, "Invalid domain name format"
    
    if len(domain_name) > 253:
        return False, "Domain name too long"
    
    if '..' in domain_name:
        return False, "Domain name cannot contain consecutive dots"
    
    return True, "Valid domain name"

def validate_dns_record(record_type, value):
    """
    Validate DNS record values based on type
    """
    import ipaddress
    import re
    
    if record_type == 'A':
        try:
            ipaddress.IPv4Address(value)
            return True, "Valid IPv4 address"
        except ipaddress.AddressValueError:
            return False, "Invalid IPv4 address"
    
    elif record_type == 'AAAA':
        try:
            ipaddress.IPv6Address(value)
            return True, "Valid IPv6 address"
        except ipaddress.AddressValueError:
            return False, "Invalid IPv6 address"
    
    elif record_type == 'MX':
        # MX records should be in format "priority hostname"
        parts = value.split()
        if len(parts) != 2:
            return False, "MX record should be in format 'priority hostname'"
        
        try:
            priority = int(parts[0])
            if priority < 0 or priority > 65535:
                return False, "MX priority must be between 0 and 65535"
        except ValueError:
            return False, "Invalid MX priority"
        
        hostname = parts[1]
        if not validate_domain_name(hostname)[0]:
            return False, "Invalid hostname in MX record"
        
        return True, "Valid MX record"
    
    elif record_type == 'CNAME':
        is_valid, message = validate_domain_name(value)
        if not is_valid:
            return False, f"Invalid CNAME target: {message}"
        return True, "Valid CNAME record"
    
    elif record_type in ['SPF', 'DMARC', 'TXT']:
        # Basic validation for text records
        if len(value) > 255:
            return False, f"{record_type} record too long (max 255 characters)"
        return True, f"Valid {record_type} record"
    
    elif record_type == 'DKIM':
        # DKIM records are typically long base64 encoded strings
        if not value.strip():
            return False, "DKIM record cannot be empty"
        return True, "Valid DKIM record"
    
    return True, "Record type not validated"

def format_dns_record_for_display(record):
    """
    Format DNS record for display purposes
    """
    display_value = record.valor
    
    if record.tipo == 'MX' and record.prioridad:
        display_value = f"{record.prioridad} {record.valor}"
    elif record.tipo == 'DKIM' and len(record.valor) > 50:
        display_value = record.valor[:50] + "..."
    
    return {
        'name': record.nombre,
        'type': record.tipo,
        'value': display_value,
        'ttl': record.ttl,
        'status': record.estado
    }

def get_domain_health_score(domain):
    """
    Calculate a health score for a domain based on its DNS records
    """
    records = domain.registros.all()
    total_records = records.count()
    
    if total_records == 0:
        return 0
    
    valid_records = records.filter(estado='valid').count()
    invalid_records = records.filter(estado='invalid').count()
    error_records = records.filter(estado='error').count()
    
    # Calculate score (0-100)
    score = (valid_records / total_records) * 100
    
    # Penalize errors more than invalid records
    error_penalty = (error_records / total_records) * 20
    invalid_penalty = (invalid_records / total_records) * 10
    
    final_score = max(0, score - error_penalty - invalid_penalty)
    
    return round(final_score, 1)