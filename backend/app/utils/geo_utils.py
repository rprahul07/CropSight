import io
try:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
except ImportError:
    Image = None

def calculate_area_from_pixels(pixel_count: int, resolution: float = 0.5) -> float:
    return pixel_count * (resolution ** 2)

def extract_gps_info(image_bytes: bytes) -> dict:
    if Image is None:
        return {"status": "unavailable"}
    try:
        img = Image.open(io.BytesIO(image_bytes))
        exif_data = img._getexif()
        if not exif_data:
            return {"status": "unavailable"}
            
        geo_info = {}
        for tag, value in exif_data.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    geo_info[sub_decoded] = value[t]
                    
        if not geo_info or 'GPSLatitude' not in geo_info or 'GPSLongitude' not in geo_info:
            return {"status": "unavailable"}
            
        def convert_to_degrees(value):
            d = float(value[0]) if not isinstance(value[0], tuple) else float(value[0][0])/float(value[0][1])
            m = float(value[1]) if not isinstance(value[1], tuple) else float(value[1][0])/float(value[1][1])
            s = float(value[2]) if not isinstance(value[2], tuple) else float(value[2][0])/float(value[2][1])
            return d + (m / 60.0) + (s / 3600.0)
            
        lat = convert_to_degrees(geo_info['GPSLatitude'])
        if geo_info.get('GPSLatitudeRef', 'N') != 'N':
            lat = -lat
            
        lon = convert_to_degrees(geo_info['GPSLongitude'])
        if geo_info.get('GPSLongitudeRef', 'E') != 'E':
            lon = -lon
            
        return {"lat": round(lat, 6), "lon": round(lon, 6), "status": "available"}
    except Exception:
        return {"status": "unavailable"}
