import { useEffect, useRef, useState } from "react";
import { useDebounce } from "../hooks/useDebounce";

export type PlayerLite = { id: string; name: string; pos: string; team: string; val: number };

export default function SearchSelect({
  label,
  onAdd,
}: {
  label: string;
  onAdd: (p: PlayerLite) => void;
}) {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const [results, setResults] = useState<PlayerLite[]>([]);
  const debounced = useDebounce(q, 250);
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (!boxRef.current?.contains(e.target as Node)) setOpen(false);
    };
    window.addEventListener("click", onClick);
    return () => window.removeEventListener("click", onClick);
  }, []);

  useEffect(() => {
    const run = async () => {
      const res = await fetch(
        `http://127.0.0.1:8000/trade_calculator/search?q=${encodeURIComponent(debounced)}`
      );
      const data = await res.json();
      setResults(data);
    };
    if (debounced.trim().length >= 2) run();
    else setResults([]);
  }, [debounced]);

  return (
    <div className="searchselect" ref={boxRef}>
      <label>{label}</label>
      <input
        placeholder="Type player name…"
        value={q}
        onChange={(e) => {
          setQ(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
      />
      {open && results.length > 0 && (
        <ul className="dropdown">
          {results.map((r) => (
            <li
              key={r.id}
              onClick={() => {
                onAdd(r);
                setQ("");
                setResults([]);
                setOpen(false);
              }}
            >
              <div className="line1">{r.name}</div>
              <div className="line2">
                {r.pos} • {r.team} • {r.val.toFixed(1)}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
