from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.network.urlrequest import UrlRequest
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock
import json
from datetime import datetime

class WeatherApp(App):
    def build(self):
        self.title = '🌤️ Weather Forecast'
        Window.size = (400, 700)
        
        main = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Title
        title = Label(text='🌤️ Weather Forecast', font_size=32, size_hint_y=None, height=60)
        main.add_widget(title)
        
        # Support Button
        support = Button(
            text='🌟 Support @SpaceExplorerWorld',
            font_size=16,
            size_hint_y=None,
            height=50,
            background_color=(0.13, 0.59, 0.95, 1)
        )
        support.bind(on_press=self.open_youtube)
        main.add_widget(support)
        
        # Input Row
        input_row = BoxLayout(size_hint_y=None, height=50, spacing=10)
        self.city_input = TextInput(hint_text='Enter city', multiline=False, font_size=18)
        self.city_input.bind(on_text_validate=self.get_weather)
        input_row.add_widget(self.city_input)
        
        search_btn = Button(text='🔍', size_hint_x=None, width=50)
        search_btn.bind(on_press=self.get_weather)
        input_row.add_widget(search_btn)
        
        location_btn = Button(text='📍', size_hint_x=None, width=50, background_color=(0.13, 0.59, 0.95, 1))
        location_btn.bind(on_press=self.get_location)
        input_row.add_widget(location_btn)
        
        main.add_widget(input_row)
        
        # Results Area
        scroll = ScrollView()
        self.result = Label(
            text='🌍 Enter a city or tap 📍',
            font_size=18,
            halign='center',
            valign='top',
            text_size=(Window.width - 40, None),
            size_hint_y=None
        )
        self.result.bind(texture_size=self.result.setter('size'))
        scroll.add_widget(self.result)
        main.add_widget(scroll)
        
        # Footer
        footer = Label(text='🔄 Open-Meteo API', font_size=12, size_hint_y=None, height=30, color=(0.6, 0.6, 0.6, 1))
        main.add_widget(footer)
        
        return main
    
    def open_youtube(self, instance):
        import webbrowser
        webbrowser.open('https://youtube.com/@SpaceExplorerWorld')
    
    def get_weather(self, instance):
        city = self.city_input.text.strip()
        if not city:
            self.result.text = '❗ Enter a city name'
            return
        
        self.result.text = '⏳ Loading...'
        url = f'https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&format=json'
        UrlRequest(url, self.on_geo_done, on_error=self.on_error)
    
    def get_location(self, instance):
        try:
            from plyer import gps
            gps.configure(on_location=self.on_gps_location, on_status=self.on_gps_status)
            gps.start(5000, 0)
            self.result.text = '📍 Getting location...'
        except:
            self.result.text = '❌ GPS not available'
    
    def on_gps_location(self, **kwargs):
        lat = kwargs.get('lat')
        lon = kwargs.get('lon')
        if lat and lon:
            self.fetch_weather(lat, lon, 'Your Location')
    
    def on_gps_status(self, stype, status):
        pass
    
    def on_geo_done(self, req, data):
        try:
            if not data.get('results'):
                self.result.text = '❌ City not found'
                return
            
            city_data = data['results'][0]
            lat = city_data['latitude']
            lon = city_data['longitude']
            name = city_data['name']
            country = city_data.get('country', '')
            
            self.fetch_weather(lat, lon, f'{name}, {country}')
        except:
            self.result.text = '❌ Error processing city'
    
    def fetch_weather(self, lat, lon, location):
        self.result.text = f'📍 {location}\n⏳ Loading...'
        url = f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,windspeed_10m,precipitation,precipitation_probability,snowfall_probability,weathercode&forecast_days=7&timezone=auto'
        UrlRequest(url, lambda req, data: self.on_weather_done(req, data, location), on_error=self.on_error)
    
    def on_weather_done(self, req, data, location):
        try:
            hourly = data.get('hourly', {})
            times = hourly.get('time', [])
            temps = hourly.get('temperature_2m', [])
            winds = hourly.get('windspeed_10m', [])
            rain_prob = hourly.get('precipitation_probability', [])
            snow_prob = hourly.get('snowfall_probability', [])
            codes = hourly.get('weathercode', [])
            
            if not times:
                self.result.text = '❌ No data'
                return
            
            text = f'📍 {location}\n\n'
            text += '🔴 CURRENT CONDITIONS\n'
            text += f'🌡️ {temps[0]}°C  💨 {winds[0]} km/h\n'
            text += f'🌧️ Rain: {rain_prob[0]}%  ❄️ Snow: {snow_prob[0]}%\n\n'
            text += '📅 7-DAY FORECAST\n'
            
            days = []
            seen = set()
            for i, t in enumerate(times):
                day = t[:10]
                if day not in seen:
                    seen.add(day)
                    days.append({
                        'day': datetime.fromisoformat(day).strftime('%a %d'),
                        'temp': temps[i],
                        'code': codes[i],
                        'rain': rain_prob[i] if i < len(rain_prob) else 0,
                        'snow': snow_prob[i] if i < len(snow_prob) else 0
                    })
                    if len(days) >= 7:
                        break
            
            for d in days:
                icon = self.get_icon(d['code'])
                text += f'{d["day"]}: {icon} {d["temp"]}°C  🌧️{d["rain"]}% ❄️{d["snow"]}%\n'
            
            text += f'\n🔄 Updated: {datetime.now().strftime("%H:%M")}'
            self.result.text = text
            
        except Exception as e:
            self.result.text = f'❌ Error: {str(e)}'
    
    def on_error(self, req, error):
        self.result.text = '⚠️ Connection error'
    
    def get_icon(self, code):
        if code == 0: return '☀️'
        if code in [1, 2]: return '⛅'
        if code == 3: return '☁️'
        if code in [45, 48]: return '🌫️'
        if code in [51, 53, 55, 56, 57]: return '🌦️'
        if code in [61, 63, 65, 66, 67, 80, 81, 82]: return '🌧️'
        if code in [71, 73, 75, 77, 85, 86]: return '❄️'
        if code in [95, 96, 99]: return '⛈️'
        return '❓'

if __name__ == '__main__':
    WeatherApp().run()
