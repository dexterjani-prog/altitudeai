from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import random

app = Flask(__name__)

# Database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+pg8000://', 1)
    elif database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+pg8000://', 1)
else:
    database_url = 'sqlite:////tmp/app.db'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
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

    def compute_buying_intent(self):
        """Fake AI: deterministic intent score based on signals."""
        score = 35  # base
        weights = {
            'contract': 30,
            'expansion': 25,
            'hiring': 20,
            'tech_mention': 15
        }
        for signal in self.signals:
            score += weights.get(signal.signal_type, 10)
        return min(score, 99)

    def compute_ai_summary(self):
        """Fake AI: generate a context-aware summary."""
        signal_types = [s.signal_type for s in self.signals]
        summaries = {
            frozenset(['hiring', 'contract']): (
                f"{self.name} is showing strong expansion signals. Recent contract awards combined with "
                f"active network engineering recruitment strongly indicate upcoming infrastructure procurement. "
                f"AI confidence: High priority target for Q1 outreach."
            ),
            frozenset(['hiring']): (
                f"AI detected active hiring of OT/IT network specialists at {self.name}. "
                f"This pattern correlates with 78% probability of infrastructure investment within 90 days."
            ),
            frozenset(['contract']): (
                f"Government contract data reveals {self.name} recently secured industrial automation funding. "
                f"AI analysis indicates a procurement window is open for network infrastructure components."
            ),
            frozenset(['expansion']): (
                f"{self.name} announced facility expansion. AI cross-referenced facility size increase with "
                f"historical network upgrade patterns — high likelihood of industrial Ethernet refresh cycle."
            ),
            frozenset(['tech_mention']): (
                f"AI scraped recent mentions of industrial networking technology at {self.name}. "
                f"Language analysis suggests active evaluation phase — recommend early engagement."
            ),
        }
        key = frozenset(signal_types)
        for k, v in summaries.items():
            if k.issubset(key) or k == key:
                return v
        return (
            f"AI analysis of {self.name} indicates a moderate buying intent profile. "
            f"Monitoring {len(self.signals)} active signal(s) across {self.industry} sector. "
            f"Recommend adding to watch list for next 30-day review cycle."
        )

    def compute_recommended_action(self):
        score = self.compute_buying_intent()
        if score >= 75:
            return "⚡ AI Recommendation: Contact immediately — high intent window is active (est. 30–60 days)"
        elif score >= 55:
            return "📅 AI Recommendation: Schedule discovery call within 2 weeks — signals are warming"
        else:
            return "👁 AI Recommendation: Add to monitoring queue — intent score building"

    def to_dict(self):
        intent_score = self.compute_buying_intent()
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
            'buying_intent_score': intent_score,
            'ai_summary': self.compute_ai_summary(),
            'recommended_action': self.compute_recommended_action(),
            'signals': [s.to_dict() for s in self.signals],
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

    def get_ai_insight(self):
        insights = {
            'hiring': "AI detected industrial OT/IT skill requirements — strong predictor of network hardware budget.",
            'contract': "AI matched contract scope keywords to industrial Ethernet procurement patterns.",
            'expansion': "AI correlated facility growth with historical network refresh cycles (avg. 6-month lag).",
            'tech_mention': "NLP analysis flagged industrial networking terminology — suggests active vendor evaluation.",
        }
        return insights.get(self.signal_type, "AI extracted structured signal from unstructured web data.")

    def to_dict(self):
        return {
            'id': self.id,
            'signal_type': self.signal_type,
            'source': self.source,
            'signal_date': self.signal_date.isoformat() if self.signal_date else None,
            'description': self.description,
            'confidence_score': self.confidence_score,
            'ai_extracted_insight': self.get_ai_insight(),
        }


