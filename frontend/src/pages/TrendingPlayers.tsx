import { useEffect, useMemo, useState } from "react";
import { useDebounce } from "../hooks/useDebounce";

type PlayerRow = {
  id: string;
  name: string;
  position: string;
  team: string;
  age: number | null;
  valuation: number;
  overall_rank: number | null;
  position_rank: number | null;
  trend30: number | null;
  adds_24h: number;
  drops_24h: number;
};

type PlayersResp = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  sort_by: string;
  order: "asc" | "desc";
  filters: any;
  items: PlayerRow[];
};

const SORT_OPTIONS = [
  { key: "valuation", label: "Value" },
  { key: "adds_24h", label: "Adds (24h)" },
  { key: "drops_24h", label: "Drops (24h)" },
  { key: "overall_rank", label: "Overall Rank" },
  { key: "position_rank", label: "Pos Rank" },
  { key: "age", label: "Age" },
  { key: "name", label: "Name" },
];

const DEFAULT_POS = ["QB", "RB", "WR", "TE"]; // you can fetch from API too

export default function TrendingPlayers() {
  // filters / controls
  const [q, setQ] = useState("");
  const qDeb = useDebounce(q, 300);

  const [positions, setPositions] = useState<string[]>(DEFAULT_POS);
  const [minVal, setMinVal] = useState<number | "">("");
  const [maxVal, setMaxVal] = useState<number | "">("");

  const [sortBy, setSortBy] = useState<string>("valuation");
  const [order, setOrder] = useState<"asc" | "desc">("desc");

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  // data
  const [data, setData] = useState<PlayersResp | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // sidebar trends
  const [topAdds, setTopAdds] = useState<PlayerRow[]>([]);
  const [topDrops, setTopDrops] = useState<PlayerRow[]>([]);

  // build query string
  const query = useMemo(() => {
    const params = new URLSearchParams();
    params.set("page", String(page));
    params.set("page_size", String(pageSize));
    if (qDeb.trim()) params.set("q", qDeb.trim());
    if (positions.length) params.set("positions", positions.join(","));
    if (minVal !== "") params.set("min_val", String(minVal));
    if (maxVal !== "") params.set("max_val", String(maxVal));
    params.set("sort_by", sortBy);
    params.set("order", order);
    return params.toString();
  }, [qDeb, positions, minVal, maxVal, sortBy, order, page, pageSize]);

  // fetch main table
  useEffect(() => {
    const run = async () => {
      setLoading(true);
      setErr(null);
      try {
        const res = await fetch(`http://127.0.0.1:8000/player_trends/players?${query}`);
        const json = (await res.json()) as PlayersResp;
        if (!res.ok) throw new Error((json as any)?.detail ?? "Failed to load players");
        setData(json);
      } catch (e: any) {
        setErr(e.message || "Failed");
        setData(null);
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [query]);

  // fetch sidebar lists (top adds/drops)
  useEffect(() => {
    const fetchSide = async () => {
      try {
        const a = await fetch(
          "http://127.0.0.1:8000/player_trends/players?sort_by=adds_24h&order=desc&page=1&page_size=5"
        ).then((r) => r.json());
        const d = await fetch(
          "http://127.0.0.1:8000/player_trends/players?sort_by=drops_24h&order=desc&page=1&page_size=5"
        ).then((r) => r.json());
        setTopAdds(a.items || []);
        setTopDrops(d.items || []);
      } catch {
        // ignore sidebar errors
      }
    };
    fetchSide();
  }, []);

  // handlers
  const togglePos = (pos: string) => {
    setPage(1);
    setPositions((prev) =>
      prev.includes(pos) ? prev.filter((p) => p !== pos) : [...prev, pos]
    );
  };
  const clearFilters = () => {
    setQ("");
    setPositions(DEFAULT_POS);
    setMinVal("");
    setMaxVal("");
    setSortBy("valuation");
    setOrder("desc");
    setPage(1);
    setPageSize(25);
  };

  const items = data?.items ?? [];
  const totalPages = data?.total_pages ?? 1;

  return (
    <div className="tp-wrap">
      {/* header controls */}
      <div className="tp-toolbar">
        <div className="tp-chips">
          {DEFAULT_POS.map((p) => (
            <button
              key={p}
              className={`chip ${positions.includes(p) ? "chip--on" : ""}`}
              onClick={() => togglePos(p)}
            >
              {p}
            </button>
          ))}
        </div>

        <div className="tp-search">
          <input
            className="tp-input"
            placeholder="Filter players"
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setPage(1);
            }}
          />
        </div>

        <div className="tp-sorts">
          <label>
            Sort
            <select value={sortBy} onChange={(e) => { setSortBy(e.target.value); setPage(1); }}>
              {SORT_OPTIONS.map((o) => (
                <option key={o.key} value={o.key}>{o.label}</option>
              ))}
            </select>
          </label>
          <button
            className="btn"
            onClick={() => setOrder((o) => (o === "asc" ? "desc" : "asc"))}
            title="Toggle order"
          >
            {order === "asc" ? "▲ asc" : "▼ desc"}
          </button>
          <label>
            Min
            <input
              type="number"
              className="tp-input small"
              value={minVal}
              onChange={(e) => { setMinVal(e.target.value === "" ? "" : Number(e.target.value)); setPage(1); }}
            />
          </label>
          <label>
            Max
            <input
              type="number"
              className="tp-input small"
              value={maxVal}
              onChange={(e) => { setMaxVal(e.target.value === "" ? "" : Number(e.target.value)); setPage(1); }}
            />
          </label>
          <button className="btn ghost" onClick={clearFilters}>Reset</button>
        </div>
      </div>

      <div className="tp-grid">
        {/* main table */}
        <div className="tp-tablecard">
          {loading ? (
            <div className="muted">Loading…</div>
          ) : err ? (
            <div className="error">{err}</div>
          ) : (
            <>
              <table className="tp-table">
                <thead>
                  <tr>
                    <th style={{width: 60}}>#</th>
                    <th>Name</th>
                    <th>Pos</th>
                    <th>Team</th>
                    <th>Age</th>
                    <th>Value</th>
                    <th>Adds 24h</th>
                    <th>Drops 24h</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((p, i) => (
                    <tr key={p.id}>
                      <td>{(data!.page - 1) * data!.page_size + i + 1}</td>
                      <td className="name">{p.name}</td>
                      <td>{p.position}</td>
                      <td>{p.team}</td>
                      <td>{p.age ?? "-"}</td>
                      <td className="num">{p.valuation.toFixed(0)}</td>
                      <td className="num pos">{p.adds_24h > 0 ? `+${p.adds_24h}` : p.adds_24h}</td>
                      <td className="num neg">{p.drops_24h > 0 ? `+${p.drops_24h}` : p.drops_24h}</td>
                    </tr>
                  ))}
                  {!items.length && (
                    <tr><td colSpan={8} className="muted" style={{textAlign:"center"}}>No players</td></tr>
                  )}
                </tbody>
              </table>

              <div className="tp-pager">
                <div className="muted">
                  Page {data?.page} / {totalPages} • Total {data?.total ?? 0}
                </div>
                <div className="tp-pagebtns">
                  <button className="btn" disabled={page <= 1} onClick={() => setPage(1)}>⏮</button>
                  <button className="btn" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>◀</button>
                  <select
                    value={page}
                    onChange={(e) => setPage(Number(e.target.value))}
                  >
                    {Array.from({ length: totalPages || 1 }, (_, i) => i + 1).map((n) => (
                      <option key={n} value={n}>{n}</option>
                    ))}
                  </select>
                  <button className="btn" disabled={page >= (totalPages || 1)} onClick={() => setPage((p) => p + 1)}>▶</button>
                  <button className="btn" disabled={page >= (totalPages || 1)} onClick={() => setPage(totalPages || 1)}>⏭</button>

                  <select
                    value={pageSize}
                    onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}
                  >
                    {[10, 25, 50, 100].map((n) => <option key={n} value={n}>{n}/page</option>)}
                  </select>
                </div>
              </div>
            </>
          )}
        </div>

        {/* sidebar */}
        <aside className="tp-sidebar">
          <div className="tp-sidecard">
            <h4>Trends</h4>
            <div className="tp-sub">Top Risers (last 24h)</div>
            <ul className="tp-mini">
              {topAdds.map((p) => (
                <li key={p.id}>
                  <span className="name">{p.name}</span>
                  <span className="pos">+{p.adds_24h}</span>
                </li>
              ))}
            </ul>
            <div className="tp-sub">Top Fallers (last 24h)</div>
            <ul className="tp-mini">
              {topDrops.map((p) => (
                <li key={p.id}>
                  <span className="name">{p.name}</span>
                  <span className="neg">-{p.drops_24h}</span>
                </li>
              ))}
            </ul>
          </div>
        </aside>
      </div>
    </div>
  );
}
