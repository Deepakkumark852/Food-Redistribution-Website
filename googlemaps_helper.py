import os
import requests

def geocode_address(address, api_key=None):
    api_key = api_key or os.environ.get('GOOGLE_MAPS_API_KEY')
    url = f'https://maps.googleapis.com/maps/api/geocode/json?address={requests.utils.quote(address)}&key={api_key}'
    resp = requests.get(url)
    data = resp.json()
    if data['status'] == 'OK':
        loc = data['results'][0]['geometry']['location']
        return loc['lat'], loc['lng']
    return None, None

def reverse_geocode(lat, lng, api_key=None):
    api_key = api_key or os.environ.get('GOOGLE_MAPS_API_KEY')
    url = f'https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={api_key}'
    resp = requests.get(url)
    data = resp.json()
    if data['status'] == 'OK':
        return data['results'][0]['formatted_address']
    return None
