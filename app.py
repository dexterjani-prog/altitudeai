from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import random

app = Flask(__name__)

# Database configuration - uses Railway PostgreSQL or SQLite fallback
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Handle Railway's postgres:// format
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    # Use pg8000 driver (pure Python, no compilation needed)
    if 'postgresql://' in database_url and 'pg8000' not in database_url:
        database_url = database_url.replace('postgresql://', 'postgresql+pg8000://', 1)
else:
    # SQLite fallback for local development
    database_url = 'sqlite:////tmp/altitudeai.db'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300
}

db = SQLAlchemy(app)

# Database Models
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
    # AI-generated fields
    ai_summary = db.Column(db.Text)
    buying_intent_score = db.Column(db.Integer, default=0)
    ai_recommendation = db.Column(db.String(50))
    last_analyzed = db.Column(db.DateTime, default=datetime.utcnow)
    
    signals = db.relationship('Signal', backref='company', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'website': self.website,
            'industry': self.industry,
            'size': self.size,
            'revenue': self.revenue,
            'country': self.country,
            'state': self.state,
            'city': self.city,
            'ai_summary': self.ai_summary,
            'buying_intent_score': self.buying_intent_score,
            'ai_recommendation': self.ai_recommendation,
            'last_analyzed': self.last_analyzed.isoformat() if self.last_analyzed else None,
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
    # AI insight for this signal
    ai_insight = db.Column(db.Text)
    impact_score = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'signal_type': self.signal_type,
            'source': self.source,
            'signal_date': self.signal_date.isoformat() if self.signal_date else None,
            'description': self.description,
            'confidence_score': self.confidence_score,
            'ai_insight': self.ai_insight,
            'impact_score': self.impact_score
        }

# AI Analysis Functions (Simulated)
def generate_ai_summary(company_name, industry, signals):
    """Generate AI summary based on company signals"""
    signal_types = [s.signal_type for s in signals]
    
    if 'hiring' in signal_types and 'contract' in signal_types:
        return f"{company_name} shows strong buying signals: active recruitment for technical roles combined with recent government contracts indicates immediate infrastructure investment needs. High priority target for industrial networking solutions."
    elif 'hiring' in signal_types:
        return f"{company_name} is expanding technical capabilities through strategic hiring. Recent job postings suggest upcoming network infrastructure projects. Good timing for engagement."
    elif 'contract' in signal_types:
        return f"{company_name} secured significant funding through government contracts. Budget availability confirmed for modernization initiatives. Approach with solution-oriented proposal."
    elif 'expansion' in signal_types:
        return f"{company_name} undergoing facility expansion, creating natural demand for scalable network infrastructure. Position solutions as growth-enabling."
    elif 'tech_mention' in signal_types:
        return f"{company_name} actively discussing Industry 4.0 initiatives publicly. Early engagement opportunity before RFP stage."
    else:
        return f"{company_name} is a {industry} company with standard monitoring indicators. Maintain in pipeline for future qualification."

def calculate_buying_intent(signals):
    """Calculate buying intent score 0-100 based on signals"""
    score = 0
    
    for signal in signals:
        if signal.signal_type == 'hiring':
            score += 25
        elif signal.signal_type == 'contract':
            score += 30
        elif signal.signal_type == 'expansion':
            score += 20
        elif signal.signal_type == 'tech_mention':
            score += 15
        
        # Boost for high confidence
        if signal.confidence_score > 0.8:
            score += 10
    
    # Cap at 100
    return min(score, 100)

def get_recommendation(score, signals):
    """Get AI recommendation based on score"""
    if score >= 80:
        return "Contact Immediately"
    elif score >= 60:
        return "Schedule Call This Week"
    elif score >= 40:
        return "Add to Nurture Campaign"
    else:
        return "Monitor for Changes"

def generate_signal_insight(signal_type, description):
    """Generate AI insight for individual signal"""
    insights = {
        'hiring': [
            "Technical hiring indicates infrastructure expansion budget approved",
            "Network engineer roles suggest imminent equipment refresh cycle",
            "OT security hires signal IIoT initiative underway"
        ],
        'contract': [
            "Government funding secured - procurement process likely active",
            "Federal contract requires compliance-grade networking equipment",
            "Budget cycle confirmed - decision makers accessible"
        ],
        'expansion': [
            "New facility requires complete network infrastructure build-out",
            "Geographic expansion creates multi-site connectivity needs",
            "Capacity increase demands robust industrial ethernet backbone"
        ],
        'tech_mention': [
            "Digital transformation messaging indicates executive sponsorship",
            "Industry 4.0 keywords suggest budget allocation for modernization",
            "Public commitment creates urgency for vendor selection"
        ]
    }
    
    return random.choice(insights.get(signal_type, ["Signal detected - monitor for additional indicators"]))

