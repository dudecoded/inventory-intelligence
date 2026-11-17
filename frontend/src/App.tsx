import { useMemo, useState } from "react";
import {
  Activity, AlertTriangle, ArrowDownRight, ArrowUpRight, Bell, Boxes,
  ChevronDown, CircleHelp, Command, LayoutDashboard, Package, Search,
  Settings2, ShoppingCart, Sparkles, TrendingUp, Truck, X,
} from "lucide-react";

type Product = {
  sku: string; name: string; category: string; stock: number;
  demand: number; status: "Healthy" | "Low stock" | "Overstock";
};

const products: Product[] = [
  { sku: "EL-2048", name: "Wireless Headphones", category: "Electronics", stock: 128, demand: 42, status: "Healthy" },
  { sku: "HM-1092", name: "Ceramic Coffee Set", category: "Home & Living", stock: 18, demand: 36, status: "Low stock" },
  { sku: "EL-3011", name: "Mechanical Keyboard", category: "Electronics", stock: 86, demand: 24, status: "Healthy" },
  { sku: "SP-0084", name: "Running Backpack", category: "Sports", stock: 214, demand: 19, status: "Overstock" },
  { sku: "HM-2210", name: "Desk Lamp", category: "Home & Living", stock: 64, demand: 21, status: "Healthy" },
];

const navItems = [
  { label: "Overview", icon: LayoutDashboard },
  { label: "Inventory", icon: Package },
  { label: "Forecasting", icon: TrendingUp },
  { label: "Procurement", icon: ShoppingCart },
];

const chartValues = [34, 43, 39, 55, 48, 62, 57, 71, 64, 79, 73, 91];

