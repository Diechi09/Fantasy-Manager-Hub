import { useEffect, useState } from "react";

type Welcome = { title: string; message: string };

export default function Home() {
  const [data, setData] = useState<Welcome | null>(null);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/")
      .then(r => r.json())
      .then(setData)
      .catch(() => setData({ title: "Fantasy Manager Hub", message: "The Tool to dominate your leagues" }));
  }, []);

  return (
    <section className="hero">
      <div className="hero-inner">
        <h1>{data?.title ?? "Fantasy Manager Hub"}</h1>
        <p className="tagline">{data?.message ?? ""}</p>
        <div className="cta-row">
          <a className="btn" href="/trade-calculator">Get Started</a>
          <a className="btn ghost" href="/trending">See Trends</a>
        </div>
      </div>
    </section>
  );
}
