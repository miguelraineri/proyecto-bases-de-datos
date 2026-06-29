## Proceso de desarrollo

Para desarrollar el sitio web, primero definimos qué consultas necesitábamos realizar en la base de datos. Antes de programar la interfaz, pensamos qué información queríamos mostrar y cómo se relacionaban las tablas entre sí.

En esa etapa trabajamos principalmente las consultas SQL, usando elementos como SELECT, JOIN, filtros y relaciones entre tablas. La consulta más importante era la que permitía ver los envíos junto con su carga asociada, relacionando tablas como Envio, Carga, Empresa, Ruta, Estado Envio y Medio Transporte.

Después de tener más claras las consultas que queríamos usar, pedimos ayuda a ChatGPT para construir un sitio web simple que pudiera ejecutar esas consultas y mostrar los resultados de forma visual. Esto lo hicimos porque no sabíamos cómo crear una interfaz web desde cero, pero sí teníamos claro qué necesitábamos consultar desde la base de datos.

El sitio web fue desarrollado con Streamlit, ya que permite crear una interfaz básica en Python sin tener que programar HTML, CSS o JavaScript. La idea fue mantener el sitio lo más simple posible, enfocándonos en que permitiera probar las consultas y mostrar el funcionamiento del POC.

## Archivo principal

El archivo principal del sitio web es:

base.2.py

## Ejecución

Para ejecutar el sitio web se debe usar el siguiente comando:

python -m streamlit run base.2.py


## Nota

El código del sitio web fue construido con apoyo de ChatGPT a partir de las consultas SQL y funcionalidades que definimos previamente para el POC.
