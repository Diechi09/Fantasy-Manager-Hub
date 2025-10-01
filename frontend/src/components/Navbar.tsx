import { NavLink } from "react-router-dom";

const linkClass = ({ isActive }: { isActive: boolean }) =>
  "nav-link" + (isActive ? " active" : "");

export default function Navbar() {
  return (
    <header className="nav">
      <NavLink to="/" className="brand">FMH</NavLink>
      <nav className="nav-links">
        <NavLink to="/trade-calculator" className={linkClass}>Trade Calculator</NavLink>
        <NavLink to="/trending" className={linkClass}>Trending Players</NavLink>
        <NavLink to="/roster-analysis" className={linkClass}>Roster Analysis</NavLink>
        <NavLink to="/coach-assistant" className={linkClass}>Coach Assistant</NavLink>
      </nav>
      <div className="spacer" />
      <nav className="auth-links">
        <NavLink to="/login" className={linkClass}>Login</NavLink>
        <NavLink to="/signup" className="nav-link primary">Sign Up</NavLink>
      </nav>
    </header>
  );
}
