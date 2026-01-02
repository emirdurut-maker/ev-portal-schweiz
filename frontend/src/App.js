import { useState, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import axios from "axios";
import { 
  Car, BarChart3, Zap, BookOpen, Calculator, Newspaper, 
  Menu, X, ChevronRight, Battery, Gauge, MapPin, 
  TrendingUp, Award, Info, Search, Filter, ArrowUpDown,
  Thermometer, Clock, Fuel, Shield, Leaf, AlertCircle,
  CheckCircle, XCircle, ExternalLink, ChevronDown, ChevronUp,
  Home as HomeIcon
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// ==================== COMPONENTS ====================

// Navigation
const Navigation = () => {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();
  
  const navItems = [
    { path: "/", label: "Home", icon: HomeIcon },
    { path: "/dashboard", label: "Dashboard", icon: BarChart3 },
    { path: "/fahrzeuge", label: "Fahrzeuge", icon: Car },
    { path: "/reichweite", label: "Reichweite & Laden", icon: Zap },
    { path: "/wissen", label: "EV-Wissen", icon: BookOpen },
    { path: "/kostenrechner", label: "Kostenrechner", icon: Calculator },
    { path: "/news", label: "News", icon: Newspaper },
  ];
  
  return (
    <nav className="bg-slate-900 text-white sticky top-0 z-50 shadow-lg" data-testid="main-navigation">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center space-x-2" data-testid="logo-link">
            <span className="text-2xl">🇨🇭</span>
            <span className="font-bold text-xl">EV Portal Schweiz</span>
          </Link>
          
          {/* Desktop Nav */}
          <div className="hidden lg:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  data-testid={`nav-${item.path.replace('/', '') || 'home'}`}
                  className={`flex items-center space-x-1 px-3 py-2 rounded-lg transition-all ${
                    isActive 
                      ? 'bg-emerald-600 text-white' 
                      : 'hover:bg-slate-800 text-slate-300 hover:text-white'
                  }`}
                >
                  <Icon size={18} />
                  <span className="text-sm">{item.label}</span>
                </Link>
              );
            })}
          </div>
          
          {/* Mobile Menu Button */}
          <button 
            onClick={() => setIsOpen(!isOpen)}
            className="lg:hidden p-2"
            data-testid="mobile-menu-toggle"
          >
            {isOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
        
        {/* Mobile Nav */}
        {isOpen && (
          <div className="lg:hidden pb-4 space-y-1" data-testid="mobile-menu">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setIsOpen(false)}
                  className={`flex items-center space-x-2 px-4 py-3 rounded-lg ${
                    isActive ? 'bg-emerald-600' : 'hover:bg-slate-800'
                  }`}
                >
                  <Icon size={20} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </nav>
  );
};

// Footer
const Footer = () => (
  <footer className="bg-slate-900 text-slate-400 py-12 mt-16" data-testid="footer">
    <div className="max-w-7xl mx-auto px-4">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
        <div>
          <div className="flex items-center space-x-2 mb-4">
            <span className="text-2xl">🇨🇭</span>
            <span className="font-bold text-white text-lg">EV Portal Schweiz</span>
          </div>
          <p className="text-sm">Das unabhängige Schweizer Portal für Elektromobilität. Daten, Wissen und Tools für Ihre EV-Entscheidung.</p>
        </div>
        <div>
          <h4 className="font-semibold text-white mb-4">Portal</h4>
          <ul className="space-y-2 text-sm">
            <li><Link to="/dashboard" className="hover:text-emerald-400">Dashboard</Link></li>
            <li><Link to="/fahrzeuge" className="hover:text-emerald-400">Fahrzeuge</Link></li>
            <li><Link to="/reichweite" className="hover:text-emerald-400">Reichweite & Laden</Link></li>
            <li><Link to="/kostenrechner" className="hover:text-emerald-400">Kostenrechner</Link></li>
          </ul>
        </div>
        <div>
          <h4 className="font-semibold text-white mb-4">Ressourcen</h4>
          <ul className="space-y-2 text-sm">
            <li><Link to="/wissen" className="hover:text-emerald-400">EV-Wissen</Link></li>
            <li><Link to="/news" className="hover:text-emerald-400">News</Link></li>
          </ul>
        </div>
        <div>
          <h4 className="font-semibold text-white mb-4">Links</h4>
          <ul className="space-y-2 text-sm">
            <li><a href="https://ich-tanke-strom.ch" target="_blank" rel="noopener noreferrer" className="hover:text-emerald-400">ich-tanke-strom.ch</a></li>
            <li><a href="https://swiss-emobility.ch" target="_blank" rel="noopener noreferrer" className="hover:text-emerald-400">Swiss eMobility</a></li>
            <li><a href="https://auto.swiss" target="_blank" rel="noopener noreferrer" className="hover:text-emerald-400">auto-schweiz</a></li>
          </ul>
        </div>
      </div>
      <div className="border-t border-slate-800 mt-8 pt-8 text-center text-sm">
        <p>© 2025 EV Portal Schweiz. Alle Daten ohne Gewähr.</p>
      </div>
    </div>
  </footer>
);

// Stat Card Component
const StatCard = ({ icon: Icon, label, value, subtext, color = "emerald" }) => (
  <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6" data-testid="stat-card">
    <div className="flex items-start justify-between">
      <div>
        <p className="text-slate-500 text-sm">{label}</p>
        <p className={`text-3xl font-bold text-${color}-600 mt-1`}>{value}</p>
        {subtext && <p className="text-slate-400 text-xs mt-1">{subtext}</p>}
      </div>
      <div className={`p-3 bg-${color}-100 rounded-lg`}>
        <Icon className={`text-${color}-600`} size={24} />
      </div>
    </div>
  </div>
);

// ==================== HOME PAGE ====================

