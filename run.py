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

#1- Ver el tema de que cuando apretas el boton de ubicacion y volves no te deja hacer nada, ver si pasa con wpp y que tambien coloque la ciudad y pais en el domicilio para que la busqueda sea mas exacta.
#2- Ver el tema de que al cambiar el precio de los productos tambien cambie en los presupuestos ya confeccionados.
#3- Ver de comentar el codigo, routes.py etc mas comentado.
#5- Pestaña calendario, con posibilidad de agregar notas.
#6- Ver tema de descargar en pdf o excel productos, o cargar una planilla en excel.
#7- Arreglar reporte PDF de presupuesto. Ver tema de pdf hacerlo de acceso publico o reveer opciones para que lo puedan descargar.
#8- Agregar nuevos indicadores en el dashboard, con posibilidad de agrandarlos, cant stock, ventas, productos mas vendidos, etc.
#9- Ver crear remito ademas del resupuesto (pdf con indicaciones para los empleados)
#10- Login Arreglarlo, ver tema de users, Cargar fotos.
#11- chatbox con ia?
#12- Presupeustos que no sean obligatorio todos los datos, unicamente con nombre/telefono si