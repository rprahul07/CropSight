import io
import logging

try:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
except ImportError:
    Image = None

logger = logging.getLogger(__name__)

def convert_to_decimal(value, ref):
    if not value or len(value) < 3:
        return 0.0
    
    def process_val(v):
        if hasattr(v, "numerator") and hasattr(v, "denominator"):
            return float(v.numerator) / float(v.denominator) if v.denominator != 0 else 0.0
        elif isinstance(v, tuple) and len(v) == 2:
            return float(v[0]) / float(v[1]) if v[1] != 0 else 0.0
        return float(v)
        
    d = process_val(value[0])
    m = process_val(value[1])
    s = process_val(value[2])
    
    decimal = d + (m / 60.0) + (s / 3600.0)
    
    if ref in ['S', 'W', 's', 'w']:
        decimal = -decimal
        
    return decimal

def extract_gps(image_data):
    if Image is None:
        return None
    try:
        if isinstance(image_data, bytes):
            img = Image.open(io.BytesIO(image_data))
        else:
            img = Image.open(image_data)
            
        exif_data = img._getexif()
        if not exif_data:
            return None
            
        geo_info = {}
        for tag, value in exif_data.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    geo_info[sub_decoded] = value[t]
                    
        if not geo_info or 'GPSLatitude' not in geo_info or 'GPSLongitude' not in geo_info:
            return None
            
        lat_ref = geo_info.get('GPSLatitudeRef', 'N')
        lon_ref = geo_info.get('GPSLongitudeRef', 'E')
        
        lat = convert_to_decimal(geo_info['GPSLatitude'], lat_ref)
        lon = convert_to_decimal(geo_info['GPSLongitude'], lon_ref)
        
        logger.info(f"GPS detected: lat={round(lat, 6)}, lon={round(lon, 6)}")
        return {"lat": round(lat, 6), "lon": round(lon, 6)}
        
    except Exception as e:
        logger.warning(f"Error extracting GPS: {str(e)}")
        return None
