from diskcache import Cache
import requests

BASE_URLL = "https://exercisesdb-api.vercel.app/api/v1/exercises"
CACHE = Cache('./cache_dir')

def get_exercises_by_target(target):
    """
    Fetch exercises by target muscle group from the API.
    Caches the result to avoid repeated API calls.
    """

    if target in CACHE:
        return CACHE[target]

    response = requests.get(f"{BASE_URLL}/target/{target}")

    if response.status_code == 200:
        result = response.json()
        CACHE[target] = result
        return result
    return []

def get_exercises_by_equipment(equipment):
    """
    Fetch exercises by equipment type from the API.
    Caches the result to avoid repeated API calls.
    """

    if equipment in CACHE:
        return CACHE[equipment]

    response = requests.get(f"{BASE_URLL}/equipment/{equipment}")

    if response.status_code == 200:
        result = response.json()
        CACHE[equipment] = result
        return result
    return []