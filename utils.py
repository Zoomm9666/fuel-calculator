import math

def calculate_distance(lat1, lon1, lat2, lon2):
    """Считает ортодромию в морских милях (NM)"""
    R = 3440.065  # Радиус Земли в морских милях
    
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return c * R

def get_intermediate_point(lat1, lon1, lat2, lon2, fraction):
    """Находит координаты точки на дистанции (fraction от 0 до 1)"""
    # Математика для поиска точки на большой дуге
    lat1, lon1 = math.radians(lat1), math.radians(lon1)
    lat2, lon2 = math.radians(lat2), math.radians(lon2)
    
    # Расстояние между точками в радианах
    d = 2 * math.asin(math.sqrt(math.sin((lat1 - lat2) / 2)**2 + 
                                  math.cos(lat1) * math.cos(lat2) * math.sin((lon1 - lon2) / 2)**2))
    
    if d == 0: return math.degrees(lat1), math.degrees(lon1)
    
    A = math.sin((1 - fraction) * d) / math.sin(d)
    B = math.sin(fraction * d) / math.sin(d)
    
    x = A * math.cos(lat1) * math.cos(lon1) + B * math.cos(lat2) * math.cos(lon2)
    y = A * math.cos(lat1) * math.sin(lon1) + B * math.cos(lat2) * math.sin(lon2)
    z = A * math.sin(lat1) + B * math.sin(lat2)
    
    lat_res = math.atan2(z, math.sqrt(x**2 + y**2))
    lon_res = math.atan2(y, x)
    
    return math.degrees(lat_res), math.degrees(lon_res)