function App() {
  const [activeNav, setActiveNav] = useState("Overview");
  const [query, setQuery] = useState("");
  const [period, setPeriod] = useState("30 days");
  const [showNotifications, setShowNotifications] = useState(false);
  const [showHelp, setShowHelp] = useState(false);

  const filteredProducts = useMemo(
    () => products.filter((product) =>
      `${product.name} ${product.sku} ${product.category}`.toLowerCase().includes(query.toLowerCase()),
    ),
    [query],
  );

  const pageTitle = activeNav === "Overview" ? "Overview" : activeNav;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#" aria-label="Inventory Intelligence home">
          <span className="brand-symbol"><Boxes size={20} /></span>
          <span className="brand-copy">stock<span>wise</span><small>INTELLIGENCE</small></span>
        </a>

        <div className="workspace-switcher">
          <div className="workspace-avatar">AC</div>
          <div className="workspace-copy"><strong>Acme Commerce</strong><span>Workspace</span></div>
          <ChevronDown size={15} />
        </div>

        <p className="nav-label">WORKSPACE</p>
        <nav className="main-nav" aria-label="Main navigation">
          {navItems.map(({ label, icon: Icon }) => (
            <button key={label} className={activeNav === label ? "nav-item active" : "nav-item"} onClick={() => setActiveNav(label)}>
              <Icon size={17} strokeWidth={1.8} /><span>{label}</span>
              {label === "Inventory" && <span className="nav-count">5</span>}
            </button>
          ))}
        </nav>

        <p className="nav-label tools-label">MANAGE</p>
        <button className="nav-item" onClick={() => setActiveNav("Suppliers")}><Truck size={17} /><span>Suppliers</span></button>
        <button className="nav-item" onClick={() => setActiveNav("Reports")}><Activity size={17} /><span>Reports & analytics</span></button>

        <div className="sidebar-bottom">
          <div className="upgrade-card">
            <span className="upgrade-icon"><Sparkles size={16} /></span>
            <strong>Make smarter moves</strong>
            <p>Connect your data to unlock inventory insights.</p>
            <button onClick={() => setActiveNav("Integrations")}>Explore integrations <ArrowUpRight size={13} /></button>
          </div>
          <button className="nav-item" onClick={() => setShowHelp(true)}><CircleHelp size={17} /><span>Help & support</span></button>
          <button className="nav-item" onClick={() => setActiveNav("Settings")}><Settings2 size={17} /><span>Settings</span></button>
          <div className="profile-row">
            <div className="profile-avatar">UZ</div>
            <div className="profile-copy"><strong>Uzair Siddiqui</strong><span>Administrator</span></div>
            <button className="icon-button profile-more" aria-label="Profile options"><ChevronDown size={15} /></button>
          </div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumbs"><span>Workspace</span><span className="crumb-slash">/</span><strong>{pageTitle}</strong></div>
          <div className="topbar-actions">
            <label className="search-box">
              <Search size={16} />
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search anything..." aria-label="Search products" />
              <kbd>⌘ K</kbd>
            </label>
            <span className="topbar-divider" />
            <button className="icon-button notification-button" aria-label="Notifications" onClick={() => setShowNotifications(!showNotifications)}>
              <Bell size={18} /><i />
            </button>
            <div className="topbar-avatar">UZ</div>
            {showNotifications && <div className="popover notification-popover"><strong>You're all caught up</strong><p>New stock alerts will appear here.</p></div>}
          </div>
        </header>

        <div className="content">
          <section className="page-heading">
            <div>
              <div className="date-label">TUESDAY, NOVEMBER 18, 2026 <span className="live-dot" /> LIVE OVERVIEW</div>
              <h1>{pageTitle === "Overview" ? "Good morning, Uzair" : pageTitle}<span className="wave">✳</span></h1>
              <p>Here's what's happening with your inventory today.</p>
            </div>
            <div className="heading-actions">
              <button className="button button-secondary" onClick={() => setShowHelp(true)}><CircleHelp size={15} /> How it works</button>
              <button className="button button-primary" onClick={() => setActiveNav("Procurement")}><ShoppingCart size={15} /> Create purchase order</button>
            </div>
          </section>

          <section className="metrics-grid" aria-label="Inventory key performance indicators">
            <MetricCard title="Total inventory value" value="₹24,86,500" change="+8.2%" positive detail="vs. last month" icon={<Boxes size={17} />} />
            <MetricCard title="Active products" value="1,284" change="+4.6%" positive detail="vs. last month" icon={<Package size={17} />} />
            <MetricCard title="Low stock alerts" value="18" change="3 new" positive={false} detail="need your attention" icon={<AlertTriangle size={17} />} />
            <MetricCard title="Forecast accuracy" value="94.2%" change="+2.1%" positive detail="vs. last month" icon={<TrendingUp size={17} />} />
          </section>

          <section className="dashboard-grid">
            <article className="panel demand-panel">
              <div className="panel-header">
                <div><div className="panel-kicker">DEMAND INTELLIGENCE</div><h2>Demand overview</h2><p>Actual sales vs. forecasted demand</p></div>
                <select value={period} onChange={(event) => setPeriod(event.target.value)} aria-label="Chart time period">
                  <option>7 days</option><option>30 days</option><option>90 days</option>
                </select>
              </div>
              <div className="chart-legend"><span><i className="legend-actual" /> Actual sales</span><span><i className="legend-forecast" /> Forecast</span></div>
              <div className="chart-wrap">
                <div className="y-labels"><span>1,000</span><span>750</span><span>500</span><span>250</span><span>0</span></div>
                <svg className="demand-chart" viewBox="0 0 660 220" role="img" aria-label={`Illustrative demand trend for the last ${period}`} preserveAspectRatio="none">
                  <defs><linearGradient id="areaFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#2dbb91" stopOpacity=".2" /><stop offset="100%" stopColor="#2dbb91" stopOpacity="0" /></linearGradient></defs>
                  {[12, 58, 104, 150, 196].map((y) => <line key={y} x1="0" y1={y} x2="660" y2={y} className="grid-line" />)}
                  <path d="M0 164 C30 152 40 142 60 148 S100 120 120 130 S160 110 180 118 S220 90 240 105 S280 82 300 92 S340 68 360 78 S400 88 420 68 S460 55 480 66 S520 42 540 54 S580 30 600 44 S640 22 660 28 L660 196 L0 196Z" fill="url(#areaFill)" />
                  <path d="M0 164 C30 152 40 142 60 148 S100 120 120 130 S160 110 180 118 S220 90 240 105 S280 82 300 92 S340 68 360 78 S400 88 420 68 S460 55 480 66 S520 42 540 54 S580 30 600 44 S640 22 660 28" className="actual-line" />
                  <path d="M0 174 C30 160 40 155 60 158 S100 139 120 145 S160 126 180 133 S220 112 240 119 S280 104 300 110 S340 88 360 98 S400 98 420 88 S460 72 480 82 S520 62 540 72 S580 52 600 62 S640 43 660 48" className="forecast-line" />
                  <circle cx="540" cy="54" r="4" className="chart-point" />
                </svg>
              </div>
              <div className="x-labels"><span>Nov 01</span><span>Nov 05</span><span>Nov 10</span><span>Nov 15</span><span>Nov 18</span></div>
              <div className="chart-insight"><span className="insight-icon"><Sparkles size={14} /></span><p><strong>Demand is trending up.</strong> Forecasted demand is 12% higher than the previous period. Consider reviewing replenishment for fast-moving items.</p></div>
            </article>

            <article className="panel health-panel">
              <div className="panel-header"><div><div className="panel-kicker">STOCK HEALTH</div><h2>Inventory distribution</h2><p>Product status across your catalogue</p></div><button className="more-button" aria-label="More inventory options">···</button></div>
              <div className="health-visual">
                <div className="donut"><div className="donut-center"><strong>1,284</strong><span>Total SKUs</span></div></div>
              </div>
              <div className="health-legend">
                <HealthRow color="green" label="Healthy stock" count="1,046" percent="81.5%" />
                <HealthRow color="amber" label="Low stock" count="168" percent="13.1%" />
                <HealthRow color="red" label="Overstock" count="70" percent="5.4%" />
              </div>
              <button className="text-link" onClick={() => setActiveNav("Inventory")}>View inventory health <ArrowUpRight size={14} /></button>
            </article>
          </section>

          <section className="bottom-grid">
            <article className="panel products-panel">
              <div className="panel-header products-heading">
                <div><div className="panel-kicker">INVENTORY MONITOR</div><h2>Products to watch</h2><p>Items that may need your attention</p></div>
                <button className="text-link" onClick={() => setActiveNav("Inventory")}>View all products <ArrowUpRight size={14} /></button>
              </div>
              <div className="table-scroll">
                <table>
                  <thead><tr><th>PRODUCT</th><th>SKU</th><th>STOCK ON HAND</th><th>30D DEMAND</th><th>STATUS</th></tr></thead>
                  <tbody>
                    {filteredProducts.map((product) => (
                      <tr key={product.sku}>
                        <td><div className="product-cell"><span className="product-thumb">{product.category === "Electronics" ? "◈" : product.category === "Sports" ? "⌁" : "▧"}</span><span><strong>{product.name}</strong><small>{product.category}</small></span></div></td>
                        <td className="sku">{product.sku}</td>
                        <td><strong>{product.stock}</strong><span className="unit"> units</span></td>
                        <td>{product.demand}<span className="unit"> units</span></td>
                        <td><StatusBadge status={product.status} /></td>
                      </tr>
                    ))}
                    {filteredProducts.length === 0 && <tr><td colSpan={5} className="empty-state">No products match “{query}”.</td></tr>}
                  </tbody>
                </table>
              </div>
            </article>

            <article className="panel alerts-panel">
              <div className="panel-header"><div><div className="panel-kicker">ACTION REQUIRED</div><h2>Priority alerts <span className="alert-count">3</span></h2><p>Recommended next steps</p></div><button className="more-button" aria-label="More alert options">···</button></div>
              <AlertItem tone="amber" title="Stock running low" text="Ceramic Coffee Set · 18 units left" time="12 min ago" />
              <AlertItem tone="red" title="Potential stockout" text="Cotton Tote Bag · 4 days of cover" time="38 min ago" />
              <AlertItem tone="blue" title="Reorder recommendation" text="Wireless Mouse · Suggested: 50 units" time="1 hr ago" />
              <button className="text-link alerts-link" onClick={() => setActiveNav("Inventory")}>Review all alerts <ArrowUpRight size={14} /></button>
            </article>
          </section>

          <footer className="app-footer"><span>© 2026 Stockwise Intelligence</span><span><i className="footer-dot" /> All systems operational</span><span>Demo workspace · Sample data</span></footer>
        </div>
      </main>

      {showHelp && <div className="modal-backdrop" onClick={() => setShowHelp(false)}><section className="help-modal" onClick={(event) => event.stopPropagation()}><button className="modal-close" onClick={() => setShowHelp(false)} aria-label="Close"><X size={18} /></button><span className="help-icon"><Sparkles size={20} /></span><p className="panel-kicker">GETTING STARTED</p><h2>Your inventory command centre</h2><p>This dashboard currently uses illustrative sample data. The next development step is connecting real product, sales, and stock records to the API, then replacing demo metrics with validated forecasts and risk signals.</p><button className="button button-primary" onClick={() => setShowHelp(false)}>Got it</button></section></div>}
    </div>
  );
}

