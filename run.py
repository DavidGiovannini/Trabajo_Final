from app import create_app

app = create_app()

if __name__ == "__main__":
    # LAN: 0.0.0.0 permite que otras PCs de la red entren
    app.run(host="0.0.0.0", port=5000, debug=True)

#-----Subir al repo-----
#git add .
#git commit -m "Comentario"
#git push origin main

#-----Bajar del repo-----
#git pull origin main

# BUGS

#- Ver el tema de que al cambiar el precio de los productos tambien cambie en los presupuestos ya confeccionados.

#5- Pestaña calendario, con posibilidad de agregar notas.
#6- Seguir con modulo productos y parámetros (configuración), ver de unificar todo en un solo modulo control de stock, arreglar en el resto de pantallas.
#7- Arreglar reporte PDF de presupuesto. Ver tema de pdf hacerlo de acceso publico o reveer opciones para que lo puedan descargar.
#8- Agregar nueva pestaña de históricos.
#9- Ver tema de las cuotas. Ver tema iva como funciona.
#10- Login/logout/configuración.
#11- chatbox con ia?