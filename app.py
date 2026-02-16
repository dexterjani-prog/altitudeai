from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import random

app = Flask(__name__)

# Database configuration - handle Railway PostgreSQL
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Railway uses postgres:// but SQLAlchemy needs postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///altitudeai.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Add engine options for PostgreSQL
if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI']:
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300
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
        # Calculate AI buying intent score
        intent_score = calculate_intent_score(self)
        
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
            'signals': [s.to_dict() for s in self.signals],
            'buying_intent_score': intent_score,
            'ai_summary': generate_ai_summary(self, intent_score),
            'recommended_action': get_recommendation(intent_score)
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
            'id': self.id,
            'signal_type': self.signal_type,
            'source': self.source,
            'signal_date': self.signal_date.isoformat() if self.signal_date else None,
            'description': self.description,
            'confidence_score': self.confidence_score,
            'ai_extracted_insight': generate_signal_insight(self)
        }

# AI Calculation Functions
def calculate_intent_score(company):
    """Calculate AI buying intent score based on signals"""
    base_score = 30  # Base score
    
    for signal in company.signals:
        if signal.signal_type == 'hiring':
            base_score += 20
        elif signal.signal_type == 'contract':
            base_score += 30
        elif signal.signal_type == 'expansion':
            base_score += 25
        elif signal.signal_type == 'tech_mention':
            base_score += 15
        
        # Boost for high confidence signals
        if signal.confidence_score and signal.confidence_score > 0.85:
            base_score += 10
    
    # Cap at 100
    return min(base_score, 100)

def generate_ai_summary(company, intent_score):
    """Generate AI analysis summary for a company"""
    signals_text = []
    for s in company.signals:
        if s.signal_type == 'hiring':
            signals_text.append("actively hiring network engineers")
        elif s.signal_type == 'contract':
            signals_text.append("recently awarded major automation contract")
        elif s.signal_type == 'expansion':
            signals_text.append("expanding facilities")
        elif s.signal_type == 'tech_mention':
            signals_text.append("discussing industrial network upgrades")
    
    if not signals_text:
        return "Limited public signals detected. Recommend monitoring for future opportunities."
    
    signal_str = " and ".join(signals_text[:2])
    
    if intent_score >= 70:
        return f"Strong buying signals detected: {signal_str}. High intent score ({intent_score}) indicates active infrastructure refresh cycle. Recommend immediate outreach."
    elif intent_score >= 50:
        return f"Moderate buying signals: {signal_str}. Intent score of {intent_score} suggests potential upgrade cycle within 6-12 months. Schedule follow-up."
    else:
        return f"Early signals detected: {signal_str}. Intent score {intent_score} indicates exploratory phase. Add to nurture campaign."

def get_recommendation(intent_score):
    """Get AI recommendation based on intent score"""
    if intent_score >= 80:
        return "🎯 Contact Immediately - High intent prospect ready to buy"
    elif intent_score >= 60:
        return "📞 Schedule Call - Strong signals, engage this quarter"
    elif intent_score >= 40:
        return "📧 Add to Nurture - Monitor for signal strengthening"
    else:
        return "🔍 Continue Monitoring - Early stage prospect"

def generate_signal_insight(signal):
    """Generate AI insight for a specific signal"""
    insights = {
        'hiring': "AI detected: Job posting indicates infrastructure expansion budget approved",
        'contract': "AI detected: Government contract suggests compliance-driven network upgrade",
        'expansion': "AI detected: Facility expansion requires new industrial network infrastructure",
        'tech_mention': "AI detected: Social post reveals evaluation of Industry 4.0 solutions"
    }
    return insights.get(signal.signal_type, "AI analyzing signal context...")

def init_sample_data():
    """Initialize sample data if database is empty"""
    try:
        if Company.query.first() is None:
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
            print("Sample data initialized successfully")
    except Exception as e:
        print(f"Error initializing sample data: {e}")
        db.session.rollback()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/companies')
