import googlemaps
import os
import json
from dotenv import load_dotenv
import populartimes

load_dotenv()
#
gmaps_client = googlemaps.Client(key=os.environ.get('gmap_api'))
ep = gmaps_client.place(place_id='ChIJReJduKGkakARt03E2ByMs8o')
response = gmaps_client.places(query="Красное&Белое 1-я Вокзальная ул., 28, Барыбино, Московская обл., 142062")
full_result = populartimes.get_id(
            api_key=os.environ.get('gmap_api'),
            place_id='ChIJe-ylXBVhNUERanpoxmy6ws8'
        )
print(json.dumps(gmaps_client.place(place_id='ChIJe-ylXBVhNUERanpoxmy6ws8'), indent=4))


