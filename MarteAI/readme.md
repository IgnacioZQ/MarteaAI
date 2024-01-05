# MarteAI

## Instrucciones

Para ejecutar el código, sigue estos pasos:

1. Instala Python y Django en tu máquina.

2. Abre una terminal o símbolo del sistema y navega hasta el directorio del proyecto.

3. Ejecuta el siguiente comando para iniciar el servidor de desarrollo:

    ```bash
    python manage.py runserver
    ```

    Este comando inicia el servidor de desarrollo de Django, que aloja tu aplicación localmente.

4. Para realizar migraciones para la aplicación MarteAI, ejecuta el siguiente comando:

    ```bash
    python manage.py makemigrations marteai
    ```

    Este comando genera los archivos de migración necesarios para la base de datos en función de los cambios que hayas realizado en los modelos.

5. Finalmente, aplica las migraciones a la base de datos ejecutando el siguiente comando:

    ```bash
    python manage.py migrate
    ```

    Este comando ejecuta los archivos de migración generados y actualiza el esquema de la base de datos en consecuencia.

6. Si deseas crear un superusuario para acceder al panel de administración de Django, ejecuta el siguiente comando:

    ```bash
    python manage.py createsuperuser
    ```

    Este comando te guiará a través del proceso de creación de un superusuario, donde deberás ingresar un nombre de usuario, una dirección de correo electrónico y una contraseña.

## Explicación de los comandos

- `python manage.py runserver`: Este comando inicia el servidor de desarrollo de Django, que te permite ejecutar tu aplicación localmente.

- `python manage.py makemigrations marteai`: Este comando crea archivos de migración para la aplicación MarteAI, en función de los cambios que hayas realizado en los modelos. Estos archivos de migración definen cómo se debe actualizar el esquema de la base de datos.

- `python manage.py migrate`: Este comando aplica los archivos de migración generados a la base de datos, actualizando el esquema y asegurándose de que coincida con el estado actual de tus modelos.

- `python manage.py createsuperuser`: Este comando te permite crear un superusuario para acceder al panel de administración de Django. Deberás ingresar un nombre de usuario, una dirección de correo electrónico y una contraseña.

Ten en cuenta que estas instrucciones asumen que ya has configurado tu proyecto de Django y tienes las dependencias necesarias instaladas. Si encuentras algún problema, consulta la documentación de Django para obtener más ayuda.
