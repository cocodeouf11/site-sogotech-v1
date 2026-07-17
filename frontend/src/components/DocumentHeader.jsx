export function DocumentHeader({ shop, numero }) {
  return (
    <div className="flex items-start justify-between border-b border-slate-300 pb-4 mb-6">
      <div className="flex items-center gap-4">
        {shop?.logo_url ? (
          <img
            src={`${process.env.REACT_APP_BACKEND_URL}${shop.logo_url}`}
            alt="logo"
            className="w-16 h-16 object-contain"
            data-testid="doc-header-logo"
          />
        ) : (
          <div className="w-16 h-16 rounded-md bg-slate-200 flex items-center justify-center text-slate-500 text-xs font-heading">
            LOGO
          </div>
        )}
        <div>
          <p className="font-heading font-semibold text-lg" data-testid="doc-header-shop-name">{shop?.nom || "Boutique"}</p>
          <p className="text-sm text-slate-600">{shop?.adresse}</p>
          <p className="text-sm text-slate-600">Tél: {shop?.telephone}</p>
        </div>
      </div>
      {numero && (
        <div className="text-right">
          <p className="text-xs uppercase tracking-widest text-slate-500">N°</p>
          <p className="font-heading text-xl font-bold" data-testid="doc-header-numero">{numero}</p>
        </div>
      )}
    </div>
  );
}