# Sample Data with AI Features
def init_sample_data():
    """Initialize database with sample data and AI analysis"""
    if Company.query.first() is not None:
        return  # Data already exists
    
    # Sample companies
    sample_companies = [
        {
            'name': "Advanced Manufacturing Solutions",
            'website': "ams-industrial.com",
            'industry': "Manufacturing",
            'size': "200-500",
            'revenue': "$50M-$100M",
            'country': "USA",
            'state': "Michigan",
            'city': "Detroit",
            'signals': [
                {'type': 'hiring', 'source': 'indeed.com', 
                 'desc': 'Hiring Senior Network Engineer with Cisco IE experience', 'conf': 0.85},
                {'type': 'contract', 'source': 'sam.gov',
                 'desc': 'Awarded $2.5M smart manufacturing upgrade contract', 'conf': 0.95}
            ]
        },
        {
            'name': "Precision Automation Corp",
            'website': "precisionauto.com",
            'industry': "Automation",
            'size': "500-1000",
            'revenue': "$100M-$500M",
            'country': "USA",
            'state': "Ohio",
            'city': "Cleveland",
            'signals': [
                {'type': 'expansion', 'source': 'press release',
                 'desc': 'Announced new facility expansion in Austin, TX', 'conf': 0.90},
                {'type': 'hiring', 'source': 'linkedin.com',
                 'desc': 'Recruiting Automation Systems Integrators', 'conf': 0.78}
            ]
        },
        {
            'name': "Industrial IoT Systems",
            'website': "iiot-sys.com",
            'industry': "Technology",
            'size': "50-200",
            'revenue': "$10M-$50M",
            'country': "USA",
            'state': "Texas",
            'city': "Houston",
            'signals': [
                {'type': 'tech_mention', 'source': 'linkedin.com',
                 'desc': 'Posted about implementing Industrial Ethernet solutions', 'conf': 0.75},
                {'type': 'tech_mention', 'source': 'twitter.com',
                 'desc': 'Shared article about Industry 4.0 transformation', 'conf': 0.65}
            ]
        },
        {
            'name': "Smart Factory Solutions",
            'website': "smartfactory.io",
            'industry': "Manufacturing",
            'size': "1000-5000",
            'revenue': "$500M-$1B",
            'country': "USA",
            'state': "California",
            'city': "San Jose",
            'signals': [
                {'type': 'hiring', 'source': 'indeed.com',
                 'desc': 'Multiple openings for OT Security Specialists', 'conf': 0.88},
                {'type': 'hiring', 'source': 'glassdoor.com',
                 'desc': 'Seeking Director of Digital Transformation', 'conf': 0.82},
                {'type': 'contract', 'source': 'sam.gov',
                 'desc': 'Won $8M defense manufacturing modernization contract', 'conf': 0.96}
            ]
        },
        {
            'name': "Process Control Industries",
            'website': "pci-controls.com",
            'industry': "Process Control",
            'size': "500-1000",
            'revenue': "$100M-$500M",
            'country': "USA",
            'state': "Pennsylvania",
            'city': "Pittsburgh",
            'signals': [
                {'type': 'expansion', 'source': 'local news',
                 'desc': 'Breaking ground on new R&D facility', 'conf': 0.85}
            ]
        },
        {
            'name': "Midwest Metal Fabricators",
            'website': "mmf-abrasives.com",
            'industry': "Manufacturing",
            'size': "200-500",
            'revenue': "$25M-$50M",
            'country': "USA",
            'state': "Illinois",
            'city': "Chicago",
            'signals': [
                {'type': 'hiring', 'source': 'indeed.com',
                 'desc': 'Looking for Plant Network Administrator', 'conf': 0.80},
                {'type': 'tech_mention', 'source': 'industry-week.com',
                 'desc': 'Featured in article about smart factory adoption', 'conf': 0.70}
            ]
        },
        {
            'name': "Gulf Coast Petrochemical",
            'website': "gcpchem.com",
            'industry': "Process Control",
            'size': "1000-5000",
            'revenue': "$1B+",
            'country': "USA",
            'state': "Texas",
            'city': "Baytown",
            'signals': [
                {'type': 'contract', 'source': 'texas.gov',
                 'desc': 'Environmental compliance upgrade project $12M', 'conf': 0.92},
                {'type': 'expansion', 'source': 'houston-chronicle.com',
                 'desc': 'Adding second production line', 'conf': 0.88},
                {'type': 'hiring', 'source': 'linkedin.com',
                 'desc': 'Seeking SCADA Network Engineers', 'conf': 0.85}
            ]
        },
        {
            'name': "Appalachian Mining Technologies",
            'website': "amt-mining.com",
            'industry': "Mining",
            'size': "500-1000",
            'revenue': "$100M-$500M",
            'country': "USA",
            'state': "West Virginia",
            'city': "Charleston",
            'signals': [
                {'type': 'tech_mention', 'source': 'mining-journal.com',
                 'desc': 'Announced autonomous vehicle network pilot', 'conf': 0.75}
            ]
        }
    ]
    
    # Create companies with AI analysis
    for company_data in sample_companies:
        company = Company(
            name=company_data['name'],
            website=company_data['website'],
            industry=company_data['industry'],
            size=company_data['size'],
            revenue=company_data['revenue'],
            country=company_data['country'],
            state=company_data['state'],
            city=company_data['city']
        )
        db.session.add(company)
        db.session.flush()  # Get company.id without committing
        
        # Create signals
        signals = []
        for signal_data in company_data['signals']:
            signal = Signal(
                company_id=company.id,
                signal_type=signal_data['type'],
                source=signal_data['source'],
                description=signal_data['desc'],
                confidence_score=signal_data['conf'],
                ai_insight=generate_signal_insight(signal_data['type'], signal_data['desc']),
                impact_score=random.randint(15, 30)
            )
            db.session.add(signal)
            signals.append(signal)
        
        # Generate AI analysis
        company.ai_summary = generate_ai_summary(company.name, company.industry, signals)
        company.buying_intent_score = calculate_buying_intent(signals)
        company.ai_recommendation = get_recommendation(company.buying_intent_score, signals)
    
    db.session.commit()

