import { useState } from "react";

type PlayerLite = { id: string; name: string; pos: string; team: string; val: number };

export default function TradeCalculator() {
  const [sideA, setSideA] = useState<PlayerLite[]>([]);
  const [sideB, setSideB] = useState<PlayerLite[]>([]);
  const [qA, setQA] = useState("");
  const [qB, setQB] = useState("");
  const [resA, setResA] = useState<PlayerLite[]>([]);
  const [resB, setResB] = useState<PlayerLite[]>([]);
  const [result, setResult] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  async function runSearch(query: string) {
    const r = await fetch(`http://127.0.0.1:8000/trade_calculator/search?q=${encodeURIComponent(query)}`);
    if (!r.ok) return [];
    return (await r.json()) as PlayerLite[];
  }

  const searchA = async () => setResA(await runSearch(qA));
  const searchB = async () => setResB(await runSearch(qB));

  const addA = (p: PlayerLite) => {
    if (sideA.some(x => x.id === p.id) || sideB.some(x => x.id === p.id)) return;
    setSideA([...sideA, p]);
    setResA([]);    // clear options after add
    setQA("");      // clear query
    setResult(null);
  };
  const addB = (p: PlayerLite) => {
    if (sideB.some(x => x.id === p.id) || sideA.some(x => x.id === p.id)) return;
    setSideB([...sideB, p]);
    setResB([]);    // clear options after add
    setQB("");      // clear query
    setResult(null);
  };
  const removeA = (id: string) => { setSideA(sideA.filter(p => p.id !== id)); setResult(null); };
  const removeB = (id: string) => { setSideB(sideB.filter(p => p.id !== id)); setResult(null); };

  const simulate = async () => {
    setErr(null);
    setResult(null);
    try {
      const payload = { side_a: sideA.map(p => p.id), side_b: sideB.map(p => p.id) };
      const r = await fetch("http://127.0.0.1:8000/trade_calculator/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data?.detail ?? "Simulation failed");
      setResult(data);
    } catch (e: any) {
      setErr(e.message);
    }
  };

  // submit-on-Enter for each searchbar
  const onSubmitA = (e: React.FormEvent) => { e.preventDefault(); searchA(); };
  const onSubmitB = (e: React.FormEvent) => { e.preventDefault(); searchB(); };

  return (
    <div className="tc-wrap">
      <h2 className="tc-title">Trade Calculator</h2>

      <div className="tc-grid">
        {/* Side A */}
        <div className="tc-col">
          <h3>Side A</h3>
          <form className="tc-searchrow" onSubmit={onSubmitA}>
            <input
              className="tc-input"
              placeholder="Search player…"
              value={qA}
              onChange={e=>setQA(e.target.value)}
            />
            <button className="tc-btn" type="submit">Search</button>
          </form>

          <ul className="tc-results">
            {resA.map(p => (
              <li key={p.id} className="tc-resultrow">
                <button className="tc-add" onClick={()=>addA(p)} title="Add to Side A">+</button>
                <span className="tc-name">{p.name}</span>
                <span className="tc-meta">{p.pos} • {p.team}</span>
                <span className="tc-val">{p.val.toFixed(1)}</span>
              </li>
            ))}
          </ul>

          <div className="tc-selected-title">Selected</div>
          <ul className="tc-picked">
            {sideA.map(p => (
              <li key={p.id} className="tc-pickedrow">
                <span className="tc-name">{p.name}</span>
                <span className="tc-meta">{p.pos} • {p.team}</span>
                <span className="tc-val">{p.val.toFixed(1)}</span>
                <button className="tc-remove" onClick={()=>removeA(p.id)}>x</button>
              </li>
            ))}
          </ul>
        </div>

        {/* Side B */}
        <div className="tc-col">
          <h3>Side B</h3>
          <form className="tc-searchrow" onSubmit={onSubmitB}>
            <input
              className="tc-input"
              placeholder="Search player…"
              value={qB}
              onChange={e=>setQB(e.target.value)}
            />
            <button className="tc-btn" type="submit">Search</button>
          </form>

          <ul className="tc-results">
            {resB.map(p => (
              <li key={p.id} className="tc-resultrow">
                <button className="tc-add tc-add--green" onClick={()=>addB(p)} title="Add to Side B">+</button>
                <span className="tc-name">{p.name}</span>
                <span className="tc-meta">{p.pos} • {p.team}</span>
                <span className="tc-val">{p.val.toFixed(1)}</span>
              </li>
            ))}
          </ul>

          <div className="tc-selected-title">Selected</div>
          <ul className="tc-picked">
            {sideB.map(p => (
              <li key={p.id} className="tc-pickedrow">
                <span className="tc-name">{p.name}</span>
                <span className="tc-meta">{p.pos} • {p.team}</span>
                <span className="tc-val">{p.val.toFixed(1)}</span>
                <button className="tc-remove" onClick={()=>removeB(p.id)}>x</button>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="tc-actions">
        <button className="tc-primary" onClick={simulate} disabled={!sideA.length && !sideB.length}>
          Simulate Trade
        </button>
        {err && <p className="tc-error">{err}</p>}
      </div>

      {result && (
        <div className="tc-resultbox">
          <p><strong>Total A:</strong> {result.side_a.total} &nbsp;|&nbsp; <strong>Total B:</strong> {result.side_b.total}</p>
          <p><strong>Δ (A - B):</strong> {result.delta} &nbsp;|&nbsp; <strong>Winner:</strong> {result.winner} &nbsp;|&nbsp; <strong>Margin:</strong> {result.margin_pct}%</p>
        </div>
      )}
    </div>
  );
}
