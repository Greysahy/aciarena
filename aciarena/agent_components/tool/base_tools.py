
from aciarena.utils import register_tool

@register_tool()
def get_weather(city: str, unit: str = "Celsius") -> str:
    """
    A simple tool to get the weather for a given city.

    Args:
        city (str): Name of the city to query the weather for.
        unit (str): Unit of temperature, default is "Celsius".
    """
    return f"The weather in {city} is sunny with a high of 25 {unit}."
