import os
import requests
from urllib.parse import quote

def find_doctors_google(specialist_type, latitude, longitude, radius=5000, api_key=None):
    if not api_key:
        return []
    
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    
    # Map the search term to Google's keyword and type
    keyword = specialist_type
    place_type = 'hospital' if 'hospital' in specialist_type.lower() else 'doctor'
    
    params = {
        'location': f"{latitude},{longitude}",
        'radius': radius,
        'keyword': keyword,
        'type': place_type,
        'key': api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # If no results found with specific keyword, try searching for general doctors/hospitals
        if not data.get('results'):
            params.pop('keyword', None)
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

        results = []
        for place in data.get('results', [])[:8]:
            lat = place.get('geometry', {}).get('location', {}).get('lat')
            lon = place.get('geometry', {}).get('location', {}).get('lng')
            
            if not lat or not lon:
                continue
                
            name = place.get('name', 'Unnamed Clinic')
            rating = place.get('rating')
            user_ratings = place.get('user_ratings_total', 0)
            
            # Format name with rating stars for premium UI
            if rating:
                name = f"{name} ({rating} ★, {user_ratings} reviews)"
                
            address = place.get('vicinity', 'Address not listed')
            
            open_now = place.get('opening_hours', {}).get('open_now')
            opening_hours = "Open Now" if open_now else ("Closed" if open_now is False else "Not listed")
            
            place_id = place.get('place_id')
            maps_link = f"https://www.google.com/maps/search/?api=1&query={quote(place.get('name', ''))}&query_place_id={place_id}" if place_id else f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
            
            results.append({
                'name': name,
                'address': address,
                'phone': 'Available on Google Maps link',
                'opening_hours': opening_hours,
                'lat': lat,
                'lon': lon,
                'maps_link': maps_link
            })
            
        return results
    except Exception as e:
        print(f"Google Places API error: {e}")
        return []

def find_doctors_osm(specialist_type, latitude, longitude, radius=5000):
    """
    Fallback method using OpenStreetMap Overpass API.
    """
    OSM_TAGS = {
        'cardiologist':       '["amenity"="doctors"]["healthcare:speciality"="cardiology"]',
        'dermatologist':      '["amenity"="doctors"]["healthcare:speciality"="dermatology"]',
        'neurologist':        '["amenity"="doctors"]["healthcare:speciality"="neurology"]',
        'orthopaedic':        '["amenity"="doctors"]["healthcare:speciality"="orthopaedics"]',
        'gynaecologist':      '["amenity"="doctors"]["healthcare:speciality"="gynaecology"]',
        'paediatrician':      '["amenity"="doctors"]["healthcare:speciality"="paediatrics"]',
        'psychiatrist':       '["amenity"="doctors"]["healthcare:speciality"="psychiatry"]',
        'ophthalmologist':    '["amenity"="doctors"]["healthcare:speciality"="ophthalmology"]',
        'ent':                '["amenity"="doctors"]["healthcare:speciality"="ENT"]',
        'gastroenterologist': '["amenity"="doctors"]["healthcare:speciality"="gastroenterology"]',
        'general physician':  '["amenity"="doctors"]',
        'hospital':           '["amenity"="hospital"]',
        'clinic':             '["amenity"="clinic"]',
        'default':            '["amenity"="hospital"]',
    }

    tag = OSM_TAGS['default']
    specialist_lower = specialist_type.lower()
    for key in OSM_TAGS:
        if key in specialist_lower:
            tag = OSM_TAGS[key]
            break

    OVERPASS_URLS = [
        "https://overpass-api.de/api/interpreter",
        "https://lz4.overpass-api.de/api/interpreter",
        "https://z.overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.private.coffee/api/interpreter",
    ]

    query = f"""
    [out:json][timeout:10];
    (
      node{tag}(around:{radius},{latitude},{longitude});
      way{tag}(around:{radius},{latitude},{longitude});
    );
    out center 8;
    """

    headers = {
        'User-Agent': 'MebEZDoctorFinder/1.0',
    }

    for url in OVERPASS_URLS:
        for attempt_method in ['POST', 'GET']:
            try:
                if attempt_method == 'POST':
                    response = requests.post(
                        url,
                        data=query,
                        headers=headers,
                        timeout=12
                    )
                else:
                    response = requests.get(
                        url,
                        params={'data': query},
                        headers=headers,
                        timeout=12
                    )
                response.raise_for_status()
                data = response.json()

                results = []
                for element in data.get('elements', []):
                    tags = element.get('tags', {})

                    if element['type'] == 'node':
                        lat = element.get('lat')
                        lon = element.get('lon')
                    else:
                        center = element.get('center', {})
                        lat = center.get('lat')
                        lon = center.get('lon')

                    if not lat or not lon:
                        continue

                    name = (tags.get('name') or
                            tags.get('operator') or
                            'Unnamed Clinic')

                    address_parts = []
                    for field in ['addr:housenumber', 'addr:street',
                                  'addr:suburb', 'addr:city']:
                        val = tags.get(field)
                        if val:
                            address_parts.append(val)
                    address = ', '.join(address_parts) if address_parts else 'Address not listed'

                    phone = tags.get('phone') or tags.get('contact:phone') or 'Not listed'
                    opening = tags.get('opening_hours') or 'Not listed'

                    results.append({
                        'name': name,
                        'address': address,
                        'phone': phone,
                        'opening_hours': opening,
                        'lat': lat,
                        'lon': lon,
                        'maps_link': f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=17"
                    })

                return results

            except requests.exceptions.Timeout:
                print(f"TIMEOUT on {url} ({attempt_method}) — trying fallback")
                continue
            except Exception as e:
                print(f"ERROR on {url} ({attempt_method}): {e}")
                continue

    print("All Overpass mirrors failed")
    return []

def find_nearby_doctors(specialist_type, latitude, longitude, radius=5000):
    """
    Main entry point. Uses Google Places API if configured, otherwise falls back to OSM.
    """
    api_key = os.getenv('GOOGLE_MAPS_KEY')
    
    if api_key and api_key != "your_google_maps_key_here":
        print("Using Google Places API for doctor lookup...")
        google_results = find_doctors_google(specialist_type, latitude, longitude, radius, api_key)
        if google_results:
            return google_results
        print("Google Places API failed/empty, falling back to OpenStreetMap...")

    return find_doctors_osm(specialist_type, latitude, longitude, radius)