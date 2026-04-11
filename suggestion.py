import requests
from pprint import pprint

def in_area(obs_lat, obs_lon, center_lat, center_lon, radius_km):
    return distance((float(obs_lat), float(obs_lon)), (center_lat, center_lon)).km <= radius_km

def place_matches(status_place, target_places):
    """
    status_place: dict or None
    target_places: list of strings to match, e.g., ['United States', 'Eastern US']
    """
    if not status_place:
        return True  # global
    place_name = status_place.get('name', '').lower()
    return any(tp.lower() in place_name for tp in target_places)

class INatClient:
    BASE_URL = 'https://api.inaturalist.org/v1'
    STATUS = {
        'EX': 'Extinct',
        'EW': 'Extinct in the Wild',
        'CR': 'Critically Endangered',
        'EN': 'Endangered',
        'VU': 'Vulnerable',
        'NT': 'Near Threatened',
        'LC': 'Least Concern',
        'DD': 'Data Deficient',
        'NE': 'Not Evaluated',
        'RE': 'Regionally Extinct',
        'NA': 'Not Applicable'
    }
    RARE_CODES = ['EX','EW','CR','EN','VU','NT','S1','S2','N1','N2']

    def __init__(self):
        pass

    def get_observations(self, lat, lon, radius_km, per_page=30, quality_grade='research'):
        url = self.BASE_URL + '/observations'
        params = {
            'lat': lat,
            'lng': lon,
            'radius': radius_km,
            'order_by': "observed_on",
            'order': "desc",
            'per_page': per_page,
            'quality_grade': quality_grade,
            'extra[]': ['taxon', 'observation_photos', 'conservation_status'],
            "include": "taxon",
            'fields': 'all'
            # 'taxon_name': taxon_filter
        }
        r = requests.get(url, params=params)
        r.raise_for_status()
        return r.json()['results']
    
    def get_taxon(self, id):
        url = f'https://api.inaturalist.org/v1/taxa/{id}'
        params = {
            'fields': 'id,name,preferred_common_name,conservation_statuses'
        }
        r = requests.get(url, params=params)
        r.raise_for_status()
        return r.json()['results'][0]

    def filter_rare(self, observations):
        rare_obs = []

        for obs in observations:
            taxon = obs.get('taxon')
            if not taxon:
                continue
            
            data = self.get_taxon(taxon.get('id'))
            for status in data.get('conservation_statuses', []):
                code = status.get('status')
                if not code:
                    continue

                codes = code.split(',')
                if any(c in self.RARE_CODES for c in codes):
                    rare_obs.append(obs)

        return rare_obs

inat = INatClient()

lat, lng = 39.1928853, -76.7241371
radius = 300


rare_sightings = inat.filter_rare(inat.get_observations(lat, lng, radius))
#rare_sightings = inat.get_observations(lat, lng, 50)

pprint(rare_sightings)
#pprint(inat.get_taxon(12727)['conservation_statuses'])
#pprint(inat.get_taxon(130793)['conservation_status']['status'])
