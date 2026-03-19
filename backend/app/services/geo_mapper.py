def create_bounds(lat: float, lon: float, offset: float = 0.0003) -> list:
    return [
        [lat - offset, lon - offset],
        [lat + offset, lon + offset]
    ]

def pixel_to_geo(x: int, y: int, width: int, height: int, bounds: list) -> list:
    min_lat, min_lon = bounds[0]
    max_lat, max_lon = bounds[1]
    
    lon_ratio = x / max(width - 1, 1)
    lon = min_lon + lon_ratio * (max_lon - min_lon)
    
    lat_ratio = y / max(height - 1, 1)
    lat = max_lat - lat_ratio * (max_lat - min_lat)
    
    return [lat, lon]

def convert_contour_to_geo(contour: list, bounds: list, image_shape: tuple) -> list:
    height = image_shape[0]
    width = image_shape[1]
    
    geo_coords = []
    for pt in contour:
        if isinstance(pt[0], (list, tuple)):
            x, y = pt[0][0], pt[0][1]
        elif isinstance(pt[0], (float, int)):
            x, y = pt[0], pt[1]
        else:
            try:
                x, y = pt[0][0], pt[0][1]
            except:
                x, y = pt[0], pt[1]
            
        geo_pt = pixel_to_geo(int(x), int(y), width, height, bounds)
        geo_coords.append(geo_pt)
    
    return geo_coords
