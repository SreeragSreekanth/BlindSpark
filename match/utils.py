# matches/utils.py
import math

def haversine_km(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return None
    R = 6371.0
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_match_score(user_a, user_b):
    a_interests = set(user_a.interests.values_list('id', flat=True))
    b_interests = set(user_b.interests.values_list('id', flat=True))
    shared = len(a_interests & b_interests)
    interest_score = (shared / max(len(a_interests), 1)) * 70

    loc_score = 15.0
    if all([user_a.latitude, user_a.longitude, user_b.latitude, user_b.longitude]):
        dist = haversine_km(user_a.latitude, user_a.longitude, user_b.latitude, user_b.longitude)
        loc_score = max(0, 30 - dist * 0.3)

    total = interest_score + loc_score
    return round(min(total, 100), 2)