from app import create_app

app = create_app()

if __name__ == "__main__":
    import os
    # debug=True solo si la variable de entorno FLASK_DEBUG=1 está activa
    # En producción dejar FLASK_DEBUG sin definir o en 0
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=5000, debug=debug)

#-----Subir al repo-----
#git add .
#git commit -m "Comentario"
#git push origin main

#-----Bajar del repo-----
#git pull origin main

# BUGS

#2- Ver el tema de que al cambiar el precio de los productos tambien cambie en los presupuestos ya confeccionados.
#3- Ver de comentar el codigo, routes.py etc mas comentado.
#4- Adicionales con cargo tambien dependan del tipo de modelo elegido. ver de quitar lo del ajuste en el presupuesto. Organizar botones de confirmación, que haya uno para el constructor y otro para adicionales, ver de 
# meter adicionales que tambien tienen diferentes tipos de precios segun si es mueble, alacena o mesada acero y puede no tener valor.
#6- Ver tema de descargar en pdf o excel productos, o cargar una planilla en excel.
#7- Ver tema de pdf hacerlo de acceso publico o reveer opciones para que lo puedan descargar. Ver en el futuro al hostearlo, probarlo
#10- Login Arreglarlo, ver tema de users, Cargar fotos.
#11- chatbox con ia?
#13- Ver embalaje en adicional es un 2.50% del total calculado, ver de agregarlo como un check
#14- Ver adaptación a mobile.