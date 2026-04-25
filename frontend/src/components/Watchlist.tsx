/**Watchlist sidebar component.*/
import { useState } from "react";
import { useGlobalStore } from "../store/useGlobalStore";

interface WatchlistProps {
  onSelectSymbol: (symbol: string) => void;
  selectedSymbol: string;
}

export default function Watchlist({ onSelectSymbol, selectedSymbol }: WatchlistProps) {
  const watchlist = useGlobalStore((s) => s.watchlist);
  const [filter, setFilter] = useState("");

  const filteredSymbols = watchlist.filter((s) =>
    s.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <aside
      className="w-64 bg-white border-r border-gray-200 flex flex-col"
      aria-label="Watchlist sidebar"
    >
      <div className="p-4 border-b border-gray-200">
        <h2 className="font-semibold text-gray-900 mb-3">Watchlist</h2>
        <input
          type="text"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filter symbols..."
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Filter watchlist symbols"
        />
      </div>

      <ul className="flex-1 overflow-y-auto" role="listbox" aria-label="Watchlist symbols">
        {filteredSymbols.map((symbol) => (
          <li key={symbol}>
            <button
              onClick={() => onSelectSymbol(symbol)}
              className={`w-full text-left px-4 py-3 text-sm font-mono transition-colors ${
                selectedSymbol === symbol
                  ? "bg-blue-50 text-blue-700 border-r-2 border-blue-500"
                  : "text-gray-700 hover:bg-gray-50"
              }`}
              role="option"
              aria-selected={selectedSymbol === symbol}
              aria-label={`Select ${symbol}`}
            >
              {symbol}
            </button>
          </li>
        ))}

        {filteredSymbols.length === 0 && (
          <li className="px-4 py-8 text-center text-gray-400 text-sm">
            {filter ? "No matching symbols" : "Watchlist empty"}
          </li>
        )}
      </ul>
    </aside>
  );
}
