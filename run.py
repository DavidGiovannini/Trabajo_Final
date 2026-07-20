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
