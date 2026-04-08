import requests
from pprint import pprint


class INatClient:
    BASE_URL = 'https://api.inaturalist.org/v2'

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
        url = f'{self.BASE_URL}/taxa/{id}'
        params = {
            "fields": ["id","name","preferred_common_name","rank","conservation_status"]
        }
        r = requests.get(url, params=params)
        r.raise_for_status()
        return r.json()['results']

    
    def filter_rare(self, observations):
        rare_obs = []
        for obs in observations:
            taxon = obs.get('taxon')
            rare_obs.append(self.get_taxon(taxon.get('id')))
            if not taxon:
                continue


        return rare_obs

inat = INatClient()

lat, lng = 37.7749, -122.4194

#rare_sightings = inat.filter_rare(inat.get_observations(lat, lng, 50))
rare_sightings = inat.get_observations(lat, lng, 50)

pprint(rare_sightings)
