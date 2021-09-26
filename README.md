# Experimento 1
## Proceso de instalación:
1. Descargar Código: [Aquí](https://uniandes-my.sharepoint.com/personal/al_caceres_uniandes_edu_co/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fal%5Fcaceres%5Funiandes%5Fedu%5Fco%2FDocuments%2FCiclo%203%2FArquitecturas%20de%20Software%20Agil%2Fmqtt%5Fpractice%5Ffinal%2Ezip&parent=%2Fpersonal%2Fal%5Fcaceres%5Funiandes%5Fedu%5Fco%2FDocuments%2FCiclo%203%2FArquitecturas%20de%20Software%20Agil&originalPath=aHR0cHM6Ly91bmlhbmRlcy1teS5zaGFyZXBvaW50LmNvbS86dTovZy9wZXJzb25hbC9hbF9jYWNlcmVzX3VuaWFuZGVzX2VkdV9jby9FZHRfWkVpT2I2aEZtVllpY1Q3Zl9pRUJrZkpjLUVmUXNlZW9tbmFoQ0JueEpRP3J0aW1lPWpaV2tsbVIxMlVn).
2. Instalar la variable entorno: py -m pip install --user virtualenv
3. Activarla: .\venv\Scripts\activate
4. Dentro de (ven), correr el siguiente comando en la raiz del proyecto: pip install -r requirements.txt
5. Para ejecutar script: python controller.py

Nota: Realizar la ejecución en el sistema operativo ubuntu 20.04

## Evidencias:
1. Ver Vídeo: [Aquí](https://www.youtube.com/watch?v=YQTgIsajFrY&ab_channel=darioherrera).
2. Descargar el log: [Aquí](https://uniandes-my.sharepoint.com/:x:/g/personal/d_herrerag_uniandes_edu_co/ETHYxCz22-1FpqGx38CHQgYBzqHSmTT_lFZ8VgDzj_Qfcw?e=i8HQRD).

## Explicacion de log de eventos:
Esta conformado por 4 columnas: 
- TIME: Estampa de tiempo en la que se registro el evento en el log durante la simulación.
- NAME: Nombre de los microservicios implicados en la simulación. 
  * Controller -> Microservicio usado para controlar la simulación. Se encarga de preparar los otros microservicios para la simulación, además de registrar todo lo que ocurre durante esta (genera el log).
  * Receptor -> Microservicio que simulara al receptor en la dedundancia activa propuesta. Transmite la petición de admisión a los microservisos de admisión.
  * AdmissionServiceX (para X = [1,3]) -> Microservicios que simularan los módulos de admisones.Procesan la petición de admisión solicitada.
- FLAG: Esta columna clasifica los eventos generados durante la simulación acorde a su valor, como se describe a continuación:
  * setup -> Señala un evento asociada a la configuración de la simulación.
  * running -> Indica que la simulación inicio su ejecución.
  * request -> Indica que el microservicio Receptor ha generado una petición de admisión a los microserviso de admisión.
  * received -> Indica que un microservicio de admisión a recibido una solicitud.
  * working -> indica que un microservicio de admisión esta procesando una solicitud.
  * success -> Inidica que un microservicio de admisión a procesado una solicitud satisfactoriamente.
  * error -> Indica un error en el microservicio.
  * switch -> Indica cuando el Receptor cambio de microservicio principal a uno de respaldo.
  * stopped -> indica que la simulación se detuvo
  * ended -> indica que la simulación ha terminado.
- INFO: Muestra informacion adicional sobre el evento generado.
## Ejecucion en Docker
1. Construir imagen: ```docker build t lab-miso:1```
2. Generar contenedor con imagen construida: ```docker run --name lab-exec lab-miso:1```
3. Esperar hasta que en la consola salga el mensaje "This is just an error to end the process. Please close this terminal." para cerrar la terminal de ejecución.
4. Extraer log de eventos generado: ```docker cp lab-exec:/app/simulation_log.xlsx .```
5. Detener ejecucion de contenedor: ```docker stop lab-exec```

Si desea ejecutar el programa con bash interactivo:
1. Crear seccion interactiva con contenedor: ```docker run -it lab-miso:1 bash```
2. Ejecutar programa en seccion interactiva: ```./start.sh```