def init_sample_data():
    if Company.query.first() is not None:
        return

    companies = [
        Company(name="Advanced Manufacturing Solutions", website="ams-industrial.com",
                industry="Manufacturing", size="200-500", revenue="$50M–$100M",
                country="USA", state="Michigan", city="Detroit"),
        Company(name="Precision Automation Corp", website="precisionauto.com",
                industry="Automation", size="500-1000", revenue="$100M–$500M",
                country="USA", state="Ohio", city="Cleveland"),
        Company(name="Industrial IoT Systems", website="iiot-sys.com",
                industry="Technology", size="50-200", revenue="$10M–$50M",
                country="USA", state="Texas", city="Houston"),
        Company(name="Smart Factory Solutions", website="smartfactory.io",
                industry="Manufacturing", size="1000-5000", revenue="$500M–$1B",
                country="USA", state="California", city="San Jose"),
        Company(name="Process Control Industries", website="pci-controls.com",
                industry="Process Control", size="500-1000", revenue="$100M–$500M",
                country="USA", state="Pennsylvania", city="Pittsburgh"),
        Company(name="Midwest Utilities Group", website="mug-utilities.com",
                industry="Utilities", size="200-500", revenue="$50M–$100M",
                country="USA", state="Illinois", city="Chicago"),
        Company(name="Gulf Coast Refinery Tech", website="gcrt.com",
                industry="Oil & Gas", size="1000-5000", revenue="$500M–$1B",
                country="USA", state="Texas", city="Beaumont"),
        Company(name="NovaStar Logistics", website="novastarlogistics.com",
                industry="Transportation", size="500-1000", revenue="$100M–$500M",
                country="USA", state="Georgia", city="Atlanta"),
    ]

    for c in companies:
        db.session.add(c)
    db.session.commit()

    signals = [
        Signal(company_id=1, signal_type="hiring", source="indeed.com",
               description="Hiring Senior Network Engineer with Cisco IE-4000 series experience",
               confidence_score=0.85),
        Signal(company_id=1, signal_type="contract", source="sam.gov",
               description="Awarded $2.5M DOD smart manufacturing upgrade contract",
               confidence_score=0.95),
        Signal(company_id=2, signal_type="expansion", source="press release",
               description="Announced 120,000 sq ft facility expansion in Austin, TX",
               confidence_score=0.90),
        Signal(company_id=2, signal_type="hiring", source="linkedin.com",
               description="3 open roles for OT Security and Industrial Network Architects",
               confidence_score=0.80),
        Signal(company_id=3, signal_type="tech_mention", source="linkedin.com",
               description="Posted case study on implementing EtherNet/IP across 4 plant floors",
               confidence_score=0.75),
        Signal(company_id=4, signal_type="hiring", source="indeed.com",
               description="Multiple openings for OT Security Specialists and SCADA Engineers",
               confidence_score=0.88),
        Signal(company_id=4, signal_type="expansion", source="company website",
               description="New smart factory campus announced — Phase 2 network buildout planned",
               confidence_score=0.82),
        Signal(company_id=5, signal_type="contract", source="sam.gov",
               description="Won $1.8M EPA environmental monitoring network upgrade contract",
               confidence_score=0.91),
        Signal(company_id=6, signal_type="hiring", source="indeed.com",
               description="Hiring Network Operations Manager with industrial protocol expertise",
               confidence_score=0.78),
        Signal(company_id=7, signal_type="tech_mention", source="industry publication",
               description="Mentioned Profinet and HART protocol modernization in annual report",
               confidence_score=0.72),
        Signal(company_id=7, signal_type="contract", source="state tender",
               description="Awarded refinery automation modernization project worth $4.2M",
               confidence_score=0.93),
        Signal(company_id=8, signal_type="expansion", source="press release",
               description="Opening 3 new distribution hubs requiring network buildout",
               confidence_score=0.86),
    ]

    for s in signals:
        db.session.add(s)
    db.session.commit()


# Initialize DB on startup
with app.app_context():
    db.create_all()
    init_sample_data()


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/stats')
def get_stats():
    companies = Company.query.all()
    intent_scores = [c.compute_buying_intent() for c in companies]
    high_intent = sum(1 for s in intent_scores if s >= 70)
    avg_intent = round(sum(intent_scores) / len(intent_scores)) if intent_scores else 0

    return jsonify({
        'total_companies': len(companies),
        'total_signals': Signal.query.count(),
        'high_intent_companies': high_intent,
        'avg_buying_intent': avg_intent,
    })


@app.route('/api/companies')
def get_companies():
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

    # Filter by min intent (post-query since it's computed)
    if min_intent:
        try:
            threshold = int(min_intent)
            companies = [c for c in companies if c.compute_buying_intent() >= threshold]
        except ValueError:
            pass

    # Sort by intent score descending
    companies.sort(key=lambda c: c.compute_buying_intent(), reverse=True)

    return jsonify([c.to_dict() for c in companies])


@app.route('/api/states')
def get_states():
    states = db.session.query(Company.state).distinct().all()
    return jsonify(sorted([s[0] for s in states if s[0]]))


@app.route('/api/industries')
def get_industries():
    industries = db.session.query(Company.industry).distinct().all()
    return jsonify(sorted([i[0] for i in industries if i[0]]))


