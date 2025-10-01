import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";

// placeholders for now
const TradeCalculator = () => <div className="page"><h2>Trade Calculator</h2></div>;
const Trending        = () => <div className="page"><h2>Trending Players</h2></div>;
const RosterAnalysis  = () => <div className="page"><h2>Roster Analysis</h2></div>;
const CoachAssistant  = () => <div className="page"><h2>Coach Assistant</h2></div>;
const Login           = () => <div className="page"><h2>Login</h2></div>;
const Signup          = () => <div className="page"><h2>Sign Up</h2></div>;

export default function App() {
  return (
    <div className="app-root">
      <Navbar />
      <main className="app-main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/trade-calculator" element={<TradeCalculator />} />
          <Route path="/trending" element={<Trending />} />
          <Route path="/roster-analysis" element={<RosterAnalysis />} />
          <Route path="/coach-assistant" element={<CoachAssistant />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
        </Routes>
      </main>
      <footer className="app-footer">© {new Date().getFullYear()} Fantasy Manager Hub</footer>
    </div>
  );
}
