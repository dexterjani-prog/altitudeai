from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# Database configuration - supports both PostgreSQL and SQLite
database_url = os.environ.get('DATABASE_URL')

if database_url:
    # Railway provides postgres:// but SQLAlchemy needs postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+pg8000://', 1)
    elif database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+pg8000://', 1)
else:
    # Fallback to SQLite for local development
    database_url = 'sqlite:///app.db'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,  # Verify connections before using
    'pool_recycle': 300,    # Recycle connections after 5 minutes
}

db = SQLAlchemy(app)

class Company(db.Model):
    __tablename__ = 'company'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    website = db.Column(db.String(200))
    industry = db.Column(db.String(100))
    size = db.Column(db.String(50))
    revenue = db.Column(db.String(50))
    country = db.Column(db.String(100))
    state = db.Column(db.String(100))
    city = db.Column(db.String(100))
    signals = db.relationship('Signal', backref='company', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'website': self.website,
            'industry': self.industry, 'size': self.size, 'revenue': self.revenue,
            'country': self.country, 'state': self.state, 'city': self.city,
            'signals': [s.to_dict() for s in self.signals]
        }

class Signal(db.Model):
    __tablename__ = 'signal'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    signal_type = db.Column(db.String(50))
    source = db.Column(db.String(200))
    signal_date = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text)
    confidence_score = db.Column(db.Float)
    
    def to_dict(self):
        return {
            'id': self.id, 'signal_type': self.signal_type, 'source': self.source,
            'signal_date': self.signal_date.isoformat() if self.signal_date else None,
            'description': self.description, 'confidence_score': self.confidence_score
        }

def init_sample_data():
    # Check if data already exists
    if Company.query.first() is not None:
        return
    
    sample_companies = [
        Company(name="Advanced Manufacturing Solutions", website="ams-industrial.com", 
               industry="Manufacturing", size="200-500", revenue="$50M-$100M",
               country="USA", state="Michigan", city="Detroit"),
        Company(name="Precision Automation Corp", website="precisionauto.com",
               industry="Automation", size="500-1000", revenue="$100M-$500M",
               country="USA", state="Ohio", city="Cleveland"),
        Company(name="Industrial IoT Systems", website="iiot-sys.com",
               industry="Technology", size="50-200", revenue="$10M-$50M",
               country="USA", state="Texas", city="Houston"),
        Company(name="Smart Factory Solutions", website="smartfactory.io",
               industry="Manufacturing", size="1000-5000", revenue="$500M-$1B",
               country="USA", state="California", city="San Jose"),
        Company(name="Process Control Industries", website="pci-controls.com",
               industry="Process Control", size="500-1000", revenue="$100M-$500M",
               country="USA", state="Pennsylvania", city="Pittsburgh"),
    ]
    
    for company in sample_companies:
        db.session.add(company)
    db.session.commit()
    
    signals = [
        Signal(company_id=1, signal_type="hiring", source="indeed.com",
              description="Hiring Senior Network Engineer with Cisco IE experience",
              confidence_score=0.85),
        Signal(company_id=1, signal_type="contract", source="sam.gov",
              description="Awarded $2.5M smart manufacturing upgrade contract",
              confidence_score=0.95),
        Signal(company_id=2, signal_type="expansion", source="press release",
              description="Announced new facility expansion in Austin, TX",
              confidence_score=0.90),
        Signal(company_id=3, signal_type="tech_mention", source="linkedin.com",
              description="Posted about implementing Industrial Ethernet solutions",
              confidence_score=0.75),
        Signal(company_id=4, signal_type="hiring", source="indeed.com",
              description="Multiple openings for OT Security Specialists",
              confidence_score=0.88),
    ]
    
    for signal in signals:
        db.session.add(signal)
    db.session.commit()

# Create tables and init data on startup
with app.app_context():
    db.create_all()
    init_sample_data()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/companies')
def get_companies():
    state = request.args.get('state', '')
    industry = request.args.get('industry', '')
    size = request.args.get('size', '')
    signal_type = request.args.get('signal_type', '')
    
    query = Company.query
    if state:
        query = query.filter(Company.state.ilike(f'%{state}%'))
    if industry:
        query = query.filter(Company.industry.ilike(f'%{industry}%'))
    if size:
        query = query.filter(Company.size == size)
    if signal_type:
        query = query.join(Signal).filter(Signal.signal_type == signal_type)
    
    return jsonify([c.to_dict() for c in query.all()])

@app.route('/api/states')
def get_states():
    return jsonify([s[0] for s in db.session.query(Company.state).distinct().all() if s[0]])

@app.route('/api/industries')
def get_industries():
    return jsonify([i[0] for i in db.session.query(Company.industry).distinct().all() if i[0]])

@app.route('/api/stats')
def get_stats():
    return jsonify({
        'total_companies': Company.query.count(),
        'total_signals': Signal.query.count(),
        'hiring_signals': Signal.query.filter_by(signal_type='hiring').count(),
        'contract_signals': Signal.query.filter_by(signal_type='contract').count()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
