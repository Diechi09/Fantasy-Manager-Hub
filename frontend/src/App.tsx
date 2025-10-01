import { useEffect, useState } from "react";

type Welcome = { title: string; message: string };

export default function App() {
  const [data, setData] = useState<Welcome | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/") // FastAPI returns welcome JSON at "/"
      .then(r => r.json())
      .then(setData)
      .catch(() => setError("Could not reach backend"));
  }, []);

  return (
    <div className="container">
      <section className="hero card">
        <h1>{data?.title ?? "Fantasy Manager Hub"}</h1>
        <p>{data?.message ?? "Loading…"}</p>
        {error && <p className="error">{error}</p>}
        <div className="row">
          <button className="btn" disabled>Get Started</button>
          <button className="btn ghost" disabled>See Trends</button>
        </div>
      </section>
    </div>
  );
}
