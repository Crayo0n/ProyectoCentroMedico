from flask import Flask
from flask_mysqldb import MySQL

from config import Config

mysql= MySQL()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    mysql.init_app(app)
    
    from controllers.DoctoresController import DoctoresBP
    app.register_blueprint(DoctoresBP)
    
    from controllers.PacientesController import PacientesBP
    app.register_blueprint(PacientesBP)
    
    from controllers.GestionController import GestionBP
    app.register_blueprint(GestionBP)
    
    from controllers.RecetaController import RecetaBP
    app.register_blueprint(RecetaBP)
    
    return app

if __name__ == '__main__':
    app=create_app()
    app.run(port=3000, debug=True)