# Market Insights (Simulated AI)
def generate_market_insights():
    """Generate AI market insights"""
    return [
        {
            'type': 'Trend Alert',
            'title': 'Manufacturing Sector Surge',
            'description': 'AI analysis detects 34% increase in network infrastructure hiring across Midwest manufacturing region. Peak buying season identified.',
            'confidence': 94
        },
        {
            'type': 'Opportunity',
            'title': 'Government Contract Window',
            'description': 'Federal fiscal year-end approaching. $2.4B in unawarded manufacturing modernization contracts identified. Immediate outreach recommended.',
            'confidence': 89
        },
        {
            'type': 'Risk Alert',
            'title': 'Competitor Activity Detected',
            'description': 'Three major competitors launched aggressive campaigns in Texas market. Consider defensive positioning or alternative regions.',
            'confidence': 78
        }
    ]

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/companies')
def get_companies():
    # Get filter parameters
    state = request.args.get('state', '')
    industry = request.args.get('industry', '')
    size = request.args.get('size', '')
    signal_type = request.args.get('signal_type', '')
    min_intent = request.args.get('min_intent', type=int, default=0)
    ai_search = request.args.get('ai_search', '').lower()
    
    query = Company.query
    
    # Standard filters
    if state:
        query = query.filter(Company.state.ilike(f'%{state}%'))
    if industry:
        query = query.filter(Company.industry.ilike(f'%{industry}%'))
    if size:
        query = query.filter(Company.size == size)
    if min_intent:
        query = query.filter(Company.buying_intent_score >= min_intent)
    
    # Signal type filter
    if signal_type:
        query = query.join(Signal).filter(Signal.signal_type == signal_type)
    
    # AI Search (simulated natural language processing)
    if ai_search:
        # Simple keyword matching for demo
        keywords = ai_search.split()
        for keyword in keywords:
            if keyword in ['high', 'hot', 'urgent', 'immediate']:
                query = query.filter(Company.buying_intent_score >= 70)
            elif keyword in ['manufacturing', 'auto', 'factory']:
                query = query.filter(Company.industry.ilike('%Manufacturing%'))
            elif keyword in ['texas', 'tx']:
                query = query.filter(Company.state.ilike('%Texas%'))
            elif keyword in ['hiring', 'recruiting']:
                query = query.join(Signal).filter(Signal.signal_type == 'hiring')
    
    companies = query.all()
    return jsonify([c.to_dict() for c in companies])

@app.route('/api/states')
def get_states():
    states = db.session.query(Company.state).distinct().all()
    return jsonify([s[0] for s in states if s[0]])

@app.route('/api/industries')
def get_industries():
    industries = db.session.query(Company.industry).distinct().all()
    return jsonify([i[0] for i in industries if i[0]])

@app.route('/api/stats')
def get_stats():
    total_companies = Company.query.count()
    total_signals = Signal.query.count()
    hiring_signals = Signal.query.filter_by(signal_type='hiring').count()
    contract_signals = Signal.query.filter_by(signal_type='contract').count()
    avg_intent = db.session.query(db.func.avg(Company.buying_intent_score)).scalar() or 0
    
    return jsonify({
        'total_companies': total_companies,
        'total_signals': total_signals,
        'hiring_signals': hiring_signals,
        'contract_signals': contract_signals,
        'avg_intent_score': round(avg_intent, 1),
        'high_intent_count': Company.query.filter(Company.buying_intent_score >= 70).count()
    })

@app.route('/api/market-insights')
def get_market_insights():
    return jsonify(generate_market_insights())

# Initialize database and sample data
with app.app_context():
    db.create_all()
    init_sample_data()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
