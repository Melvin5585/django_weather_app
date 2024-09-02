from django.shortcuts import render
from django.http import HttpResponse
from weather_app import settings
import requests
import os
import json
from datetime import datetime, timedelta

# Create your views here.

def hello_world(request):
    return render(request, "home.html")


def search_weather(request):
    if request.method == 'POST':
        
        city_name = request.POST.get('city', '')
        # check if cache file exists
        # filename = f"app/cache/{city_name}{round(city['lat'], 2)}-{round(city['lon'], 2)}.txt"
        cache_directory = 'app/cache'
        filename = get_fullname(directory_path=cache_directory, prefix=city_name)

        if not filename is None and check_if_cache_file_exists(filename=filename):
            # read data from cache if they not 180 minutes old
            cache_data = read_cache(filename=filename)

            # check if the information is not 180 minutes longer
            time_cache_created = cache_data['datetime']
            time_created = datetime.strptime(time_cache_created, "%Y-%m-%d %H:%M:%S.%f")

            current_time = datetime.now()
            time_difference = current_time - time_created
            three_hours_passed = time_difference >= timedelta(minutes=180)

            if not three_hours_passed:
                print("FROM CACHE")
                return render(request, 'home.html', {'city_weather': cache_data, 'search_status': 'success'})
            else:
                # delete old file
                print("DELETING OLD CACHE FILE AND CREATE NEW")
                delete_old_cache_file(filename)
                response = weather_api_call(city_name=city_name, request=request)
                return response

            
        else:
            # create cache file with data
            response = weather_api_call(city_name=city_name, request=request)
            return response
                              

def weather_api_call(city_name, request):
    api_url = f'https://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=5&appid={settings.OPEN_WEATHER_API_KEY}'
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()

        for city in data:
            if city['country'] == "ZA":
                # lat and lon inside dictionary `city`
                # use coordinates to search for city weather
                api_url2 = f"https://api.openweathermap.org/data/2.5/weather?lat={city['lat']}&lon={city['lon']}&appid={settings.OPEN_WEATHER_API_KEY}"
                response = requests.get(api_url2)
                city_weather_info = response.json()
                if response.status_code == 200:
                    city_weather_info['datetime'] = str(datetime.now())
                    city_weather_info['main']['temp'] = round(city_weather_info['main']['temp'] - 273.15, 2)
                    filename = f"app/cache/{city_name}{round(city['lat'], 2)}-{round(city['lon'], 2)}.txt"
                    write_cache(filename=filename, data=city_weather_info)
                    return render(request, 'home.html', {'city_weather': city_weather_info, 'search_status': 'success'})
                else:
                    return render(request, 'home.html', {'city:': None, 'search_status': 'failed', 'reason':f'Error while fetching {city_name} weather'}) 
    else:
        return render(request, 'home.html', {'city:': None, 'search_status': 'failed', 'reason':f'Error while converting {city_name} to coordinates'})  





def write_cache(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)


def read_cache(filename):
    with open(filename, 'r') as file:
        return json.load(file)
    
def get_fullname(directory_path, prefix):
    files = sorted(os.listdir(directory_path))
    prefix = prefix.lower()  # Convert prefix to lower case for case-insensitive comparison
    for file in files:
        file_lower = file.lower()  # Convert file name to lower case
        if file_lower.startswith(prefix.lower()):  # Ensure prefix is lower case
            file_path = os.path.join(directory_path, file)
            return file_path
    return None

def delete_old_cache_file(path):
    if os.path.exists(path):
        os.remove(path)


def check_if_cache_file_exists(filename):
    if os.path.exists(filename):
        return True
    else:
        return False
    