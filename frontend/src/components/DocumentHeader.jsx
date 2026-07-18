export function DocumentHeader({ shop, numero }) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-300 pb-4 mb-6">
      <div className="flex items-center gap-4 min-w-0">
        {shop?.logo_url ? (
          <img
            src={`${process.env.REACT_APP_BACKEND_URL}${shop.logo_url}`}
            alt="logo"
            className="w-16 h-16 object-contain shrink-0"
            data-testid="doc-header-logo"
          />
        ) : (
          <div className="w-16 h-16 rounded-md bg-slate-200 flex items-center justify-center text-slate-500 text-xs font-heading shrink-0">
            LOGO
          </div>
        )}
        <div className="min-w-0">
          <p className="font-heading font-semibold text-lg truncate" data-testid="doc-header-shop-name">{shop?.nom || "Boutique"}</p>
          <p className="text-sm text-slate-600 break-words">{shop?.adresse}</p>
          <p className="text-sm text-slate-600">Tél: {shop?.telephone}</p>
          {shop?.siret && <p className="text-sm text-slate-600">SIRET: {shop.siret}</p>}
        </div>
      </div>
      {numero && (
        <div className="text-right shrink-0">
          <p className="text-xs uppercase tracking-widest text-slate-500">N°</p>
          <p className="font-heading text-xl font-bold" data-testid="doc-header-numero">{numero}</p>
        </div>
      )}
    </div>
  );
}
