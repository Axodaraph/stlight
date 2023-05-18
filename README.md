# semartforo
Servicio web que controla un semáforo inteligente

## Montaje

1. Crear un entorno virtual
```sh
$ python -m venv venv
```
El entorno virtual se activa en linux con
```sh
$ source venv/bin/activate
```
2. Instalar el archivo ```requirements.txt``` con pip
```sh
pip install -r requirements.txt
```
3. Correr el servidor en localhost con Uvicorn
```sh
$ uvicorn app:app --reload
```

Otra variante implica hacer la api accesible por LAN, para lo cual se debe de especificar la dirección IP ```0.0.0.0```. 

Entonces para correr el servidor de esta forma se usa el comdando
```sh
$ uvicorn app:app --reload --host 0.0.0.0
```
**NOTA**: El puerto debe de ser siempre el 8000, no debería de haber problemas si se siguen los pasos tal cual.

4. Luego conectar las PCs en la misma red de área local y cambiar la IP en el archivo ```postTR.py``` por la de la PC que corre el server. Este último archivo se debe de correr en la laptop que accede al servidor.

## Posibles errores

1. Es posible que si se intenta **acceder a la vista de la página web desde otra PC distinta a la que corre el servidor** ocurran errores en la visualización de datos porque la dirección del WebSocket no está configurada *todavía* para ello

2. Si no se carga la página estilizada, la causa es que **Bootstrap emplea archivos online** para su funcionamiento y, **al menos en la primera corrida, debe de estar conectada a Internet**.