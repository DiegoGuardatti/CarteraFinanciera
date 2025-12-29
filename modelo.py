from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Broker(db.Model):
    __tablename__ = 'broker'
    Id_Broker = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Nombre = db.Column(db.String(60), nullable=False)
    Comision = db.Column(db.Float, nullable=False)
    Asesor = db.Column(db.String(60), nullable=False)
    comitentes = db.relationship('Comitente', backref='broker', lazy=True)

class Comitente(db.Model):
    __tablename__ = 'comitente'
    Id_Comitente = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Titular = db.Column(db.String(60), nullable=False)
    Numero = db.Column(db.Integer, nullable=False)
    Id_Broker = db.Column(db.Integer, db.ForeignKey('broker.Id_Broker'), nullable=False)

class InstrumentoFinanciero(db.Model):
    __tablename__ = 'instrumento_financiero'
    Id_InstrumentoFinanciero = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Nombre = db.Column(db.String(60), nullable=False)

class Ticker(db.Model):
    __tablename__ = 'ticker'
    Id_Ticker = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Nombre_Ticker = db.Column(db.String(60), nullable=False)
    Descripcion = db.Column(db.String(60), nullable=False)
    Id_InstrumentoFinanciero = db.Column(db.Integer, db.ForeignKey('instrumento_financiero.Id_InstrumentoFinanciero'), nullable=False)
    instrumento_financiero = db.relationship('InstrumentoFinanciero', backref='tickers', lazy=True)

class Activo(db.Model):
    __tablename__ = 'activo'
    Id_Activo = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Id_Broker = db.Column(db.Integer, db.ForeignKey('broker.Id_Broker'), nullable=False)
    Id_Comitente = db.Column(db.Integer, db.ForeignKey('comitente.Id_Comitente'), nullable=False)
    Id_Ticker = db.Column(db.Integer, db.ForeignKey('ticker.Id_Ticker'), nullable=False)
    Precio_Dolar_MEP_Compra = db.Column(db.Float, nullable=False)
    Fecha_Hora_Compra = db.Column(db.DateTime, nullable=False)
    Precio_Compra = db.Column(db.Float, nullable=False)
    Cantidad_Nominales_Compra = db.Column(db.Float, nullable=False)
    Comision_Broker = db.Column(db.Float, nullable=False)
    Total_Pesos_Compra = db.Column(db.Float, nullable=False)
    Total_Dolares_Compra = db.Column(db.Float, nullable=False)
    Precio_Dolar_MEP_Venta = db.Column(db.Float, nullable=True)
    Fecha_Hora_Venta= db.Column(db.DateTime, nullable=True)
    Precio_Venta = db.Column(db.Float, nullable=True)
    Cantidad_Nominales_Venta = db.Column(db.Float, nullable=True)
    Total_Pesos_Venta = db.Column(db.Float, nullable=True)
    Total_Dolares_Venta = db.Column(db.Float, nullable=True)
    Activo_Estado = db.Column(db.String(20), nullable=False, default='EN_CARTERA')

    broker = db.relationship('Broker', backref='compras', lazy=True)
    comitente = db.relationship('Comitente', backref='compras', lazy=True)
    ticker = db.relationship('Ticker', backref='compras', lazy=True)