const HomePage = () => {
  const [stats, setStats] = useState(null);
  
  useEffect(() => {
    axios.get(`${API}/market/stats`).then(res => setStats(res.data)).catch(console.error);
  }, []);
  
  const features = [
    { icon: BarChart3, title: "Live Marktdaten", desc: "Aktuelle Zulassungszahlen und Trends der Schweizer Elektromobilität", link: "/dashboard" },
    { icon: Car, title: "Fahrzeug-Datenbank", desc: "30+ Elektrofahrzeuge vergleichen mit allen technischen Daten", link: "/fahrzeuge" },
    { icon: Zap, title: "Reichweite & Laden", desc: "Realistische Reichweite berechnen und Ladestationen finden", link: "/reichweite" },
    { icon: BookOpen, title: "EV-Wissen", desc: "Alles über Batterien, Laden und Elektromobilität verständlich erklärt", link: "/wissen" },
    { icon: Calculator, title: "Kostenrechner", desc: "TCO-Vergleich: Was kostet ein EV wirklich vs. Verbrenner?", link: "/kostenrechner" },
    { icon: Newspaper, title: "News Hub", desc: "Aktuelle Nachrichten aus der Welt der Elektromobilität", link: "/news" },
  ];
  
  return (
    <div data-testid="home-page">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-900 text-white py-20">
        <div className="max-w-7xl mx-auto px-4">
          <div className="max-w-3xl">
            <div className="flex items-center space-x-2 mb-4">
              <span className="text-4xl">🇨🇭</span>
              <span className="bg-emerald-500/20 text-emerald-400 px-3 py-1 rounded-full text-sm">Das Schweizer EV-Portal</span>
            </div>
            <h1 className="text-4xl md:text-6xl font-bold mb-6 leading-tight">
              Elektromobilität<br/>
              <span className="text-emerald-400">verstehen. entscheiden. fahren.</span>
            </h1>
            <p className="text-xl text-slate-300 mb-8">
              Unabhängige Daten, fundiertes Wissen und praktische Tools für Ihren Umstieg auf Elektro. Alles mit Fokus auf die Schweiz.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link to="/fahrzeuge" className="bg-emerald-500 hover:bg-emerald-600 text-white px-6 py-3 rounded-lg font-semibold flex items-center space-x-2 transition-all" data-testid="cta-fahrzeuge">
                <Car size={20} />
                <span>Fahrzeuge vergleichen</span>
              </Link>
              <Link to="/kostenrechner" className="bg-white/10 hover:bg-white/20 text-white px-6 py-3 rounded-lg font-semibold flex items-center space-x-2 transition-all" data-testid="cta-kostenrechner">
                <Calculator size={20} />
                <span>Kosten berechnen</span>
              </Link>
            </div>
          </div>
        </div>
      </section>
      
      {/* Stats Section */}
      {stats && (
        <section className="py-12 bg-slate-50">
          <div className="max-w-7xl mx-auto px-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard icon={TrendingUp} label="BEV-Marktanteil" value={`${stats.bev_market_share}%`} subtext={`${stats.current_month} ${stats.year}`} />
              <StatCard icon={Car} label="BEV pro Monat" value={stats.bev_registrations_monthly?.toLocaleString('de-CH')} subtext="Neuzulassungen" />
              <StatCard icon={Zap} label="Ladepunkte CH" value={stats.charging_points_ch?.toLocaleString('de-CH')} subtext="davon 2'850 Schnelllader" />
              <StatCard icon={Award} label="#1 Marke" value="Tesla" subtext="Meistverkauft 2024" />
            </div>
          </div>
        </section>
      )}
      
      {/* Features Grid */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-4">Alles an einem Ort</h2>
          <p className="text-slate-600 text-center mb-12 max-w-2xl mx-auto">Von Marktdaten bis Reichweitenrechner - die Tools die Sie für Ihre EV-Entscheidung brauchen.</p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, idx) => {
              const Icon = feature.icon;
              return (
                <Link 
                  key={idx} 
                  to={feature.link}
                  className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md hover:border-emerald-300 transition-all group"
                  data-testid={`feature-card-${idx}`}
                >
                  <div className="bg-emerald-100 w-12 h-12 rounded-lg flex items-center justify-center mb-4 group-hover:bg-emerald-500 transition-all">
                    <Icon className="text-emerald-600 group-hover:text-white" size={24} />
                  </div>
                  <h3 className="font-semibold text-lg mb-2">{feature.title}</h3>
                  <p className="text-slate-600 text-sm mb-4">{feature.desc}</p>
                  <span className="text-emerald-600 text-sm font-medium flex items-center space-x-1 group-hover:space-x-2 transition-all">
                    <span>Mehr erfahren</span>
                    <ChevronRight size={16} />
                  </span>
                </Link>
              );
            })}
          </div>
        </div>
      </section>
      
      {/* CTA Section */}
      <section className="py-16 bg-emerald-600 text-white">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">Bereit für die Elektromobilität?</h2>
          <p className="text-emerald-100 mb-8">Vergleichen Sie jetzt über 30 Elektrofahrzeuge und finden Sie Ihr perfektes E-Auto.</p>
          <Link to="/fahrzeuge" className="bg-white text-emerald-600 px-8 py-4 rounded-lg font-semibold inline-flex items-center space-x-2 hover:bg-emerald-50 transition-all" data-testid="cta-bottom">
            <Car size={20} />
            <span>Fahrzeuge vergleichen</span>
          </Link>
        </div>
      </section>
    </div>
  );
};

// ==================== DASHBOARD PAGE ====================

