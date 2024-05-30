from PIL import Image
from gmplot import gmplot
from pyproj import Proj, transform
import math
import exifread

class Geolocalizacion:

    def __init__(self,imagen,pixels_ancho,pixels_alto):
        self.imagen = imagen
        self.pixels_ancho = pixels_ancho
        self.pixels_alto = pixels_alto

    # Función para convertir las coordenadas GPS en formato EXIF a grados decimales
    def convertir_a_grados(self, val):
        return val[0] + (val[1] / 60.0) + (val[2] / 3600.0)

    # Cargar la imagen y extraer los datos EXIF
    def conseguir_datos_exif(self):
        exif_data = self.imagen._getexif()

        # Asegurarse de que hay datos EXIF
        if not exif_data:
            raise ValueError("No se encontraron datos EXIF en la imagen.")

        # Extraer la información GPS
        gps_info = exif_data.get(34853)  # 34853 es el tag de GPSInfo
        if not gps_info:
            raise ValueError("No se encontraron datos GPS en la imagen.")

        # Extraer latitud y longitud del GPSInfo
        lat = self.convertir_a_grados(gps_info[2])
        if gps_info[1] == 'S':
            lat = -lat

        lon = self.convertir_a_grados(gps_info[4])
        if gps_info[3] == 'W':
            lon = -lon

        return lat, lon
    def obtener_geolocalizacion(self):
        lat,lon = self.conseguir_datos_exif()
        # Convertir a UTM
        zona_UTM = int((lon + 180) / 6) + 1
        hemisferio_UTM = 'N' if lat >= 0 else 'S'

        # Definir el sistema de coordenadas
        wgs84 = Proj(proj='latlong', datum='WGS84')
        utm = Proj(proj='utm', zone=zona_UTM, datum='WGS84', south=lat < 0)

        # Convertir de latitud/longitud a UTM
        utm_x, utm_y = transform(wgs84, utm, lon, lat)

        # Calcular las nuevas coordenadas UTM después del desplazamiento
        grados = 42
        altura_dron = 14
        distancia_extremo = altura_dron * math.tan(math.radians(grados))

        extremo_x1 = distancia_extremo * math.cos(math.radians(36.87))
        extremo_y1 = distancia_extremo * math.sin(math.radians(36.87))

        anchuraPixel, alturaPixel = self.imagen.size
        anchura_metros = 2 * extremo_x1
        altura_metros = 2 * extremo_y1

        anchuraMxP = anchura_metros / anchuraPixel
        alturaMxP = altura_metros / alturaPixel

        # Desplazamiento en UTM
        utm_x_nuevo = utm_x - self.pixels_ancho  * anchuraMxP
        utm_y_nuevo = utm_y - self.pixels_alto  * alturaMxP

        # Convertir de UTM a grados decimales
        lon_final, lat_final = transform(utm, wgs84, utm_x_nuevo, utm_y_nuevo)

        # Imprimir resultados

        print(f"Coordenadas originales: Latitud={lat}, Longitud={lon}")
        print(f"Coordenadas UTM: X={utm_x}, Y={utm_y}, Zona={zona_UTM}{hemisferio_UTM}")
        print(f"Nuevas coordenadas UTM: X={utm_x_nuevo}, Y={utm_y_nuevo}")
        print(f"Nuevas coordenadas geográficas: Latitud={lat_final}, Longitud={lon_final}")

        # Graficar en el mapa
        gmap = gmplot.GoogleMapPlotter(lat, lon, 12)
        gmap.marker(lat, lon, color='cornflowerblue')
        gmap.marker(lat_final, lon_final, color='red')
        gmap.draw("location.html")
        return lat_final, lon_final