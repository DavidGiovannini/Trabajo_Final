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

#2- Ver el tema de que al cambiar el precio de los productos tambien cambie en los presupuestos ya confeccionados.
#3- corregir y optimizar codigo eliminar duplicados, hacer comentarios, dividir entre css, js, html y el back comentarlo.
#4- Arreglar presupuestos para muebles a medida, ver como hacer la funcionalidad. Me gusta mucho la del constructor por defecto que te tire el mas cercano pero q tambien haya una forma de elegir o buscar manual, o de elejir el del constructor por defecto q ahora solo te lo muestra, o de particionar es decir agregar 2 bases con la misma medida, ver como hacer. 
#5- Pestaña calendario, con posibilidad de agregar notas.
#6- Ver tema de descargar en pdf o excel productos, o cargar una planilla en excel.
#7- Arreglar reporte PDF de presupuesto. Ver tema de pdf hacerlo de acceso publico o reveer opciones para que lo puedan descargar.
#8- Agregar nuevos indicadores en el dashboard, con posibilidad de agrandarlos, cant stock, ventas, productos mas vendidos, etc.
#9- Ver tema iva como funciona.
#10- Login Arreglarlo, ver tema de users, Cargar fotos.
#11- chatbox con ia?
# En la carga de presupuestos, que el boton limpiar todo, tambien limpie el resumen. 