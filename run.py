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

#1- Ver la fecha de nuevo no aparece en las cards de pedidos.
#2- Arreglar el formulario al apretar el botón "Ver", que el cancelar este mas centrado y que el nombre sea el numero del pago.
#3- Arreglar el funcionamiento cuando se elimina un pago, que no solo te actualice el lo que debe sino que te permita crear otro pago, hoy esto esta bugeado y te abre el formulario de "Ver".
#4- Agregar un botón de eliminar (Basurerito), en las cards de pedidos para poder eliminar directamente el pedido.
#5- Arreglar botonera de menú (dejar los que mas utilizaría)
#6- Agregar el botón de wpp, al lado del telefono del cliente
#7- Ver de Arreglar el formulario para agregar mas formas de pago en el presupuestador y ver lo de tarjeta para agregar las cuotas.
#8- Seguir con modulo productos y parámetros.