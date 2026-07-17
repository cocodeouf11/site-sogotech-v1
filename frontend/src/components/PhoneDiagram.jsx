import { useState } from "react";

const FRONT_ZONES = ["Écran", "Caméra avant", "Haut-parleur", "Bouton power", "Boutons volume"];

export function PhoneDiagram({ marks = [], onAdd, face = "avant" }) {
  const [hover, setHover] = useState(null);

  const handleClick = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    onAdd({ x, y, face });
  };

  const faceMarks = marks.filter((m) => m.face === face);

  return (
    <div
      onClick={handleClick}
      onMouseMove={(e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        setHover({ x: ((e.clientX - rect.left) / rect.width) * 100, y: ((e.clientY - rect.top) / rect.height) * 100 });
      }}
      data-testid={`phone-diagram-${face}`}
      className="relative w-full aspect-[9/18] max-w-[160px] mx-auto cursor-crosshair select-none"
      title="Cliquez pour marquer un défaut"
    >
      <svg viewBox="0 0 100 200" className="w-full h-full">
        <rect x="5" y="5" width="90" height="190" rx="16" className="fill-slate-100 dark:fill-zinc-800 stroke-slate-400 dark:stroke-zinc-600" strokeWidth="2" />
        {face === "avant" && (
          <>
            <rect x="15" y="15" width="70" height="170" rx="6" className="fill-slate-300/60 dark:fill-zinc-700/60" />
            <circle cx="50" cy="10" r="2.5" className="fill-slate-400" />
          </>
        )}
        {face === "arriere" && (
          <circle cx="30" cy="25" r="6" className="fill-slate-400/50 stroke-slate-500" strokeWidth="1" />
        )}
      </svg>
      {faceMarks.map((m, idx) => (
        <span
          key={idx}
          data-testid={`phone-diagram-mark-${face}-${idx}`}
          className="absolute text-red-600 font-bold text-lg -translate-x-1/2 -translate-y-1/2"
          style={{ left: `${m.x}%`, top: `${m.y}%` }}
        >
          ✕
        </span>
      ))}
    </div>
  );
}
