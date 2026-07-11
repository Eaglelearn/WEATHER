import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.network.urlrequest import UrlRequest
from kivy.core.window import Window
from kivy.metrics import dp
import json
from datetime import datetime
import ssl
import certifi

# Fix SSL for Android
try:
    import android
except ImportError:
    pass

class WeatherApp(App):
    def build(self):
        self.title = '1 Hour Weather Forecast'
        Window.size = (350, 600)
        self.main_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # Title
        title = Label(text='🌤️ Weather Forecast', font_size=dp(24), size_hint_y=None, height=dp(50))
        self.main_layout.add_widget(title)
        
        # Support Button (Clickable)
        support_btn = Button(
            text='🌟 Support @SpaceExplorerWorld 🌟\non YouTube!',
            font_size=dp(14),
            size_hint_y=None,
            height=dp(60),
            background_color=(0.13, 0.59, 0.95, 1),
            color=(1, 1, 1, 1)
        )
        support_btn.bind(on_press=self.open_youtube)
        self.main_layout.add_widget(support_btn)
        
        # Input Layout
        input_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        
        self.city_input = TextInput(
            hint_text='Enter city name',
            font_size=dp(16),
            multiline=False
        )
        self.city_input.bind(on_text_validate=self.search_weather)
        input_layout.add_widget(self.city_input)
        
        search_btn = Button(text='🔍', font_size=dp(20), size_hint_x=None, width=dp(50))
        search_btn.bind(on_press=self.search_weather)
        input_layout.add_widget(search_btn)
        
        location_btn = Button(
            text='📍',
            font_size=dp(20),
            size_hint_x=None,
            width=dp(50),
            background_color=(0.13, 0.59, 0.95, 1)
        )
        location_btn.bind(on_press=self.get_location)
        input_layout.add_widget(location_btn)
        
        self.main_layout.add_widget(input_layout)
        
        # Scrollable Results
        self.result_scroll = ScrollView()
        self.result_label = Label(
            text='Enter a city or tap 📍 for your location!',
            font_size=dp(16),
            halign='center',
            valign='top',
            text_size=(Window.width - dp(40), None)
        )
        self.result_scroll.add_widget(self.result_label)
        self.main_layout.add_widget(self.result_scroll)
        
        # Footer
        footer = Label(
            text='🔄 Data from Open-Meteo',
            font_size=dp(10),
            size_hint_y=None,
            height=dp(30),
            color=(0.6, 0.6, 0.6, 1)
        )
        self.main_layout.add_widget(footer)
        
        return self.main_layout
    
    def open_youtube(self, instance):
        import webbrowser
        webbrowser.open('https://youtube.com/@SpaceExplorerWorld')
    
    def search_weather(self, instance):
        city = self.city_input.text.strip()
        if not city:
            self.result_label.text = '❗ Please enter a city.'
            return
        
        self.result_label.text = '⏳ Loading forecast...'
        url = f'https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&format=json'
        UrlRequest(url, self.on_geo_success, on_error=self.on_error)
    
    def get_location(self, instance):
        try:
            from plyer import gps
            gps.configure(on_location=self.on_location, on_status=self.on_status)
            gps.start(5000, 0)
            self.result_label.text = '📍 Getting your location...'
        except Exception as e:
            self.result_label.text = f'❌ GPS error: {str(e)}'
    
    def on_location(self, **kwargs):
        lat = kwargs.get('lat')
        lon = kwargs.get('lon')
        if lat and lon:
            self.fetch_weather_by_coords(lat, lon, 'Your Location')
    
    def on_status(self, stype, status):
        pass
    
    def fetch_weather_by_coords(self, lat, lon, location_name):
        self.result_label.text = '⏳ Loading weather...'
        url = f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,windspeed_10m,precipitation,precipitation_probability,snowfall_probability,weathercode&forecast_days=7&timezone=auto'
        UrlRequest(url, self.on_weather_success, on_error=self.on_error)
    
    def on_geo_success(self, req, result):
        try:
            if not result.get('results'):
                self.result_label.text = '❌ City not found.'
                return
            
            geo_data = result['results'][0]
            lat = geo_data['latitude']
            lon = geo_data['longitude']
            city = geo_data['name']
            country = geo_data.get('country', '')
            
            url = f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,windspeed_10m,precipitation,precipitation_probability,snowfall_probability,weathercode&forecast_days=7&timezone=auto'
            self.result_label.text = f'📍 {city}{", " + country if country else ""}\n⏳ Loading...'
            UrlRequest(url, lambda req, data: self.on_weather_success(req, data, city, country), on_error=self.on_error)
        except Exception as e:
            self.result_label.text = f'❌ Error: {str(e)}'
    
    def on_weather_success(self, req, data, city='', country=''):
        try:
            hourly = data.get('hourly', {})
            times = hourly.get('time', [])
            temps = hourly.get('temperature_2m', [])
            winds = hourly.get('windspeed_10m', [])
            precip = hourly.get('precipitation', [])
            rain_prob = hourly.get('precipitation_probability', [])
            snow_prob = hourly.get('snowfall_probability', [])
            codes = hourly.get('weathercode', [])
            
            if not times:
                self.result_label.text = '❌ No data available.'
                return
            
            # Build display text
            display_text = f"📍 {city}{', ' + country if country else ''}\n\n"
            display_text += "🔴 CURRENT CONDITIONS\n"
            display_text += f"🌡️ {temps[0]}°C | 💨 {winds[0]} km/h\n"
            display_text += f"🌧️ Rain: {rain_prob[0] if rain_prob else 0}% | ❄️ Snow: {snow_prob[0] if snow_prob else 0}%\n"
            display_text += f"💧 {precip[0] if precip else 0} mm\n\n"
            display_text += "📅 7-DAY FORECAST\n"
            
            # Show next 7 days summary (simplified)
            days = []
            current_day = ''
            for i, t in enumerate(times):
                day = datetime.fromisoformat(t[:10]).strftime('%a %d')
                if day != current_day:
                    current_day = day
                    days.append({
                        'day': day,
                        'temp': temps[i],
                        'code': codes[i]
                    })
                    if len(days) >= 7:
                        break
            
            for d in days:
                display_text += f"{d['day']}: {self.get_icon(d['code'])} {d['temp']}°C\n"
            
            display_text += f"\n🔄 Updated: {datetime.now().strftime('%H:%M')}"
            
            self.result_label.text = display_text
            self.result_label.text_size = (Window.width - dp(40), None)
            
        except Exception as e:
            self.result_label.text = f'❌ Error: {str(e)}'
    
    def on_error(self, req, error):
        self.result_label.text = f'⚠️ Connection error: {str(error)}'
    
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