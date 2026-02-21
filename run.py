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
#1- Fecha de actualización en los pedidos.
#2- El desplegar/contraer de las cards en pedidos, no funciona al tocar toda la card.
#3- La sección de Monto Pagado que esté y no que se desplegue al seleccionar el tipo.
#4- El botón "Adjuntar Comprobante", que esté debajo de el campo de "Monto Pagado" y que su carga, asi como tambien el archivo adjunto que se vea al lado.
#5- Que en el título de este modal diga el numero del pago (ID).
#6- Limpiar codigo repetido el styles.css

#7- Hacer la grilla con los pagos en la parte de forma de pago haciendo que la seña aparezca como primer pago, en los casos que tenga.