def get_companies():
    try:
        state = request.args.get('state', '')
        industry = request.args.get('industry', '')
        size = request.args.get('size', '')
        signal_type = request.args.get('signal_type', '')
        min_intent = request.args.get('min_intent', '')
        
        query = Company.query
        
        if state:
            query = query.filter(Company.state.ilike(f'%{state}%'))
        if industry:
            query = query.filter(Company.industry.ilike(f'%{industry}%'))
        if size:
            query = query.filter(Company.size == size)
        if signal_type:
            query = query.join(Signal).filter(Signal.signal_type == signal_type)
        
        companies = query.all()
        
        # Filter by intent score if specified
        if min_intent:
            try:
                min_score = int(min_intent)
                companies = [c for c in companies if calculate_intent_score(c) >= min_score]
            except ValueError:
                pass
        
        # Sort by buying intent score (highest first)
        companies.sort(key=lambda c: calculate_intent_score(c), reverse=True)
        
        return jsonify([c.to_dict() for c in companies])
    except Exception as e:
        print(f"Error in get_companies: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/states')
def get_states():
    try:
        states = db.session.query(Company.state).distinct().all()
        return jsonify([s[0] for s in states if s[0]])
    except Exception as e:
        print(f"Error in get_states: {e}")
        return jsonify([]), 500

@app.route('/api/industries')
def get_industries():
    try:
        industries = db.session.query(Company.industry).distinct().all()
        return jsonify([i[0] for i in industries if i[0]])
    except Exception as e:
        print(f"Error in get_industries: {e}")
        return jsonify([]), 500

@app.route('/api/stats')
def get_stats():
    try:
        companies = Company.query.all()
        total = len(companies)
        
        # Calculate average buying intent
        if total > 0:
            total_intent = sum(calculate_intent_score(c) for c in companies)
            avg_intent = round(total_intent / total)
            high_intent = sum(1 for c in companies if calculate_intent_score(c) >= 70)
        else:
            avg_intent = 0
            high_intent = 0
        
        return jsonify({
            'total_companies': total,
            'total_signals': Signal.query.count(),
            'hiring_signals': Signal.query.filter_by(signal_type='hiring').count(),
            'contract_signals': Signal.query.filter_by(signal_type='contract').count(),
            'avg_buying_intent': avg_intent,
            'high_intent_companies': high_intent
        })
    except Exception as e:
        print(f"Error in get_stats: {e}")
        # Return safe defaults on error
        return jsonify({
            'total_companies': 0,
            'total_signals': 0,
            'hiring_signals': 0,
            'contract_signals': 0,
            'avg_buying_intent': 0,
            'high_intent_companies': 0
        }), 500

@app.route('/api/ai-insights')
def get_ai_insights():
    """Generate AI market insights"""
    try:
        insights = [
            {
                'insight_type': 'Market Trend',
                'title': 'Manufacturing sector showing 34% increase in network hiring',
                'description': 'AI detected significant uptick in OT/IT convergence roles across Midwest manufacturing hubs. Companies preparing for Industry 4.0 transitions.',
                'confidence': 0.92
            },
            {
                'insight_type': 'Opportunity Alert',
                'title': 'Federal infrastructure spending driving automation contracts',
                'description': 'SAM.gov analysis reveals $2.1B in smart manufacturing contracts awarded Q1-Q2 2024. Average deal size increased 28% YoY.',
                'confidence': 0.88
            },
            {
                'insight_type': 'Risk Factor',
                'title': 'Supply chain disruptions delaying network refresh cycles',
                'description': 'AI monitoring indicates 15% of high-intent prospects pushing projects to Q4. Recommend accelerated outreach to secure Q3 commitments.',
                'confidence': 0.85
            }
        ]
        return jsonify(insights)
    except Exception as e:
        print(f"Error in get_ai_insights: {e}")
        return jsonify([]), 500

@app.route('/api/search', methods=['POST'])
def ai_search():
    """AI-powered natural language search"""
    try:
        data = request.get_json() or {}
        query = data.get('query', '').lower()
        
        if not query:
            return jsonify({
                'ai_interpretation': 'Empty search query',
                'results': [],
                'total_matches': 0
            })
        
        # Simple keyword extraction
        keywords = {
            'manufacturing': ['manufacturing', 'factory', 'plant'],
            'michigan': ['michigan', 'mi', 'detroit'],
            'hiring': ['hiring', 'job', 'engineer', 'network'],
            'high intent': ['high intent', 'ready to buy', 'hot lead']
        }
        
        detected_filters = []
        for category, terms in keywords.items():
            if any(term in query for term in terms):
                detected_filters.append(category)
        
        # Build filter description
        ai_interpretation = f"AI interpreted: Searching for companies"
        if detected_filters:
            ai_interpretation += f" related to {', '.join(detected_filters)}"
        else:
            ai_interpretation += " (broad search)"
        
        # Get all companies and rank by relevance
        companies = Company.query.all()
        results = []
        
        for company in companies:
            score = 0
            company_text = f"{company.name} {company.industry} {company.state} {company.city}".lower()
            
            # Score based on keyword matches
            for category, terms in keywords.items():
                if any(term in company_text for term in terms):
                    score += 10
            
            # Boost for high intent
            intent = calculate_intent_score(company)
            if intent >= 70:
                score += 20
            elif intent >= 50:
                score += 10
            
            if score > 0:
                results.append({
                    'company': company.to_dict(),
                    'relevance_score': score,
                    'matched_keywords': detected_filters
                })
        
        # Sort by relevance
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return jsonify({
            'ai_interpretation': ai_interpretation,
            'results': results[:10],
            'total_matches': len(results)
        })
    except Exception as e:
        print(f"Error in ai_search: {e}")
        return jsonify({
            'ai_interpretation': 'Search error occurred',
            'results': [],
            'total_matches': 0
        }), 500

# Initialize database and sample data
with app.app_context():
    try:
        db.create_all()
        init_sample_data()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization error: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
