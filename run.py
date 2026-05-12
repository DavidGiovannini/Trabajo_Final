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

#1 Ver el tema de que al cambiar el precio de los productos tambien cambie en los presupuestos ya confeccionados, colocar alguna alerta o mensajes de atencion.
#2 Ver de comentar el codigo, routes.py etc mas comentado.
#3 Ver tema de descargar en pdf o excel productos, o cargar una planilla en excel.
#4 Ver en el futuro al hostearlo, probar pdf.
#5 Login Arreglarlo, ver tema de users, Cargar fotos.
#6 chatbox con ia?
#7 Ver embalaje en adicional es un 2.50% del total calculado, ver de agregarlo como un check
#8 Ver adaptación a mobile.
#9 Ver tema seguridad que no quede user y contraseña en el proyecto, ver funcionalidad de cambiar contraseña, enviando un mail etc.
