from math import radians, sin, cos, sqrt, atan2


def calculate_distance(lat1, lon1, lat2, lon2):

    R = 6371  # Earth radius km

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2

    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c * 1000  # meters


def is_out_of_stage(rider_lat, rider_lon, stage_lat, stage_lon, radius):

    distance = calculate_distance(rider_lat, rider_lon, stage_lat, stage_lon)

    return distance > radius

def trigger_auto_fine(user, reason, amount, location):

    from fines.models import Fine

    Fine.objects.create(
        issued_by=None,  # system generated
        rider=user.rider_profile if hasattr(user, 'rider_profile') else None,
        guest_rider=user.guest_rider_profile if hasattr(user, 'guest_rider_profile') else None,
        reason=reason,
        amount=amount,
        status='pending',
        latitude=location.get('lat'),
        longitude=location.get('lng'),
    )