@app.route('/api/ai-insights')
def get_ai_insights():
    """Fake AI market insights — deterministic from real data."""
    companies = Company.query.all()
    signals = Signal.query.all()

    hiring_count = sum(1 for s in signals if s.signal_type == 'hiring')
    contract_count = sum(1 for s in signals if s.signal_type == 'contract')
    expansion_count = sum(1 for s in signals if s.signal_type == 'expansion')

    top_states = {}
    for c in companies:
        top_states[c.state] = top_states.get(c.state, 0) + 1
    hottest_state = max(top_states, key=top_states.get) if top_states else "Texas"

    insights = [
        {
            "insight_type": "Market Trend",
            "title": f"Hiring signals up {hiring_count * 12}% vs last quarter",
            "description": (
                f"AI detected {hiring_count} active network engineering job postings across tracked companies. "
                f"This leading indicator suggests significant infrastructure procurement within 60–90 days."
            ),
            "confidence": 0.87
        },
        {
            "insight_type": "Geographic Opportunity",
            "title": f"{hottest_state} is the highest-density target market",
            "description": (
                f"AI clustering analysis identified {hottest_state} as the region with the highest concentration "
                f"of industrial companies showing active buying signals. Recommended for priority sales coverage."
            ),
            "confidence": 0.91
        },
        {
            "insight_type": "Contract Intelligence",
            "title": f"${contract_count * 2.1:.1f}M in government automation contracts detected",
            "description": (
                f"AI scanned SAM.gov and state procurement portals — {contract_count} contracts awarded to tracked "
                f"companies include industrial network infrastructure scope. These companies have confirmed budget."
            ),
            "confidence": 0.94
        },
        {
            "insight_type": "Expansion Alert",
            "title": f"{expansion_count} facility expansions signal network buildout demand",
            "description": (
                f"AI correlated {expansion_count} facility expansion announcements with historical network hardware "
                f"purchase data. Average time-to-procurement: 4.2 months post-announcement."
            ),
            "confidence": 0.83
        },
    ]

    return jsonify(insights)


@app.route('/api/search', methods=['POST'])
def ai_search():
    """Fake AI natural language search — keyword matching with AI framing."""
    data = request.get_json()
    query = data.get('query', '').lower()

    # Parse intent from natural language
    filters = {}
    ai_interpretation = ""

    if any(w in query for w in ['high intent', 'ready to buy', 'hot']):
        filters['min_intent'] = 70
        ai_interpretation = "AI identified query as high-intent prospect filter. Returning companies with intent score ≥ 70."
    elif any(w in query for w in ['hiring', 'recruiting']):
        filters['signal_type'] = 'hiring'
        ai_interpretation = "AI detected hiring signal intent. Filtering to companies actively recruiting network engineers."
    elif any(w in query for w in ['contract', 'government', 'federal']):
        filters['signal_type'] = 'contract'
        ai_interpretation = "AI identified government contract interest. Returning companies with active contract awards."
    elif any(w in query for w in ['expanding', 'expansion', 'growing']):
        filters['signal_type'] = 'expansion'
        ai_interpretation = "AI matched expansion keywords. Showing companies with facility growth signals."

    # State detection
    state_map = {
        'michigan': 'Michigan', 'ohio': 'Ohio', 'texas': 'Texas',
        'california': 'California', 'pennsylvania': 'Pennsylvania',
        'illinois': 'Illinois', 'georgia': 'Georgia',
    }
    for keyword, state in state_map.items():
        if keyword in query:
            filters['state'] = state
            ai_interpretation += f" Geo-filter applied: {state}."

    # Industry detection
    industry_map = {
        'manufactur': 'Manufacturing', 'automat': 'Automation',
        'utilities': 'Utilities', 'oil': 'Oil & Gas', 'transport': 'Transportation',
    }
    for keyword, industry in industry_map.items():
        if keyword in query:
            filters['industry'] = industry
            ai_interpretation += f" Industry filter: {industry}."

    if not ai_interpretation:
        ai_interpretation = f"AI performed semantic search for '{query}'. Returning best matches by intent score."

    # Apply filters
    q = Company.query
    if 'state' in filters:
        q = q.filter(Company.state == filters['state'])
    if 'industry' in filters:
        q = q.filter(Company.industry.ilike(f"%{filters['industry']}%"))
    if 'signal_type' in filters:
        q = q.join(Signal).filter(Signal.signal_type == filters['signal_type'])

    companies = q.all()

    if 'min_intent' in filters:
        companies = [c for c in companies if c.compute_buying_intent() >= filters['min_intent']]

    companies.sort(key=lambda c: c.compute_buying_intent(), reverse=True)

    results = [
        {
            'company': c.to_dict(),
            'relevance_score': round(min(c.compute_buying_intent() / 100, 0.99), 2),
            'match_reason': ai_interpretation,
        }
        for c in companies
    ]

    return jsonify({
        'ai_interpretation': ai_interpretation,
        'results': results,
        'total': len(results),
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