function MetricCard({ title, value, change, positive, detail, icon }: { title: string; value: string; change: string; positive: boolean; detail: string; icon: React.ReactNode }) {
  return <article className="metric-card"><div className="metric-top"><span>{title}</span><span className="metric-icon">{icon}</span></div><div className="metric-value">{value}</div><div className="metric-foot"><span className={positive ? "change positive" : "change negative"}>{positive ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />}{change}</span><span>{detail}</span></div></article>;
}

function HealthRow({ color, label, count, percent }: { color: string; label: string; count: string; percent: string }) {
  return <div className="health-row"><span className={`health-dot ${color}`} /><span className="health-label">{label}</span><strong>{count}</strong><small>{percent}</small></div>;
}

function StatusBadge({ status }: { status: Product["status"] }) {
  const className = status === "Healthy" ? "healthy" : status === "Low stock" ? "low" : "over";
  return <span className={`status-badge ${className}`}><i />{status}</span>;
}

function AlertItem({ tone, title, text, time }: { tone: string; title: string; text: string; time: string }) {
  return <div className="alert-item"><span className={`alert-icon ${tone}`}>{tone === "amber" ? <AlertTriangle size={15} /> : tone === "red" ? <AlertTriangle size={15} /> : <ShoppingCart size={15} />}</span><div className="alert-copy"><strong>{title}</strong><p>{text}</p><small>{time}</small></div><ArrowUpRight size={14} className="alert-arrow" /></div>;
}

export default App;
