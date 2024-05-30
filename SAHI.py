from sahi.models.yolov8 import Yolov8DetectionModel
from sahi.predict import get_sliced_prediction
from sahi.utils.file import save_json
import matplotlib.pyplot as plt
import cv2
import simplekml
from PIL import Image
from geolocalizador import Geolocalizacion
import numpy as np
import os


directorio_Actual = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(directorio_Actual, 'modelo','best.pt')
image_path = os.path.join(directorio_Actual, 'modelo','Pruebas.JPG')
dpi = 96
def get_PixelCentral(image_path):
    image = cv2.imread(image_path)
    # Obtener las dimensiones de la imagen
    alto, ancho = image.shape[:2]  # shape devuelve (alto, ancho, canales)
    centro_x = ancho // 2
    centro_y = alto // 2
    # Imprimir las dimensiones
    print(f"Width: {ancho} pixels")
    print(f"Height: {alto} pixels")
    return ancho, alto, centro_x, centro_y

yolov8_model = Yolov8DetectionModel(
    model_path=model_path,  # Ruta al modelo entrenado
    confidence_threshold=0.5,
    device='cuda'  # Usa 'cpu' si no tienes una GPU
)

# Realizar la inferencia con SAHI


image = Image.open(image_path)
result = get_sliced_prediction(
    image=image_path,
    detection_model=yolov8_model,
    slice_height=512,  # Altura de los slices
    slice_width=512,   # Ancho de los slices
    overlap_height_ratio=0.2,  # Proporción de superposición vertical
    overlap_width_ratio=0.2    # Proporción de superposición horizontal
)

# Guardar los resultados
save_json(result.to_coco_annotations(), 'output.json')

# Obtener las dimensiones y el centro de la imagen
ancho, alto, centro_x_img, centro_y_img = get_PixelCentral(image_path)

# Lista para almacenar las coordenadas geográficas
coordenadas_geograficas = []
kml = simplekml.Kml()

# Procesar cada predicción para obtener las coordenadas centrales en píxeles y luego convertirlas a latitud y longitud
for prediction in result.object_prediction_list:
    bbox = prediction.bbox
    minx, miny, maxx, maxy = int(bbox.minx), int(bbox.miny), int(bbox.maxx), int(bbox.maxy)
    center_x = (minx + maxx) // 2
    center_y = (miny + maxy) // 2
    print(f"Pixel central de la caja: Min X: {center_x}, Min Y: {center_y}")

    # Convertir píxeles a coordenadas geográficas
    lon = center_x - ancho
    lat = center_y - alto
    geolocalizacion = Geolocalizacion(image, lon, lat)

    coordenadas_lat, coordenadas_lon = geolocalizacion.obtener_geolocalizacion()

    # Agregar las coordenadas a la lista
    coordenadas_geograficas.append((coordenadas_lat, coordenadas_lon))

# Agregar las coordenadas geográficas al KML
for latitud, longitud in coordenadas_geograficas:
    kml.newpoint(name="Predicción", coords=[(longitud, latitud)])

# Guardar el archivo KML
kml.save("predicciones.kml")

# Visualización de los resultados
def visualize_predictions(image,imagen_np, predictions):

    plt.figure(figsize=(image.width / dpi, image.height / dpi), dpi=dpi)
    for prediction in predictions:
        bbox = prediction.bbox
        pt1 = (int(bbox.minx), int(bbox.miny))
        pt2 = (int(bbox.maxx), int(bbox.maxy))
        cv2.rectangle(imagen_np, pt1, pt2, (255, 0, 0), 2)
        label = f"{prediction.category}: {prediction.score.value:.2f}"
        cv2.putText(imagen_np, label, pt1, cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
    plt.imshow(imagen_np)
    plt.axis('off')
    plt.show()

# Visualizar los resultados

image_np = np.array(image)
visualize_predictions(image,image_np, result.object_prediction_list)
