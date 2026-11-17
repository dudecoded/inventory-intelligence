function App() {
  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand-mark">II</div>
        <div>
          <p className="eyebrow">INVENTORY INTELLIGENCE</p>
          <h1>Inventory, understood.</h1>
        </div>
        <span className="status"><i /> Foundation online</span>
      </header>

      <section className="welcome">
        <p className="eyebrow">DECISION SUPPORT WORKSPACE</p>
        <h2>Turn inventory data into<br /><span>confident decisions.</span></h2>
        <p className="intro">
          Demand forecasting, stock-risk monitoring, and smarter replenishment
          will come together here.
        </p>
      </section>

      <section className="cards" aria-label="Platform modules">
        <article className="card">
          <span className="number">01</span>
          <h3>Demand forecasting</h3>
          <p>Estimate future product demand from historical sales patterns.</p>
          <span className="tag">In development</span>
        </article>
        <article className="card">
          <span className="number">02</span>
          <h3>Inventory risk</h3>
          <p>Surface potential stockouts, excess stock, and slow-moving items.</p>
          <span className="tag">In development</span>
        </article>
        <article className="card">
          <span className="number">03</span>
          <h3>Procurement optimizer</h3>
          <p>Recommend replenishment quantities within real business constraints.</p>
          <span className="tag">In development</span>
        </article>
      </section>

      <footer>Built for better inventory decisions · API and model integrations are next.</footer>
    </main>
  );
}

export default App;
