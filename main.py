from functools import wraps
from typing import Callable
from populartimes.crawler import PopulartimesException
import populartimes
import googlemaps
from flask import Flask, jsonify, request, Response
from dotenv import load_dotenv
import os
from googlemaps.exceptions import ApiError

load_dotenv()

app = Flask(__name__)
app.config['API_KEY'] = os.environ.get('api_key')
gmaps_client = googlemaps.Client(key=os.environ.get('gmap_api'))


def token_required(func: Callable) -> Callable:
    @wraps(func)
    def decorator(*args, **kwargs):
        token = None
        if 'Api-Access-Tokens' in request.headers:
            token = request.headers.get('Api-Access-Tokens')
        if not token:
            return jsonify({'message': 'a valid token is missing', 'status': 401})
        if app.config['API_KEY'] != token:
            return jsonify({'message': 'token is invalid', 'status': 401})
        return func(*args, **kwargs)
    return decorator


def get_data_by_id(place_id: str) -> Response:
    try:
        response = gmaps_client.place(place_id=place_id, language='ru-RU')
        full_result = populartimes.get_id(
            api_key=os.environ.get('gmap_api'),
            place_id=place_id
        )
        full_result['status'] = 200
        if response['result']:
            print(response)
            if 'photos' in response['result']:
                full_result['photos'] = response['result']['photos']
            if 'price_level' in response['result']:
                full_result['price_level'] = response['result']['price_level']
            if 'opening_hours' in response['result']:
                full_result['open_now'] = response['result']['opening_hours']['open_now']
                full_result['weekday_text'] = response['result']['opening_hours']['weekday_text']
        return jsonify(full_result)
    except (PopulartimesException, ApiError):
        return jsonify({'result': 'invalid place_id', 'status': 401})


@app.route('/', methods=['GET'])
@token_required
def gmaps() -> Response:
    place_id = request.args.get('place_id')
    if place_id is None:
        search_val = request.args.get('search_by')
        if search_val is not None:
            response = gmaps_client.places(query=search_val)
            if response['results']:
                place_id = response['results'][0]['place_id']
            else:
                return jsonify({'result': 'wrong search_by query', 'status': 401})
        else:
            return jsonify({'result': 'place_id or search_by required', 'status': 401})
    return get_data_by_id(place_id=place_id)


@app.route('/PlacesNearby/', methods=['GET'])
@token_required
def nearby_search() -> Response:
    data = request.args
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    try:
        radius = int(float(data.get('radius')) * 1000)
    except (ValueError, TypeError):
        return jsonify({'result': 'radius must be integer', 'status': 401})

    if None not in (latitude, longitude, radius):
        response = gmaps_client.places_nearby(location=(latitude, longitude),
                                              radius=radius,
                                              min_price=data.get('min_price'),
                                              max_price=data.get('max_price'),
                                              open_now=data.get('open_now'),
                                              page_token=data.get('page_token'),
                                              type=data.get('type'))
        id_list = list()
        for i in response['results']:
            id_list.append(i['place_id'])
        return jsonify({'next_page_token': response['next_page_token'] if 'next_page_token' in response else None,
                        'id_array': id_list, 'status': 200})
    else:
        return jsonify({'result': 'latitude, longitude and radius are required ', 'status': 401})


@app.route('/short-data-by-id/', methods=['GET'])
@token_required
def short_data_by_id() -> Response:
    place_id = request.args.get('place_id')
    if place_id is not None:
        try:
            response = gmaps_client.place(place_id=place_id, language='ru-RU')
            full_result = populartimes.get_id(
                api_key=os.environ.get('gmap_api'),
                place_id=place_id
            )
            full_result['status'] = 200
            delete_items = ('coordinates', "rating", "international_phone_number", "populartimes")
            for i in delete_items:
                full_result.pop(i)
            if response['result']:
                if 'photos' in response['result']:
                    full_result['photos'] = response['result']['photos'][0]
                    full_result['open_now'] = response['result']['opening_hours']['open_now']
            return jsonify(full_result)
        except (PopulartimesException, ApiError):
            return jsonify({'result': 'invalid place_id', 'status': 401})


if __name__ == '__main__':
    app.run()
