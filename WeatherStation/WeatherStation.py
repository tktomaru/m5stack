from m5stack import lcd, btnA
import m5stack as m5
import utime, machine, urequests, ujson
import ntptime

lcd_mute    = False # Global
g_api_key   = "input your key"# Global input your api key
g_city_code = 0 # Global input your city code

NTP_DELTA   =  (9*60*60)# define

# お天気クラス
class Weather:
    def __init__(self):
        self.base_weather_url = 'http://api.openweathermap.org/data/2.5/weather?id={}&units=metric&APPID={}'
        self.base_forecast_url = 'http://api.openweathermap.org/data/2.5/forecast?id={}&APPID={}&units=metric&cnt=8'
        self.api_key = g_api_key
        self.prefectures = [g_city_code]

        lcd.setCursor(0, 0)
        lcd.setColor(lcd.WHITE)
        lcd.font(lcd.FONT_DejaVu24)
        self.fw, self.fh = lcd.fontSize()

    # "*"をnum個表示する
    def diaplay_asta( self, num, asta1="*" ):
      asta = ""
      for ii in range(num):
        asta = asta + asta1
      lcd.print(asta, 0, self.fw * 0)
      num = num + 1
      return num

    # サーバーから天気予報を取得する
    def get_forecast(self, prefecture):
        n_asta = 1
        n_asta = self.diaplay_asta( n_asta )
        response = urequests.get(self.base_forecast_url.format(prefecture, self.api_key))
        n_asta = self.diaplay_asta( n_asta )
        json = response.json()
        n_asta = self.diaplay_asta( n_asta )
        forecastsList = ""
        if 'list' in json:
          forecastsList = json['list']
        else:
          lcd.print("fail get list", 10, self.fw * 0)
          return -1
          
        n_asta = self.diaplay_asta( n_asta )
        outline = 1
        countlist = 1
        self.weatherList = []
        first = 0
        for hour3 in forecastsList:
          temp = 0
          pressure = 0
          humidity = 0
          temp_min = 0
          temp_max = 0
          title = ""
          description = ""
          dt = 0
          icon = ""
          if 'dt' in hour3:
            dt = hour3["dt"]
          if 'weather' in hour3:
            weather = hour3['weather'][0]
            title, description, icon = self.get_1weather( weather )
          if 'main' in hour3:
            main = hour3["main"]
            temp, pressure, humidity, temp_min, temp_max = self.get_1main( main )
          self.weatherList.append( [prefecture, title, description, pressure, temp, humidity, temp_min, temp_max, icon, outline, dt] )
          outline = outline + 1
          countlist = countlist + 1

    # 3hごとの気温予報を表示する
    def display_forecast(self):
        outline = 1
        now = time.localtime()
        day  = now[2]
        nextday = day
        disptime = [0,3,6,9,12,15,18,21]
        lcd.clear()
        stime = time.localtime(self.weatherList[0][10] + NTP_DELTA)
        sday = stime[2] + 1
        lcd.print("{}  dt  temp  min   max".format(sday), 0, self.fw * 0)
        for ws in self.weatherList:
            stime = time.localtime(ws[10] + NTP_DELTA)
            sday = stime[2] + 1
            stime = stime[3]
            ws4 = "{:.1f}".format(ws[4])
            ws4 = "{:0>4}".format(ws4)
            ws6 = "{:.1f}".format(ws[6])
            ws6 = "{:0>4}".format(ws6)
            ws7 = "{:.1f}".format(ws[7])
            ws7 = "{:0>4}".format(ws7)
            s_tmp = "  {:0>2}  {}  {}  {}".format( stime, ws4, ws6, ws7)
            lcd.print(s_tmp, 30, self.fw * outline)
            lcd.image(0, 24*outline, "/sd/icon/p24/" + ws[8] + ".jpg", 0, lcd.JPG)
            outline = outline + 1

    # お天気アイコン（大）表示
    def display_forecast_image(self):
        now = time.localtime()
        day  = now[2]
        nextday = day + 1
        lcd.clear()
        dispcount = 1
        disptime = [0,3,6,9,12,15,18,21]
        stime = time.localtime(self.weatherList[0][10] + NTP_DELTA)
        startday = stime[2] + 1
        for ws in  self.weatherList:
            stime = time.localtime(ws[10] + NTP_DELTA)
            sday = stime[2] + 1
            stime = stime[3]
            row = 0
            if(dispcount-1 <= 0):
              row = 0
            else:
              row = int((dispcount - 1) / 3)
            col = int((dispcount -1 ) % 3)
            if( dispcount <= 9):
                lcd.print(str(stime % 12), (80 + 24) * col, 80 * row)
                lcd.image((80 + 24) * col + 24, 80 * row, "/sd/icon/p80/" + ws[8] + ".jpg", 0, lcd.JPG)
                dispcount = dispcount + 1
        lcd.print(str(startday), (80 + 24) * 2, 80 * 2)

    # forecastのjsonのmainを取得する
    def get_1main( self , main):
      m_t = 0
      m_p = 0
      m_h = 0
      m_t_min = 0
      m_t_max = 0
      if 'temp' in main :
        m_t = main['temp']
      if 'pressure' in main :
        m_p = main['pressure']
      if 'humidity' in main :
        m_h = main['humidity']
      if 'temp_min' in main :
        m_t_min = main['temp_min']
      if 'temp_max' in main :
        m_t_max = main['temp_max']
      return (float(m_t), float(m_p), float(m_h), float(m_t_min), float(m_t_max))

    # forecastのjsonのweatherを取得する
    def get_1weather( self, weather):
        title = ""
        description = ""
        if 'main' in weather:
          title = weather['main']
        if 'description' in weather:
          description = weather['description']
        if 'icon' in weather:
          icon = weather['icon']
        return (title, description, icon)

# Aボタンを押した時の動作
# 表示／非表示切り替え
def on_AwasReleased():
    global lcd_mute
    if lcd_mute:
        lcd_mute = False
    else:
        lcd_mute = True
    if lcd_mute == True:
        lcd.setBrightness(0)
    else :
        lcd.setBrightness(200)

# Bボタンを押した時の動作
# 3hごとのお天気アイコン表示（大）
def on_BwasReleased():
    for prefecture in weather.prefectures:
        try:
            weather.get_forecast(prefecture)
            weather.display_forecast_image()
        except Exception as e:
            print(e)

# Cボタンを押した時の動作
# 3hごとのお天気情報（気温）表示
def on_CwasReleased():
    for prefecture in weather.prefectures:
        try:
            weather.get_forecast(prefecture)
            weather.display_forecast()
        except Exception as e:
            print(e)
    
# メイン処理はここから
lcd.clear()
lcd.print("booting", 0, 0)

lcd.image(0, 0, "/sd/logo.jpg", 0, lcd.JPG)

time.sleep(1)

# WiFi設定
import wifiCfg
wifiCfg.autoConnect(lcdShow=True)

# RTC設定
utime.localtime(ntptime.settime())

# 天気
weather = Weather()

# 初期の天気表示
for prefecture in weather.prefectures:
    try:
        weather.get_forecast(prefecture)
        weather.display_forecast_image()
    except Exception as e:
        print(e)

btnA.wasReleased(on_AwasReleased)
btnB.wasReleased(on_BwasReleased)
btnC.wasReleased(on_CwasReleased)

while True:
    # 1hour周期で自動取得
    time.sleep(60*60)
    for prefecture in weather.prefectures:
        try:
            weather.get_forecast(prefecture)
            weather.display_forecast_image()
        except Exception as e:
            print(e)

