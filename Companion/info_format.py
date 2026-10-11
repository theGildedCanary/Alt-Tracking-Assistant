"""Render character info markup without changing its saved source."""
import re
import theme

PROFILE_IMAGES = {
    'interface/petbattles/weather-sandstorm': 'weather-sandstorm.png',
    'interface/questframe/ui-horizontalbreak': 'ui-horizontalbreak.png',
}
HEADER_IMAGES = {
    'Sandstorm': 'Sandstorm',
    'Arcane Storm': 'ArcaneStorm',
    'Blizzard': 'Blizzard',
    'Burnt Earth': 'BurntEarth',
    'Darkness': 'Darkness',
    'Moonlight': 'Moonlight',
    'Earth': 'Mud',
    'Rain': 'Rain',
    'Electrical Storm': 'StaticField',
    'Sunlight': 'Sunlight',
    'Fel': 'ToxicFumes',
    'Wind': 'Windy',
}
for weather in HEADER_IMAGES.values():
    PROFILE_IMAGES['interface/petbattles/weather-'+weather.lower()] = 'weather-'+weather.lower()+'.png'


def header_name(source):
    html_image = re.match(r'\s*<img\b[^>]*\bsrc=["\']([^"\']+)["\'][^>]*>', source, re.I)
    if html_image:
        weather = re.search(r'weather-([^/.]+)', html_image.group(1), re.I)
        if weather:
            return next((name for name, value in HEADER_IMAGES.items() if value.lower() == weather.group(1).lower()), 'None')
    return 'None'


def set_header(source, name):
    if header_name(source) != 'None':
        source = re.sub(r'^\s*<img\b[^>]*>[ \t]*(?:\r?\n)?', '', source, count=1, flags=re.I)
    if name == 'None':
        return source
    return '<img src="Interface\\PETBATTLES\\Weather-'+HEADER_IMAGES[name]+'" width="512" height="128" align="center">\n'+source


def render_info(widget, source, family='Montserrat'):
    from info_html import render_html
    widget.configure(font=(family, 9), spacing1=0, spacing2=0, spacing3=0)
    render_html(widget, source, family, PROFILE_IMAGES)
