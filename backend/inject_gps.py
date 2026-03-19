import piexif
from PIL import Image
import sys
import os

def to_dms(decimal_degree):
    """Converts a decimal degree to Degrees, Minutes, Seconds (DMS) format used by EXIF."""
    d = int(decimal_degree)
    m = int((decimal_degree - d) * 60)
    s = (decimal_degree - d - m/60.0) * 3600.0
    return ((d, 1), (m, 1), (int(s * 100), 100))

def inject_gps(input_filename, output_filename, lat, lon):
    if not os.path.exists(input_filename):
        print(f"Error: {input_filename} not found.")
        return

    try:
        # Load existing image EXIF if available, otherwise create a blank dictionary
        try:
            exif_dict = piexif.load(input_filename)
        except Exception:
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "Interop": {}}

        lat_ref = 'N' if lat >= 0 else 'S'
        lon_ref = 'E' if lon >= 0 else 'W'

        # Force inject standard GPS EXIF tags
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = lat_ref
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = to_dms(abs(lat))
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = lon_ref
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = to_dms(abs(lon))
        exif_dict["GPS"][piexif.GPSIFD.GPSAltitude] = (150, 1) # Fake 150m drone elevation

        exif_bytes = piexif.dump(exif_dict)
        
        img = Image.open(input_filename)
        if img.mode != "RGB":
            img = img.convert("RGB")
            
        img.save(output_filename, "jpeg", exif=exif_bytes)
        print(f"Success! Saved GPS-injected image as: {output_filename}")
        print(f"Coordinates: {lat}, {lon}")

    except Exception as e:
        print(f"Failed to inject EXIF: {e}")

if __name__ == "__main__":
    print("CropSight Fake GPS Injector")

    input_file = "PermanentCrop_90.jpg"
    output_file = "geotagged_crop2.jpg"
    
    # Example coordinates: A random farming field in Iowa, USA
    latitude = 41.8780 
    longitude = -93.0977
    
    inject_gps(input_file, output_file, latitude, longitude)
