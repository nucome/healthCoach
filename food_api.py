import asyncio
import requests

BASE_URLL = "https://world.openfoodfacts.org/api/v0/product"


def get_food_by_barcode(barcode):

    """
    Fetch food product details by barcode from the Open Food Facts API.
    """
    url = f"{BASE_URLL}/{barcode}.json"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if 'product' in data:
            return data['product']
        else:
            return {"error": "Product not found"}
    else:
        return {"error": f"Failed to fetch data, status code: {response.status_code}"}

async def async_search_foods(query):
    """
    Asynchronous function to search for food products by query.
    """
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={query}&search_simple=1&json=1"

    response = await asyncio.to_thread(requests.get, url)

    if response.status_code == 200:
        data = response.json()
        return data.get('products', [])
    else:
        return {"error": f"Failed to fetch data, status code: {response.status_code}"}