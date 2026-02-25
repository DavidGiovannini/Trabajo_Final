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

#
#
#
#1- Función de Editar, ver de editar datos del cliente, el pedido se edita? poner los lapicitos para editar info.
#2- Agregar un botón de eliminar (Basurerito), en las cards de pedidos para poder eliminar directamente el pedido.
#3- Arreglar botonera de menú (dejar los que mas utilizaría).
#4- Agregar todas las formas de pago en el presupuestador.


#5- Pestaña calendario, con posibilidad de agregar notas.
#6- Seguir con modulo productos y parámetros (configuración), ver de unificar todo en un solo modulo control de stock, arreglar en el resto de pantallas.
#7- Arreglar reporte PDF de presupuesto.
#8- Agregar nueva pestaña de históricos.
#9- Ver tema de las cuotas.
#10- Login/logout/configuración.
#11- chatbox con ia?