const DashboardPage = () => {
  const [stats, setStats] = useState(null);
  const [marketData, setMarketData] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    Promise.all([
      axios.get(`${API}/market/stats`),
      axios.get(`${API}/market/data`)
    ]).then(([statsRes, dataRes]) => {
      setStats(statsRes.data);
      setMarketData(dataRes.data);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, []);
  
  if (loading) return <div className="flex items-center justify-center min-h-screen"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div></div>;
  
  return (
    <div className="max-w-7xl mx-auto px-4 py-8" data-testid="dashboard-page">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">📊 Markt-Dashboard</h1>
        <p className="text-slate-600">Live-Daten & Statistiken zum Schweizer EV-Markt</p>
      </div>
      
      {/* Key Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard icon={TrendingUp} label="BEV-Marktanteil" value={`${stats?.bev_market_share}%`} subtext={stats?.current_month} />
        <StatCard icon={Car} label="BEV Neuzulassungen" value={stats?.bev_registrations_monthly?.toLocaleString('de-CH')} subtext="Pro Monat" />
        <StatCard icon={Zap} label="Ladepunkte CH" value={stats?.charging_points_ch?.toLocaleString('de-CH')} />
        <StatCard icon={Battery} label="Schnelllader" value={stats?.fast_chargers_ch?.toLocaleString('de-CH')} subtext="50+ kW" />
      </div>
      
      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Monthly Trend */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h3 className="font-semibold mb-4 flex items-center space-x-2">
            <TrendingUp size={20} className="text-emerald-600" />
            <span>BEV-Zulassungen 2024</span>
          </h3>
          <div className="space-y-2">
            {marketData?.monthly_data?.map((month, idx) => (
              <div key={idx} className="flex items-center space-x-3">
                <span className="text-sm text-slate-500 w-20">{month.month.slice(0, 3)}</span>
                <div className="flex-1 bg-slate-100 rounded-full h-6 overflow-hidden">
                  <div 
                    className="bg-emerald-500 h-full rounded-full flex items-center justify-end pr-2"
                    style={{ width: `${(month.bev_registrations / 10000) * 100}%` }}
                  >
                    <span className="text-xs text-white font-medium">{month.bev_registrations.toLocaleString('de-CH')}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {/* Market Share Pie */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h3 className="font-semibold mb-4 flex items-center space-x-2">
            <BarChart3 size={20} className="text-emerald-600" />
            <span>Antriebsarten {stats?.year}</span>
          </h3>
          <div className="flex items-center justify-center space-x-8">
            <div className="relative w-40 h-40">
              <svg viewBox="0 0 100 100" className="transform -rotate-90">
                <circle cx="50" cy="50" r="40" fill="none" stroke="#e2e8f0" strokeWidth="20" />
                <circle cx="50" cy="50" r="40" fill="none" stroke="#10b981" strokeWidth="20" 
                  strokeDasharray={`${stats?.bev_market_share * 2.51} 251`} />
                <circle cx="50" cy="50" r="40" fill="none" stroke="#6366f1" strokeWidth="20"
                  strokeDasharray={`${8 * 2.51} 251`} strokeDashoffset={`-${stats?.bev_market_share * 2.51}`} />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-2xl font-bold">{stats?.bev_market_share}%</span>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-emerald-500 rounded"></div>
                <span className="text-sm">BEV ({stats?.bev_market_share}%)</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-indigo-500 rounded"></div>
                <span className="text-sm">PHEV (~8%)</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-slate-200 rounded"></div>
                <span className="text-sm">Andere (~70%)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Rankings */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Brands */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h3 className="font-semibold mb-4 flex items-center space-x-2">
            <Award size={20} className="text-emerald-600" />
            <span>Top 10 Marken</span>
          </h3>
          <div className="space-y-3">
            {stats?.top_brands?.map((brand, idx) => (
              <div key={idx} className="flex items-center space-x-3">
                <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                  idx === 0 ? 'bg-yellow-100 text-yellow-700' : 
                  idx === 1 ? 'bg-slate-100 text-slate-700' :
                  idx === 2 ? 'bg-orange-100 text-orange-700' : 'bg-slate-50 text-slate-500'
                }`}>{idx + 1}</span>
                <span className="flex-1 font-medium">{brand.brand}</span>
                <span className="text-slate-500 text-sm">{brand.sales?.toLocaleString('de-CH')}</span>
                <span className="text-emerald-600 text-sm font-medium">{brand.share}%</span>
              </div>
            ))}
          </div>
        </div>
        
        {/* Top Models */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h3 className="font-semibold mb-4 flex items-center space-x-2">
            <Car size={20} className="text-emerald-600" />
            <span>Top 10 Modelle</span>
          </h3>
          <div className="space-y-3">
            {stats?.top_models?.map((model, idx) => (
              <div key={idx} className="flex items-center space-x-3">
                <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                  idx === 0 ? 'bg-yellow-100 text-yellow-700' : 
                  idx === 1 ? 'bg-slate-100 text-slate-700' :
                  idx === 2 ? 'bg-orange-100 text-orange-700' : 'bg-slate-50 text-slate-500'
                }`}>{idx + 1}</span>
                <span className="flex-1 font-medium">{model.model}</span>
                <span className="text-slate-500 text-sm">{model.sales?.toLocaleString('de-CH')}</span>
                <span className="text-emerald-600 text-sm font-medium">{model.share}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// ==================== VEHICLES PAGE ====================

const VehiclesPage = () => {
  const [vehicles, setVehicles] = useState([]);
  const [brands, setBrands] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    brand: '',
    category: '',
    minPrice: '',
    maxPrice: '',
    minRange: '',
    sortBy: 'price_chf',
    sortOrder: 'asc'
  });
  const [compareList, setCompareList] = useState([]);
  const [showCompare, setShowCompare] = useState(false);
  
  const fetchVehicles = async () => {
    try {
      const params = new URLSearchParams();
      if (filters.brand) params.append('brand', filters.brand);
      if (filters.category) params.append('category', filters.category);
      if (filters.minPrice) params.append('min_price', filters.minPrice);
      if (filters.maxPrice) params.append('max_price', filters.maxPrice);
      if (filters.minRange) params.append('min_range', filters.minRange);
      params.append('sort_by', filters.sortBy);
      params.append('sort_order', filters.sortOrder);
      
      const res = await axios.get(`${API}/vehicles?${params}`);
      setVehicles(res.data);
    } catch (err) {
      console.error(err);
    }
  };
  
  useEffect(() => {
    Promise.all([
      axios.get(`${API}/vehicles`),
      axios.get(`${API}/vehicles/brands/list`),
      axios.get(`${API}/vehicles/categories/list`)
    ]).then(([vehiclesRes, brandsRes, catsRes]) => {
      setVehicles(vehiclesRes.data);
      setBrands(brandsRes.data.brands);
      setCategories(catsRes.data.categories);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, []);
  
  useEffect(() => {
    fetchVehicles();
  }, [filters]);
  
  const toggleCompare = (vehicle) => {
    if (compareList.find(v => v.id === vehicle.id)) {
      setCompareList(compareList.filter(v => v.id !== vehicle.id));
    } else if (compareList.length < 3) {
      setCompareList([...compareList, vehicle]);
    }
  };
  
  if (loading) return <div className="flex items-center justify-center min-h-screen"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div></div>;
  
  return (
    <div className="max-w-7xl mx-auto px-4 py-8" data-testid="vehicles-page">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">🚗 Fahrzeug-Datenbank</h1>
        <p className="text-slate-600">{vehicles.length} Elektrofahrzeuge vergleichen</p>
      </div>
      
      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-6" data-testid="vehicle-filters">
        <div className="flex items-center space-x-2 mb-4">
          <Filter size={20} className="text-slate-500" />
          <span className="font-semibold">Filter</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          <select 
            value={filters.brand} 
            onChange={(e) => setFilters({...filters, brand: e.target.value})}
            className="border border-slate-300 rounded-lg px-3 py-2 text-sm"
            data-testid="filter-brand"
          >
            <option value="">Alle Marken</option>
            {brands.map(b => <option key={b} value={b}>{b}</option>)}
          </select>
          <select 
            value={filters.category} 
            onChange={(e) => setFilters({...filters, category: e.target.value})}
            className="border border-slate-300 rounded-lg px-3 py-2 text-sm"
            data-testid="filter-category"
          >
            <option value="">Alle Kategorien</option>
            {categories.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <input 
            type="number" 
            placeholder="Min. Preis CHF"
            value={filters.minPrice}
            onChange={(e) => setFilters({...filters, minPrice: e.target.value})}
            className="border border-slate-300 rounded-lg px-3 py-2 text-sm"
            data-testid="filter-min-price"
          />
          <input 
            type="number" 
            placeholder="Max. Preis CHF"
            value={filters.maxPrice}
            onChange={(e) => setFilters({...filters, maxPrice: e.target.value})}
            className="border border-slate-300 rounded-lg px-3 py-2 text-sm"
            data-testid="filter-max-price"
          />
          <input 
            type="number" 
            placeholder="Min. Reichweite km"
            value={filters.minRange}
            onChange={(e) => setFilters({...filters, minRange: e.target.value})}
            className="border border-slate-300 rounded-lg px-3 py-2 text-sm"
            data-testid="filter-min-range"
          />
          <select 
            value={`${filters.sortBy}-${filters.sortOrder}`} 
            onChange={(e) => {
              const [sortBy, sortOrder] = e.target.value.split('-');
              setFilters({...filters, sortBy, sortOrder});
            }}
            className="border border-slate-300 rounded-lg px-3 py-2 text-sm"
            data-testid="filter-sort"
          >
            <option value="price_chf-asc">Preis ↑</option>
            <option value="price_chf-desc">Preis ↓</option>
            <option value="range_wltp_km-desc">Reichweite ↓</option>
            <option value="range_wltp_km-asc">Reichweite ↑</option>
            <option value="acceleration_0_100-asc">0-100 schnellste</option>
          </select>
        </div>
      </div>
      
      {/* Compare Bar */}
      {compareList.length > 0 && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 mb-6 flex items-center justify-between" data-testid="compare-bar">
          <div className="flex items-center space-x-4">
            <span className="font-medium text-emerald-800">Vergleich ({compareList.length}/3):</span>
            {compareList.map(v => (
              <span key={v.id} className="bg-white px-3 py-1 rounded-lg text-sm flex items-center space-x-2">
                <span>{v.brand} {v.model}</span>
                <button onClick={() => toggleCompare(v)} className="text-slate-400 hover:text-red-500"><X size={14} /></button>
              </span>
            ))}
          </div>
          <button 
            onClick={() => setShowCompare(true)}
            className="bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700"
            data-testid="compare-button"
          >
            Vergleichen
          </button>
        </div>
      )}
      
      {/* Vehicle Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {vehicles.map((vehicle) => (
          <div key={vehicle.id} className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden hover:shadow-md transition-all" data-testid={`vehicle-card-${vehicle.id}`}>
            <div className="aspect-video bg-slate-100 relative">
              <img 
                src={vehicle.image_url || 'https://images.unsplash.com/photo-1593941707882-a5bba14938c7?w=400'} 
                alt={`${vehicle.brand} ${vehicle.model}`}
                className="w-full h-full object-cover"
              />
              <span className="absolute top-3 left-3 bg-white/90 px-2 py-1 rounded text-xs font-medium">{vehicle.category}</span>
            </div>
            <div className="p-4">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h3 className="font-bold text-lg">{vehicle.brand} {vehicle.model}</h3>
                  <p className="text-slate-500 text-sm">{vehicle.variant}</p>
                </div>
                <button 
                  onClick={() => toggleCompare(vehicle)}
                  className={`p-2 rounded-lg transition-all ${compareList.find(v => v.id === vehicle.id) ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-100 text-slate-400 hover:bg-emerald-50'}`}
                  data-testid={`compare-toggle-${vehicle.id}`}
                >
                  <CheckCircle size={20} />
                </button>
              </div>
              
              <div className="grid grid-cols-2 gap-2 mb-4">
                <div className="bg-slate-50 rounded-lg p-2 text-center">
                  <p className="text-xs text-slate-500">Reichweite</p>
                  <p className="font-bold text-emerald-600">{vehicle.range_wltp_km} km</p>
                </div>
                <div className="bg-slate-50 rounded-lg p-2 text-center">
                  <p className="text-xs text-slate-500">Batterie</p>
                  <p className="font-bold">{vehicle.battery_kwh} kWh</p>
                </div>
                <div className="bg-slate-50 rounded-lg p-2 text-center">
                  <p className="text-xs text-slate-500">0-100 km/h</p>
                  <p className="font-bold">{vehicle.acceleration_0_100}s</p>
                </div>
                <div className="bg-slate-50 rounded-lg p-2 text-center">
                  <p className="text-xs text-slate-500">DC-Laden</p>
                  <p className="font-bold">{vehicle.charging_dc_kw} kW</p>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <p className="text-2xl font-bold">CHF {vehicle.price_chf.toLocaleString('de-CH')}</p>
                <span className="text-xs text-slate-500">{vehicle.year}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Compare Modal */}
      {showCompare && compareList.length > 0 && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" data-testid="compare-modal">
          <div className="bg-white rounded-2xl shadow-xl max-w-5xl w-full max-h-[90vh] overflow-auto">
            <div className="sticky top-0 bg-white border-b border-slate-200 p-4 flex items-center justify-between">
              <h2 className="text-xl font-bold">Fahrzeugvergleich</h2>
              <button onClick={() => setShowCompare(false)} className="p-2 hover:bg-slate-100 rounded-lg"><X size={24} /></button>
            </div>
            <div className="p-6">
              <table className="w-full">
                <thead>
                  <tr>
                    <th className="text-left p-2"></th>
                    {compareList.map(v => (
                      <th key={v.id} className="text-center p-2">
                        <p className="font-bold">{v.brand}</p>
                        <p className="text-sm text-slate-500">{v.model}</p>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {[
                    { label: 'Preis', key: 'price_chf', format: (v) => `CHF ${v.toLocaleString('de-CH')}` },
                    { label: 'Reichweite WLTP', key: 'range_wltp_km', format: (v) => `${v} km` },
                    { label: 'Batterie', key: 'battery_kwh', format: (v) => `${v} kWh` },
                    { label: 'Verbrauch', key: 'consumption_kwh_100km', format: (v) => `${v} kWh/100km` },
                    { label: '0-100 km/h', key: 'acceleration_0_100', format: (v) => `${v}s` },
                    { label: 'Höchstgeschw.', key: 'top_speed_kmh', format: (v) => `${v} km/h` },
                    { label: 'DC-Laden', key: 'charging_dc_kw', format: (v) => `${v} kW` },
                    { label: 'AC-Laden', key: 'charging_ac_kw', format: (v) => `${v} kW` },
                    { label: 'Kofferraum', key: 'cargo_liters', format: (v) => `${v} L` },
                    { label: 'Sitze', key: 'seats', format: (v) => v },
                    { label: 'Antrieb', key: 'drivetrain', format: (v) => v },
                  ].map((row, idx) => (
                    <tr key={idx} className={idx % 2 === 0 ? 'bg-slate-50' : ''}>
                      <td className="p-3 font-medium text-slate-700">{row.label}</td>
                      {compareList.map(v => (
                        <td key={v.id} className="p-3 text-center">{row.format(v[row.key])}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50">
      <BrowserRouter>
        <Navigation />
        <main>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/fahrzeuge" element={<VehiclesPage />} />
            <Route path="/reichweite" element={<RangePage />} />
            <Route path="/wissen" element={<KnowledgePage />} />
            <Route path="/kostenrechner" element={<CostCalculatorPage />} />
            <Route path="/news" element={<NewsPage />} />
          </Routes>
        </main>
        <Footer />
      </BrowserRouter>
    </div>
  );
}

// ==================== RANGE & CHARGING PAGE ====================

const RangePage = () => {
  const [rangeParams, setRangeParams] = useState({
    wltp_range_km: 450,
    temperature_c: 20,
    speed_kmh: 100,
    climate_on: false,
    highway_percent: 50
  });
  const [rangeResult, setRangeResult] = useState(null);
  const [stations, setStations] = useState([]);
  const [networks, setNetworks] = useState([]);
  const [loadingStations, setLoadingStations] = useState(false);
  const [location, setLocation] = useState({ lat: 47.3769, lng: 8.5417, city: 'Zürich' });
  
  useEffect(() => {
    axios.get(`${API}/charging/networks`).then(res => setNetworks(res.data.networks)).catch(console.error);
  }, []);
  
  const calculateRange = async () => {
    try {
      const params = new URLSearchParams({
        wltp_range_km: rangeParams.wltp_range_km,
        temperature_c: rangeParams.temperature_c,
        speed_kmh: rangeParams.speed_kmh,
        climate_on: rangeParams.climate_on,
        highway_percent: rangeParams.highway_percent
      });
      const res = await axios.post(`${API}/calculator/range?${params}`);
      setRangeResult(res.data);
    } catch (err) {
      console.error(err);
    }
  };
  
  const fetchStations = async () => {
    setLoadingStations(true);
    try {
      const res = await axios.get(`${API}/charging/stations?lat=${location.lat}&lng=${location.lng}&radius=25&limit=20`);
      setStations(res.data.stations || []);
    } catch (err) {
      console.error(err);
    }
    setLoadingStations(false);
  };
  
  useEffect(() => {
    calculateRange();
  }, [rangeParams]);
  
  useEffect(() => {
    fetchStations();
  }, [location]);
  
  const cities = [
    { name: 'Zürich', lat: 47.3769, lng: 8.5417 },
    { name: 'Bern', lat: 46.9480, lng: 7.4474 },
    { name: 'Basel', lat: 47.5596, lng: 7.5886 },
    { name: 'Genf', lat: 46.2044, lng: 6.1432 },
    { name: 'Lausanne', lat: 46.5197, lng: 6.6323 },
    { name: 'Luzern', lat: 47.0502, lng: 8.3093 },
  ];
  
  return (
    <div className="max-w-7xl mx-auto px-4 py-8" data-testid="range-page">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">⚡ Reichweite & Laden</h1>
        <p className="text-slate-600">Realistische Reichweite berechnen und Ladestationen finden</p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Range Calculator */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h2 className="font-bold text-xl mb-4 flex items-center space-x-2">
              <Gauge size={24} className="text-emerald-600" />
              <span>Reichweiten-Rechner</span>
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">WLTP-Reichweite: {rangeParams.wltp_range_km} km</label>
                <input 
                  type="range" 
                  min="200" 
                  max="800" 
                  value={rangeParams.wltp_range_km}
                  onChange={(e) => setRangeParams({...rangeParams, wltp_range_km: parseInt(e.target.value)})}
                  className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-emerald-600"
                  data-testid="range-wltp-slider"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Temperatur: {rangeParams.temperature_c}°C</label>
                <input 
                  type="range" 
                  min="-20" 
                  max="40" 
                  value={rangeParams.temperature_c}
                  onChange={(e) => setRangeParams({...rangeParams, temperature_c: parseInt(e.target.value)})}
                  className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-emerald-600"
                  data-testid="range-temp-slider"
                />
                <div className="flex justify-between text-xs text-slate-400 mt-1">
                  <span>❄️ -20°C</span>
                  <span>☀️ 40°C</span>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Geschwindigkeit: {rangeParams.speed_kmh} km/h</label>
                <input 
                  type="range" 
                  min="50" 
                  max="150" 
                  value={rangeParams.speed_kmh}
                  onChange={(e) => setRangeParams({...rangeParams, speed_kmh: parseInt(e.target.value)})}
                  className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-emerald-600"
                  data-testid="range-speed-slider"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Autobahnanteil: {rangeParams.highway_percent}%</label>
                <input 
                  type="range" 
                  min="0" 
                  max="100" 
                  value={rangeParams.highway_percent}
                  onChange={(e) => setRangeParams({...rangeParams, highway_percent: parseInt(e.target.value)})}
                  className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-emerald-600"
                  data-testid="range-highway-slider"
                />
              </div>
              
              <label className="flex items-center space-x-3 cursor-pointer">
                <input 
                  type="checkbox" 
                  checked={rangeParams.climate_on}
                  onChange={(e) => setRangeParams({...rangeParams, climate_on: e.target.checked})}
                  className="w-5 h-5 text-emerald-600 rounded"
                  data-testid="range-climate-checkbox"
                />
                <span>Klimaanlage/Heizung aktiv</span>
              </label>
            </div>
            
            {/* Result */}
            {rangeResult && (
              <div className="mt-6 bg-gradient-to-br from-emerald-50 to-emerald-100 rounded-xl p-6" data-testid="range-result">
                <div className="text-center">
                  <p className="text-sm text-emerald-700 mb-1">Realistische Reichweite</p>
                  <p className="text-5xl font-bold text-emerald-600">{rangeResult.calculated_range_km} km</p>
                  <p className="text-sm text-emerald-600 mt-2">{rangeResult.efficiency_percent}% der WLTP-Angabe</p>
                </div>
                
                <div className="mt-4 space-y-2">
                  {rangeResult.tips?.map((tip, idx) => (
                    <div key={idx} className="flex items-start space-x-2 text-sm text-emerald-800">
                      <Info size={16} className="mt-0.5 flex-shrink-0" />
                      <span>{tip}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
        
        {/* Charging Stations */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h2 className="font-bold text-xl mb-4 flex items-center space-x-2">
              <MapPin size={24} className="text-emerald-600" />
              <span>Ladestationen in der Nähe</span>
            </h2>
            
            <div className="flex flex-wrap gap-2 mb-4">
              {cities.map((city) => (
                <button
                  key={city.name}
                  onClick={() => setLocation({ lat: city.lat, lng: city.lng, city: city.name })}
                  className={`px-3 py-1 rounded-full text-sm transition-all ${
                    location.city === city.name 
                      ? 'bg-emerald-600 text-white' 
                      : 'bg-slate-100 hover:bg-slate-200'
                  }`}
                  data-testid={`city-${city.name.toLowerCase()}`}
                >
                  {city.name}
                </button>
              ))}
            </div>
            
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {loadingStations ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mx-auto"></div>
                </div>
              ) : stations.length > 0 ? (
                stations.map((station, idx) => (
                  <div key={idx} className="border border-slate-200 rounded-lg p-3 hover:bg-slate-50" data-testid={`station-${idx}`}>
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium">{station.name || 'Ladestation'}</p>
                        <p className="text-sm text-slate-500">{station.address}, {station.city}</p>
                      </div>
                      {station.is_fast_charger && (
                        <span className="bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded text-xs">⚡ Schnell</span>
                      )}
                    </div>
                    <div className="flex items-center space-x-4 mt-2 text-sm text-slate-600">
                      <span>{station.num_points} Ladepunkte</span>
                      {station.max_power_kw > 0 && <span>{station.max_power_kw} kW</span>}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-center text-slate-500 py-4">Keine Ladestationen gefunden</p>
              )}
            </div>
            
            <a 
              href="https://ich-tanke-strom.ch" 
              target="_blank" 
              rel="noopener noreferrer"
              className="mt-4 flex items-center justify-center space-x-2 text-emerald-600 hover:text-emerald-700"
            >
              <span>Alle Stationen auf ich-tanke-strom.ch</span>
              <ExternalLink size={16} />
            </a>
          </div>
        </div>
      </div>
      
      {/* Network Pricing */}
      <div className="mt-8 bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h2 className="font-bold text-xl mb-4 flex items-center space-x-2">
          <Fuel size={24} className="text-emerald-600" />
          <span>Preisvergleich Ladenetzwerke</span>
        </h2>
        
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="text-left p-3">Netzwerk</th>
                <th className="text-center p-3">AC (kWh)</th>
                <th className="text-center p-3">DC 50kW</th>
                <th className="text-center p-3">DC 150kW</th>
                <th className="text-center p-3">DC 150kW+</th>
                <th className="text-center p-3">Abo</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {networks.map((network, idx) => (
                <tr key={idx} className="hover:bg-slate-50">
                  <td className="p-3 font-medium">
                    <a href={network.url} target="_blank" rel="noopener noreferrer" className="text-emerald-600 hover:underline">
                      {network.name}
                    </a>
                  </td>
                  <td className="text-center p-3">{network.ac_kwh ? `CHF ${network.ac_kwh}` : '-'}</td>
                  <td className="text-center p-3">{network.dc_50_kwh ? `CHF ${network.dc_50_kwh}` : '-'}</td>
                  <td className="text-center p-3">{network.dc_150_kwh ? `CHF ${network.dc_150_kwh}` : '-'}</td>
                  <td className="text-center p-3">{network.dc_fast_kwh ? `CHF ${network.dc_fast_kwh}` : '-'}</td>
                  <td className="text-center p-3 text-slate-500">{network.subscription || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-slate-400 mt-4">Stand: Januar 2025. Preise können variieren.</p>
      </div>
    </div>
  );
};

// ==================== KNOWLEDGE PAGE ====================

const KnowledgePage = () => {
  const [articles, setArticles] = useState([]);
  const [glossary, setGlossary] = useState([]);
  const [myths, setMyths] = useState([]);
  const [categories, setCategories] = useState([]);
  const [activeCategory, setActiveCategory] = useState(null);
  const [expandedArticle, setExpandedArticle] = useState(null);
  const [expandedMyth, setExpandedMyth] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  
  useEffect(() => {
    Promise.all([
      axios.get(`${API}/knowledge/articles`),
      axios.get(`${API}/knowledge/glossary`),
      axios.get(`${API}/knowledge/myths`),
      axios.get(`${API}/knowledge/categories`)
    ]).then(([articlesRes, glossaryRes, mythsRes, catsRes]) => {
      setArticles(articlesRes.data.articles);
      setGlossary(glossaryRes.data.terms);
      setMyths(mythsRes.data.myths);
      setCategories(catsRes.data.categories);
    }).catch(console.error);
  }, []);
  
  const filteredGlossary = glossary.filter(term => 
    term.term.toLowerCase().includes(searchTerm.toLowerCase()) ||
    term.definition.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  return (
    <div className="max-w-7xl mx-auto px-4 py-8" data-testid="knowledge-page">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">🧠 EV-Wissen</h1>
        <p className="text-slate-600">Alles über Elektromobilität verständlich erklärt</p>
      </div>
      
      {/* Categories */}
      <div className="flex flex-wrap gap-3 mb-8">
        <button
          onClick={() => setActiveCategory(null)}
          className={`px-4 py-2 rounded-lg font-medium transition-all ${
            !activeCategory ? 'bg-emerald-600 text-white' : 'bg-slate-100 hover:bg-slate-200'
          }`}
          data-testid="category-all"
        >
          Alle Themen
        </button>
        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setActiveCategory(cat.id)}
            className={`px-4 py-2 rounded-lg font-medium transition-all flex items-center space-x-2 ${
              activeCategory === cat.id ? 'bg-emerald-600 text-white' : 'bg-slate-100 hover:bg-slate-200'
            }`}
            data-testid={`category-${cat.id}`}
          >
            <span>{cat.icon}</span>
            <span>{cat.name}</span>
          </button>
        ))}
      </div>
      
      {/* Articles */}
      <div className="mb-12">
        <h2 className="text-2xl font-bold mb-6">📚 Wissensartikel</h2>
        <div className="space-y-4">
          {articles
            .filter(a => !activeCategory || a.category === activeCategory)
            .map((article) => (
            <div 
              key={article.id} 
              className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden"
              data-testid={`article-${article.id}`}
            >
              <button
                onClick={() => setExpandedArticle(expandedArticle === article.id ? null : article.id)}
                className="w-full p-6 text-left flex items-center justify-between hover:bg-slate-50 transition-all"
              >
                <div>
                  <h3 className="font-bold text-lg">{article.title}</h3>
                  <p className="text-slate-600 text-sm mt-1">{article.summary}</p>
                </div>
                {expandedArticle === article.id ? <ChevronUp size={24} /> : <ChevronDown size={24} />}
              </button>
              
              {expandedArticle === article.id && (
                <div className="px-6 pb-6 border-t border-slate-100">
                  <div className="prose prose-slate max-w-none mt-4">
                    {article.content.split('\n').map((para, idx) => {
                      if (para.startsWith('**') && para.endsWith('**')) {
                        return <h4 key={idx} className="font-bold text-lg mt-4 mb-2">{para.replace(/\*\*/g, '')}</h4>;
                      } else if (para.startsWith('- ')) {
                        return <li key={idx} className="ml-4">{para.substring(2)}</li>;
                      } else if (para.startsWith('| ')) {
                        return null; // Skip table rows for now
                      } else if (para.trim()) {
                        return <p key={idx} className="mb-2">{para}</p>;
                      }
                      return null;
                    })}
                  </div>
                  <div className="flex flex-wrap gap-2 mt-4">
                    {article.keywords.map((kw, idx) => (
                      <span key={idx} className="bg-slate-100 px-2 py-1 rounded text-xs text-slate-600">{kw}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
      
      {/* Myths & Facts */}
      <div className="mb-12">
        <h2 className="text-2xl font-bold mb-6">🔍 Mythen vs. Fakten</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {myths.map((myth) => (
            <div 
              key={myth.id} 
              className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden"
              data-testid={`myth-${myth.id}`}
            >
              <button
                onClick={() => setExpandedMyth(expandedMyth === myth.id ? null : myth.id)}
                className="w-full p-4 text-left hover:bg-slate-50 transition-all"
              >
                <div className="flex items-start space-x-3">
                  <XCircle className="text-red-500 flex-shrink-0 mt-1" size={20} />
                  <div className="flex-1">
                    <p className="font-medium text-red-700">Mythos:</p>
                    <p className="text-slate-800">"{myth.myth}"</p>
                  </div>
                  {expandedMyth === myth.id ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                </div>
              </button>
              
              {expandedMyth === myth.id && (
                <div className="px-4 pb-4 border-t border-slate-100">
                  <div className="flex items-start space-x-3 mt-4">
                    <CheckCircle className="text-emerald-500 flex-shrink-0 mt-1" size={20} />
                    <div>
                      <p className="font-medium text-emerald-700">Fakt:</p>
                      <p className="text-slate-700">{myth.fact}</p>
                      <p className="text-xs text-slate-500 mt-2">Quelle: {myth.source}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
      
      {/* Glossary */}
      <div>
        <h2 className="text-2xl font-bold mb-6">📖 Glossar A-Z</h2>
        
        <div className="relative mb-6">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={20} />
          <input
            type="text"
            placeholder="Begriff suchen..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            data-testid="glossary-search"
          />
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredGlossary.map((term, idx) => (
            <div key={idx} className="bg-white rounded-xl shadow-sm border border-slate-200 p-4" data-testid={`glossary-${idx}`}>
              <div className="flex items-start justify-between">
                <h4 className="font-bold text-emerald-600">{term.term}</h4>
                <span className="bg-slate-100 px-2 py-0.5 rounded text-xs">{term.category}</span>
              </div>
              <p className="text-slate-600 text-sm mt-2">{term.definition}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// ==================== COST CALCULATOR PAGE ====================

const CostCalculatorPage = () => {
  const [cantons, setCantons] = useState([]);
  const [input, setInput] = useState({
    yearly_km: 15000,
    electricity_price_kwh: 0.25,
    petrol_price_liter: 1.85,
    ev_consumption_kwh_100km: 17,
    ice_consumption_l_100km: 7,
    canton: 'ZH'
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    axios.get(`${API}/calculator/cantons`).then(res => setCantons(res.data.cantons)).catch(console.error);
  }, []);
  
  const calculate = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/calculator/cost`, input);
      setResult(res.data);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };
  
  useEffect(() => {
    calculate();
  }, [input]);
  
  const selectedCanton = cantons.find(c => c.code === input.canton);
  
  return (
    <div className="max-w-7xl mx-auto px-4 py-8" data-testid="calculator-page">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">💰 Kostenrechner</h1>
        <p className="text-slate-600">TCO-Vergleich: Elektroauto vs. Verbrenner</p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Input Form */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 sticky top-24">
            <h2 className="font-bold text-lg mb-4">Ihre Angaben</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Jährliche Kilometer</label>
                <input
                  type="number"
                  value={input.yearly_km}
                  onChange={(e) => setInput({...input, yearly_km: parseInt(e.target.value) || 0})}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2"
                  data-testid="input-yearly-km"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Kanton</label>
                <select
                  value={input.canton}
                  onChange={(e) => setInput({...input, canton: e.target.value})}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2"
                  data-testid="input-canton"
                >
                  {cantons.map(c => <option key={c.code} value={c.code}>{c.name}</option>)}
                </select>
                {selectedCanton?.incentive > 0 && (
                  <p className="text-xs text-emerald-600 mt-1">🎁 Förderung: CHF {selectedCanton.incentive}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Strompreis (CHF/kWh)</label>
                <input
                  type="number"
                  step="0.01"
                  value={input.electricity_price_kwh}
                  onChange={(e) => setInput({...input, electricity_price_kwh: parseFloat(e.target.value) || 0})}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2"
                  data-testid="input-electricity-price"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Benzinpreis (CHF/L)</label>
                <input
                  type="number"
                  step="0.01"
                  value={input.petrol_price_liter}
                  onChange={(e) => setInput({...input, petrol_price_liter: parseFloat(e.target.value) || 0})}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2"
                  data-testid="input-petrol-price"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">EV-Verbrauch (kWh/100km)</label>
                <input
                  type="number"
                  step="0.1"
                  value={input.ev_consumption_kwh_100km}
                  onChange={(e) => setInput({...input, ev_consumption_kwh_100km: parseFloat(e.target.value) || 0})}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2"
                  data-testid="input-ev-consumption"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Verbrenner-Verbrauch (L/100km)</label>
                <input
                  type="number"
                  step="0.1"
                  value={input.ice_consumption_l_100km}
                  onChange={(e) => setInput({...input, ice_consumption_l_100km: parseFloat(e.target.value) || 0})}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2"
                  data-testid="input-ice-consumption"
                />
              </div>
            </div>
          </div>
        </div>
        
        {/* Results */}
        <div className="lg:col-span-2">
          {result && (
            <div className="space-y-6">
              {/* Savings Highlight */}
              <div className="bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl p-6 text-white" data-testid="savings-highlight">
                <div className="text-center">
                  <p className="text-emerald-100 mb-1">Jährliche Ersparnis mit EV</p>
                  <p className="text-5xl font-bold">CHF {result.yearly_savings.toLocaleString('de-CH')}</p>
                  <p className="text-emerald-100 mt-4">In 5 Jahren: <span className="font-bold text-white">CHF {result.five_year_savings.toLocaleString('de-CH')}</span></p>
                </div>
              </div>
              
              {/* Cost Comparison */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <h3 className="font-bold text-lg mb-4">Jährliche Kosten im Detail</h3>
                
                <div className="grid grid-cols-3 gap-4 text-center mb-6">
                  <div></div>
                  <div className="font-bold text-emerald-600 flex items-center justify-center space-x-2">
                    <Zap size={20} />
                    <span>Elektroauto</span>
                  </div>
                  <div className="font-bold text-slate-600 flex items-center justify-center space-x-2">
                    <Fuel size={20} />
                    <span>Verbrenner</span>
                  </div>
                </div>
                
                <div className="space-y-4">
                  {[
                    { label: 'Energie / Kraftstoff', ev: result.ev_yearly_fuel_cost, ice: result.ice_yearly_fuel_cost },
                    { label: 'Service & Wartung', ev: result.ev_yearly_maintenance, ice: result.ice_yearly_maintenance },
                    { label: 'Motorfahrzeugsteuer', ev: result.ev_yearly_tax, ice: result.ice_yearly_tax },
                    { label: 'Versicherung', ev: result.ev_yearly_insurance, ice: result.ice_yearly_insurance },
                  ].map((row, idx) => (
                    <div key={idx} className="grid grid-cols-3 gap-4 py-3 border-b border-slate-100">
                      <div className="text-slate-600">{row.label}</div>
                      <div className="text-center font-medium">CHF {row.ev.toLocaleString('de-CH')}</div>
                      <div className="text-center font-medium">CHF {row.ice.toLocaleString('de-CH')}</div>
                    </div>
                  ))}
                  
                  <div className="grid grid-cols-3 gap-4 py-3 bg-slate-50 rounded-lg font-bold">
                    <div>Total pro Jahr</div>
                    <div className="text-center text-emerald-600">CHF {result.ev_total_yearly.toLocaleString('de-CH')}</div>
                    <div className="text-center text-slate-700">CHF {result.ice_total_yearly.toLocaleString('de-CH')}</div>
                  </div>
                </div>
              </div>
              
              {/* Visual Comparison */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <h3 className="font-bold text-lg mb-4">Kostenvergleich visualisiert</h3>
                
                <div className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">Elektroauto</span>
                      <span className="text-sm text-emerald-600 font-bold">CHF {result.ev_total_yearly.toLocaleString('de-CH')}</span>
                    </div>
                    <div className="h-8 bg-slate-100 rounded-lg overflow-hidden">
                      <div 
                        className="h-full bg-emerald-500 rounded-lg flex items-center justify-end pr-2"
                        style={{ width: `${(result.ev_total_yearly / result.ice_total_yearly) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">Verbrenner</span>
                      <span className="text-sm text-slate-600 font-bold">CHF {result.ice_total_yearly.toLocaleString('de-CH')}</span>
                    </div>
                    <div className="h-8 bg-slate-100 rounded-lg overflow-hidden">
                      <div className="h-full bg-slate-400 rounded-lg w-full"></div>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Canton Info */}
              {selectedCanton && (
                <div className="bg-blue-50 border border-blue-200 rounded-xl p-6" data-testid="canton-info">
                  <h3 className="font-bold text-lg mb-2 text-blue-800">ℹ️ Infos für {selectedCanton.name}</h3>
                  <ul className="space-y-2 text-blue-700">
                    <li>• Motorfahrzeugsteuer EV: CHF {selectedCanton.ev_tax}/Jahr</li>
                    <li>• Motorfahrzeugsteuer Verbrenner: CHF {selectedCanton.ice_tax}/Jahr</li>
                    {selectedCanton.incentive > 0 && (
                      <li className="font-medium">• 🎁 Kaufförderung: CHF {selectedCanton.incentive}</li>
                    )}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// ==================== NEWS PAGE ====================

const NewsPage = () => {
  const newsFeeds = [
    { name: 'Electrive', url: 'https://www.electrive.net/', icon: '🔌' },
    { name: 'InsideEVs', url: 'https://insideevs.com/', icon: '🚗' },
    { name: 'Elektroauto-News', url: 'https://www.elektroauto-news.net/', icon: '📰' },
    { name: 'Auto-Schweiz', url: 'https://auto.swiss/', icon: '🇨🇭' },
    { name: 'TCS', url: 'https://www.tcs.ch/', icon: '🛡️' },
    { name: 'Swiss eMobility', url: 'https://www.swiss-emobility.ch/', icon: '⚡' },
  ];
  
  return (
    <div className="max-w-7xl mx-auto px-4 py-8" data-testid="news-page">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">📰 News Hub</h1>
        <p className="text-slate-600">Aktuelle Nachrichten aus der Welt der Elektromobilität</p>
      </div>
      
      <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6 mb-8">
        <div className="flex items-start space-x-3">
          <AlertCircle className="text-yellow-600 flex-shrink-0 mt-1" size={24} />
          <div>
            <h3 className="font-bold text-yellow-800">News-Feed in Entwicklung</h3>
            <p className="text-yellow-700 mt-1">
              Wir arbeiten an einer automatischen Aggregation von EV-News aus verschiedenen Quellen. 
              In der Zwischenzeit finden Sie unten Links zu den besten Quellen.
            </p>
          </div>
        </div>
      </div>
      
      <h2 className="text-xl font-bold mb-4">🔗 Empfohlene Quellen</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {newsFeeds.map((feed, idx) => (
          <a
            key={idx}
            href={feed.url}
            target="_blank"
            rel="noopener noreferrer"
            className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md hover:border-emerald-300 transition-all flex items-center space-x-4"
            data-testid={`news-feed-${idx}`}
          >
            <span className="text-3xl">{feed.icon}</span>
            <div>
              <h3 className="font-bold">{feed.name}</h3>
              <span className="text-emerald-600 text-sm flex items-center space-x-1">
                <span>Besuchen</span>
                <ExternalLink size={14} />
              </span>
            </div>
          </a>
        ))}
      </div>
      
      <div className="mt-12 bg-slate-100 rounded-xl p-8 text-center">
        <h3 className="text-xl font-bold mb-2">🔔 Newsletter (Coming Soon)</h3>
        <p className="text-slate-600 mb-4">Erhalten Sie wöchentlich die wichtigsten EV-News direkt in Ihr Postfach.</p>
        <div className="flex max-w-md mx-auto">
          <input 
            type="email" 
            placeholder="ihre@email.ch" 
            className="flex-1 px-4 py-3 rounded-l-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            disabled
          />
          <button className="bg-slate-400 text-white px-6 py-3 rounded-r-lg font-medium cursor-not-allowed">
            Anmelden
          </button>
        </div>
        <p className="text-xs text-slate-500 mt-2">Newsletter-Funktion wird bald verfügbar sein</p>
      </div>
    </div>
  );
};
