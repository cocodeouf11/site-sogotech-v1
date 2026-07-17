import { useRef, useState, useEffect, useImperativeHandle, forwardRef } from "react";
import { Button } from "./ui/button";
import { Eraser } from "lucide-react";

export const SignaturePad = forwardRef(function SignaturePad({ testId = "signature-pad" }, ref) {
  const canvasRef = useRef(null);
  const drawing = useRef(false);
  const [empty, setEmpty] = useState(true);

  useEffect(() => {
    const canvas = canvasRef.current;
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);
    ctx.lineWidth = 2.2;
    ctx.lineCap = "round";
    ctx.strokeStyle = "#111827";
  }, []);

  const getPos = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const point = e.touches ? e.touches[0] : e;
    return { x: point.clientX - rect.left, y: point.clientY - rect.top };
  };

  const start = (e) => {
    e.preventDefault();
    drawing.current = true;
    const ctx = canvasRef.current.getContext("2d");
    const { x, y } = getPos(e);
    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const move = (e) => {
    if (!drawing.current) return;
    e.preventDefault();
    const ctx = canvasRef.current.getContext("2d");
    const { x, y } = getPos(e);
    ctx.lineTo(x, y);
    ctx.stroke();
    setEmpty(false);
  };

  const end = () => {
    drawing.current = false;
  };

  const clear = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setEmpty(true);
  };

  useImperativeHandle(ref, () => ({
    isEmpty: () => empty,
    clear,
    toDataURL: () => (empty ? "" : canvasRef.current.toDataURL("image/png")),
  }));

  return (
    <div className="relative">
      <canvas
        ref={canvasRef}
        data-testid={testId}
        className="w-full h-36 bg-slate-50 dark:bg-zinc-800 border-2 border-dashed border-border rounded-lg touch-none cursor-crosshair"
        onMouseDown={start}
        onMouseMove={move}
        onMouseUp={end}
        onMouseLeave={end}
        onTouchStart={start}
        onTouchMove={move}
        onTouchEnd={end}
      />
      <Button
        type="button"
        size="sm"
        variant="outline"
        data-testid={`${testId}-clear-button`}
        onClick={clear}
        className="absolute top-2 right-2 gap-1"
      >
        <Eraser className="w-3.5 h-3.5" /> Effacer
      </Button>
    </div>
  );
});
