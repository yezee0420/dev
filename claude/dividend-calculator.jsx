import { useState, useMemo } from "react";

const EXCHANGE_RATE = 1380;

const STOCKS_DATA = [
  // US Stocks
  { ticker: "AAPL", name: "Apple", currency: "USD", price: 178.50, dividendPerShare: 1.00, exDivDate: "2026-05-09", payDate: "2026-05-15", frequency: "분기", market: "US" },
  { ticker: "MSFT", name: "Microsoft", currency: "USD", price: 420.30, dividendPerShare: 3.00, exDivDate: "2026-05-21", payDate: "2026-06-11", frequency: "분기", market: "US" },
  { ticker: "JNJ", name: "Johnson & Johnson", currency: "USD", price: 155.80, dividendPerShare: 4.96, exDivDate: "2026-05-26", payDate: "2026-06-10", frequency: "분기", market: "US" },
  { ticker: "KO", name: "Coca-Cola", currency: "USD", price: 62.40, dividendPerShare: 1.94, exDivDate: "2026-06-14", payDate: "2026-07-01", frequency: "분기", market: "US" },
  { ticker: "PG", name: "Procter & Gamble", currency: "USD", price: 165.20, dividendPerShare: 3.98, exDivDate: "2026-07-23", payDate: "2026-08-15", frequency: "분기", market: "US" },
  { ticker: "T", name: "AT&T", currency: "USD", price: 17.80, dividendPerShare: 1.11, exDivDate: "2026-07-09", payDate: "2026-08-03", frequency: "분기", market: "US" },
  { ticker: "VZ", name: "Verizon", currency: "USD", price: 40.50, dividendPerShare: 2.66, exDivDate: "2026-07-09", payDate: "2026-08-01", frequency: "분기", market: "US" },
  { ticker: "SCHD", name: "Schwab US Div ETF", currency: "USD", price: 79.00, dividendPerShare: 2.68, exDivDate: "2026-06-22", payDate: "2026-06-29", frequency: "분기", market: "US" },
  // High-Yield US Stocks
  { ticker: "MO", name: "Altria Group", currency: "USD", price: 65.74, dividendPerShare: 4.24, exDivDate: "2026-06-24", payDate: "2026-07-10", frequency: "분기", market: "US" },
  { ticker: "O", name: "Realty Income", currency: "USD", price: 62.19, dividendPerShare: 3.24, exDivDate: "2026-04-30", payDate: "2026-05-15", frequency: "월배당", market: "US" },
  { ticker: "MPLX", name: "MPLX LP", currency: "USD", price: 57.39, dividendPerShare: 4.31, exDivDate: "2026-05-07", payDate: "2026-05-15", frequency: "분기", market: "US" },
  // High-Yield US ETFs
  { ticker: "JEPI", name: "JPMorgan Equity Premium", currency: "USD", price: 59.60, dividendPerShare: 4.77, exDivDate: "2026-05-01", payDate: "2026-05-06", frequency: "월배당", market: "US" },
  { ticker: "KNG", name: "Dividend Aristocrats ETF", currency: "USD", price: 48.70, dividendPerShare: 4.22, exDivDate: "2026-04-20", payDate: "2026-04-24", frequency: "월배당", market: "US" },
  { ticker: "DIVO", name: "Amplify Enhanced Div", currency: "USD", price: 45.00, dividendPerShare: 2.91, exDivDate: "2026-04-23", payDate: "2026-04-30", frequency: "월배당", market: "US" },
  { ticker: "SPYD", name: "S&P 500 High Div ETF", currency: "USD", price: 43.84, dividendPerShare: 1.99, exDivDate: "2026-06-19", payDate: "2026-06-25", frequency: "분기", market: "US" },
  // Korean Stocks
  { ticker: "005930", name: "삼성전자", currency: "KRW", price: 72000, dividendPerShare: 1444, exDivDate: "2026-12-29", payDate: "2027-04-20", frequency: "연간", market: "KR" },
  { ticker: "000660", name: "SK하이닉스", currency: "KRW", price: 135000, dividendPerShare: 1200, exDivDate: "2026-12-29", payDate: "2027-04-20", frequency: "연간", market: "KR" },
  { ticker: "035420", name: "NAVER", currency: "KRW", price: 215000, dividendPerShare: 1571, exDivDate: "2026-12-29", payDate: "2027-04-20", frequency: "연간", market: "KR" },
  { ticker: "017670", name: "SK텔레콤", currency: "KRW", price: 53000, dividendPerShare: 3540, exDivDate: "2026-12-29", payDate: "2027-04-20", frequency: "연간", market: "KR" },
  { ticker: "032830", name: "삼성생명", currency: "KRW", price: 78000, dividendPerShare: 3600, exDivDate: "2026-12-29", payDate: "2027-04-20", frequency: "연간", market: "KR" },
  { ticker: "086790", name: "하나금융지주", currency: "KRW", price: 54000, dividendPerShare: 3600, exDivDate: "2026-12-29", payDate: "2027-04-20", frequency: "연간", market: "KR" },
];

function fmt(n, currency) {
  if (currency === "KRW") return n.toLocaleString("ko-KR") + "원";
  return "$" + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtNum(n) {
  return n.toLocaleString("ko-KR", { maximumFractionDigits: 0 });
}

function daysUntil(dateStr) {
  const now = new Date("2026-04-07");
  const target = new Date(dateStr);
  const diff = Math.ceil((target - now) / (1000 * 60 * 60 * 24));
  return diff;
}

function StockTable({ stocks, onSelect, selectedTicker }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b-2 border-gray-700">
            <th className="text-left py-2 px-2 text-gray-400 font-medium">종목</th>
            <th className="text-right py-2 px-2 text-gray-400 font-medium">현재가</th>
            <th className="text-right py-2 px-2 text-gray-400 font-medium">1주 배당금</th>
            <th className="text-right py-2 px-2 text-gray-400 font-medium">배당수익률</th>
            <th className="text-center py-2 px-2 text-gray-400 font-medium">배당락일</th>
            <th className="text-center py-2 px-2 text-gray-400 font-medium">배당일</th>
            <th className="text-center py-2 px-2 text-gray-400 font-medium">주기</th>
          </tr>
        </thead>
        <tbody>
          {stocks.map((s) => {
            const yld = ((s.dividendPerShare / s.price) * 100).toFixed(2);
            const isSelected = s.ticker === selectedTicker;
            return (
              <tr
                key={s.ticker}
                onClick={() => onSelect(s.ticker)}
                className={`border-b border-gray-800 cursor-pointer transition-colors ${isSelected ? "bg-blue-900 bg-opacity-40" : "hover:bg-gray-800"}`}
              >
                <td className="py-2.5 px-2">
                  <div className="flex items-center gap-2">
                    <span className={`inline-block w-2 h-2 rounded-full ${s.market === "US" ? "bg-blue-400" : "bg-red-400"}`}></span>
                    <div>
                      <span className="font-semibold text-white">{s.ticker}</span>
                      <span className="text-gray-500 ml-1.5 text-xs">{s.name}</span>
                    </div>
                  </div>
                </td>
                <td className="text-right py-2.5 px-2 text-gray-200 font-mono">{fmt(s.price, s.currency)}</td>
                <td className="text-right py-2.5 px-2 text-green-400 font-mono">{fmt(s.dividendPerShare, s.currency)}</td>
                <td className="text-right py-2.5 px-2 font-mono">
                  <span className="bg-green-900 bg-opacity-50 text-green-300 px-1.5 py-0.5 rounded text-xs">{yld}%</span>
                </td>
                <td className="text-center py-2.5 px-2 text-gray-300 text-xs">{s.exDivDate}</td>
                <td className="text-center py-2.5 px-2 text-gray-300 text-xs">{s.payDate}</td>
                <td className="text-center py-2.5 px-2">
                  <span className="text-xs bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded">{s.frequency}</span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function ScenarioBar({ pct, maxPct, dividendYield, label }) {
  const width = Math.min((Math.abs(pct) / maxPct) * 100, 100);
  const isDefended = Math.abs(pct) <= dividendYield;
  return (
    <div className="flex items-center gap-3 py-1">
      <span className="text-xs text-gray-400 w-12 text-right font-mono">{label}</span>
      <div className="flex-1 h-5 bg-gray-800 rounded-full overflow-hidden relative">
        <div
          className={`h-full rounded-full transition-all ${isDefended ? "bg-green-500" : "bg-red-500"}`}
          style={{ width: `${width}%`, opacity: isDefended ? 0.7 : 0.5 }}
        ></div>
        {dividendYield > 0 && (
          <div
            className="absolute top-0 h-full w-0.5 bg-yellow-400"
            style={{ left: `${Math.min((dividendYield / maxPct) * 100, 100)}%` }}
          ></div>
        )}
      </div>
      <span className={`text-xs font-mono w-20 text-right ${isDefended ? "text-green-400" : "text-red-400"}`}>
        {isDefended ? "방어 가능" : "손실 구간"}
      </span>
    </div>
  );
}

export default function DividendCalculator() {
  const [selectedTicker, setSelectedTicker] = useState(null);
  const [investAmount, setInvestAmount] = useState("");
  const [investDate, setInvestDate] = useState("2026-04-07");
  const [displayCurrency, setDisplayCurrency] = useState("KRW");
  const [marketFilter, setMarketFilter] = useState("ALL");
  const [customStocks, setCustomStocks] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newStock, setNewStock] = useState({ ticker: "", name: "", currency: "USD", price: "", dividendPerShare: "", exDivDate: "", payDate: "", frequency: "분기", market: "US" });

  const allStocks = [...STOCKS_DATA, ...customStocks];
  const filteredStocks = marketFilter === "ALL" ? allStocks : allStocks.filter(s => s.market === marketFilter);
  const stock = allStocks.find((s) => s.ticker === selectedTicker);

  const amount = parseFloat(investAmount) || 0;

  const calc = useMemo(() => {
    if (!stock || amount <= 0) return null;

    let investInStockCurrency = amount;
    if (displayCurrency === "KRW" && stock.currency === "USD") {
      investInStockCurrency = amount / EXCHANGE_RATE;
    } else if (displayCurrency === "USD" && stock.currency === "KRW") {
      investInStockCurrency = amount * EXCHANGE_RATE;
    }

    const shares = Math.floor(investInStockCurrency / stock.price);
    if (shares <= 0) return null;

    const totalCost = shares * stock.price;
    const annualDividend = shares * stock.dividendPerShare;
    const dividendYield = (stock.dividendPerShare / stock.price) * 100;

    const daysToExDiv = daysUntil(stock.exDivDate);
    const daysToPayDate = daysUntil(stock.payDate);

    const toDisplay = (val) => {
      if (displayCurrency === stock.currency) return val;
      if (displayCurrency === "KRW" && stock.currency === "USD") return val * EXCHANGE_RATE;
      if (displayCurrency === "USD" && stock.currency === "KRW") return val / EXCHANGE_RATE;
      return val;
    };

    const bepPrice = stock.price - stock.dividendPerShare;
    const bepDropPct = (stock.dividendPerShare / stock.price) * 100;

    const scenarios = [-1, -2, -3, -5, -7, -10, -15, -20].map((pct) => {
      const newPrice = stock.price * (1 + pct / 100);
      const priceLoss = (stock.price - newPrice) * shares;
      const netPnL = annualDividend - priceLoss;
      return {
        pct,
        newPrice,
        priceLoss,
        netPnL,
        defended: netPnL >= 0,
      };
    });

    return {
      shares,
      totalCost,
      annualDividend,
      dividendYield,
      daysToExDiv,
      daysToPayDate,
      bepPrice,
      bepDropPct,
      scenarios,
      toDisplay,
      remainingCash: investInStockCurrency - totalCost,
    };
  }, [stock, amount, displayCurrency]);

  const addCustomStock = () => {
    if (newStock.ticker && newStock.price && newStock.dividendPerShare) {
      setCustomStocks([...customStocks, {
        ...newStock,
        price: parseFloat(newStock.price),
        dividendPerShare: parseFloat(newStock.dividendPerShare),
      }]);
      setNewStock({ ticker: "", name: "", currency: "USD", price: "", dividendPerShare: "", exDivDate: "", payDate: "", frequency: "분기", market: "US" });
      setShowAddForm(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-4" style={{ fontFamily: "'Inter', 'Pretendard', -apple-system, sans-serif" }}>
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <span className="text-green-400">$</span> 배당금 지급 계산기
          </h1>
          <p className="text-gray-500 text-sm mt-1">투자금액 기반 배당 수익 및 주가 하락 방어 시나리오 분석</p>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap gap-3 mb-4">
          <div className="flex bg-gray-900 rounded-lg overflow-hidden border border-gray-800">
            {["ALL", "US", "KR"].map((m) => (
              <button
                key={m}
                onClick={() => setMarketFilter(m)}
                className={`px-3 py-1.5 text-xs font-medium transition-colors ${marketFilter === m ? "bg-gray-700 text-white" : "text-gray-500 hover:text-gray-300"}`}
              >
                {m === "ALL" ? "전체" : m === "US" ? "미국" : "한국"}
              </button>
            ))}
          </div>

          <div className="flex bg-gray-900 rounded-lg overflow-hidden border border-gray-800">
            {["KRW", "USD"].map((c) => (
              <button
                key={c}
                onClick={() => setDisplayCurrency(c)}
                className={`px-3 py-1.5 text-xs font-medium transition-colors ${displayCurrency === c ? "bg-blue-600 text-white" : "text-gray-500 hover:text-gray-300"}`}
              >
                {c === "KRW" ? "원화 (KRW)" : "달러 (USD)"}
              </button>
            ))}
          </div>

          <span className="text-xs text-gray-600 flex items-center">기준환율: 1 USD = {EXCHANGE_RATE.toLocaleString()}원</span>

          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="ml-auto px-3 py-1.5 text-xs font-medium bg-gray-800 border border-gray-700 rounded-lg text-gray-400 hover:text-white hover:border-gray-600 transition-colors"
          >
            + 종목 추가
          </button>
        </div>

        {/* Add Stock Form */}
        {showAddForm && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-4">
            <h3 className="text-sm font-semibold text-gray-300 mb-3">종목 직접 추가</h3>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <input placeholder="티커 (예: AAPL)" value={newStock.ticker} onChange={e => setNewStock({...newStock, ticker: e.target.value.toUpperCase()})} className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-white placeholder-gray-600" />
              <input placeholder="종목명" value={newStock.name} onChange={e => setNewStock({...newStock, name: e.target.value})} className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-white placeholder-gray-600" />
              <input type="number" placeholder="현재가" value={newStock.price} onChange={e => setNewStock({...newStock, price: e.target.value})} className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-white placeholder-gray-600" />
              <input type="number" placeholder="1주 배당금" value={newStock.dividendPerShare} onChange={e => setNewStock({...newStock, dividendPerShare: e.target.value})} className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-white placeholder-gray-600" />
              <input type="date" placeholder="배당락일" value={newStock.exDivDate} onChange={e => setNewStock({...newStock, exDivDate: e.target.value})} className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-white placeholder-gray-600" />
              <input type="date" placeholder="배당일" value={newStock.payDate} onChange={e => setNewStock({...newStock, payDate: e.target.value})} className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-white placeholder-gray-600" />
              <select value={newStock.currency} onChange={e => setNewStock({...newStock, currency: e.target.value, market: e.target.value === "USD" ? "US" : "KR"})} className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-white">
                <option value="USD">USD</option>
                <option value="KRW">KRW</option>
              </select>
              <button onClick={addCustomStock} className="bg-blue-600 hover:bg-blue-500 text-white rounded px-3 py-1.5 text-sm font-medium transition-colors">추가</button>
            </div>
          </div>
        )}

        {/* Stock Table */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-4">
          <StockTable stocks={filteredStocks} onSelect={setSelectedTicker} selectedTicker={selectedTicker} />
        </div>

        {/* Investment Input */}
        {stock && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-4">
            <div className="flex items-center gap-2 mb-3">
              <span className={`inline-block w-3 h-3 rounded-full ${stock.market === "US" ? "bg-blue-400" : "bg-red-400"}`}></span>
              <h2 className="text-lg font-bold text-white">{stock.ticker}</h2>
              <span className="text-gray-500 text-sm">{stock.name}</span>
              <span className="ml-auto text-xs bg-green-900 bg-opacity-50 text-green-300 px-2 py-0.5 rounded">
                배당수익률 {((stock.dividendPerShare / stock.price) * 100).toFixed(2)}%
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="text-xs text-gray-500 block mb-1">투자일</label>
                <input
                  type="date"
                  value={investDate}
                  onChange={(e) => setInvestDate(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white"
                />
              </div>
              <div className="sm:col-span-2">
                <label className="text-xs text-gray-500 block mb-1">
                  투자금액 ({displayCurrency === "KRW" ? "원" : "달러"})
                </label>
                <input
                  type="text"
                  value={investAmount}
                  onChange={(e) => setInvestAmount(e.target.value.replace(/[^0-9.]/g, ""))}
                  placeholder={displayCurrency === "KRW" ? "예: 10000000" : "예: 10000"}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white font-mono placeholder-gray-600"
                />
              </div>
            </div>

            {/* Quick Amount Buttons */}
            <div className="flex flex-wrap gap-2 mt-3">
              {(displayCurrency === "KRW"
                ? [1000000, 5000000, 10000000, 50000000, 100000000]
                : [1000, 5000, 10000, 50000, 100000]
              ).map((v) => (
                <button
                  key={v}
                  onClick={() => setInvestAmount(String(v))}
                  className="px-2.5 py-1 text-xs bg-gray-800 border border-gray-700 rounded-lg text-gray-400 hover:text-white hover:border-gray-500 transition-colors font-mono"
                >
                  {displayCurrency === "KRW" ? (v >= 100000000 ? `${v / 100000000}억` : `${v / 10000}만`) : `$${v.toLocaleString()}`}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Results */}
        {calc && stock && (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <div className="text-xs text-gray-500 mb-1">매수 가능 주수</div>
                <div className="text-xl font-bold text-white font-mono">{calc.shares.toLocaleString()}주</div>
                <div className="text-xs text-gray-600 mt-1">잔여: {fmt(calc.toDisplay(calc.remainingCash), displayCurrency)}</div>
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <div className="text-xs text-gray-500 mb-1">총 투자금액</div>
                <div className="text-xl font-bold text-white font-mono">{fmt(calc.toDisplay(calc.totalCost), displayCurrency)}</div>
                <div className="text-xs text-gray-600 mt-1">@ {fmt(stock.price, stock.currency)}/주</div>
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <div className="text-xs text-gray-500 mb-1">연간 배당금 (세전)</div>
                <div className="text-xl font-bold text-green-400 font-mono">{fmt(calc.toDisplay(calc.annualDividend), displayCurrency)}</div>
                <div className="text-xs text-gray-600 mt-1">{fmt(stock.dividendPerShare, stock.currency)} x {calc.shares}주</div>
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <div className="text-xs text-gray-500 mb-1">다음 배당일까지</div>
                <div className="text-xl font-bold text-blue-400 font-mono">D{calc.daysToPayDate > 0 ? `-${calc.daysToPayDate}` : `+${Math.abs(calc.daysToPayDate)}`}</div>
                <div className="text-xs text-gray-600 mt-1">배당락 D{calc.daysToExDiv > 0 ? `-${calc.daysToExDiv}` : `+${Math.abs(calc.daysToExDiv)}`}</div>
              </div>
            </div>

            {/* Timeline */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-4">
              <h3 className="text-sm font-semibold text-gray-300 mb-3">배당 타임라인</h3>
              <div className="relative">
                <div className="absolute left-4 top-0 bottom-0 w-px bg-gray-800"></div>
                {[
                  { date: investDate, label: "투자일", desc: `${fmt(calc.toDisplay(calc.totalCost), displayCurrency)} 투자 (${calc.shares}주)`, color: "bg-blue-500" },
                  { date: stock.exDivDate, label: "배당락일", desc: "이 날 이전에 보유해야 배당 수령 가능", color: "bg-yellow-500" },
                  { date: stock.payDate, label: "배당 지급일", desc: `${fmt(calc.toDisplay(calc.annualDividend), displayCurrency)} 수령 예정 (세전)`, color: "bg-green-500" },
                ].map((item, i) => (
                  <div key={i} className="relative pl-10 pb-4">
                    <div className={`absolute left-2.5 w-3 h-3 rounded-full ${item.color} border-2 border-gray-900`}></div>
                    <div className="text-xs text-gray-500">{item.date}</div>
                    <div className="text-sm font-medium text-white">{item.label}</div>
                    <div className="text-xs text-gray-500">{item.desc}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* BEP & Scenario Analysis */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-4">
              <h3 className="text-sm font-semibold text-gray-300 mb-1">주가 하락 방어 분석 (BEP)</h3>
              <p className="text-xs text-gray-600 mb-4">배당금으로 주가 하락을 얼마나 방어할 수 있는지 시뮬레이션</p>

              {/* BEP Info */}
              <div className="bg-gray-800 rounded-lg p-3 mb-4 flex flex-wrap gap-4">
                <div>
                  <div className="text-xs text-gray-500">손익분기 주가 (BEP)</div>
                  <div className="text-lg font-bold text-yellow-400 font-mono">{fmt(calc.bepPrice, stock.currency)}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">방어 가능 하락폭</div>
                  <div className="text-lg font-bold text-yellow-400 font-mono">-{calc.bepDropPct.toFixed(2)}%</div>
                </div>
                <div className="flex-1 flex items-center">
                  <p className="text-xs text-gray-500">
                    현재가 {fmt(stock.price, stock.currency)}에서 {fmt(calc.bepPrice, stock.currency)}까지({calc.bepDropPct.toFixed(2)}%) 하락해도
                    배당금으로 손실 완전 방어 가능
                  </p>
                </div>
              </div>

              {/* Scenario Bars */}
              <div className="space-y-1">
                {calc.scenarios.map((sc) => (
                  <ScenarioBar
                    key={sc.pct}
                    pct={sc.pct}
                    maxPct={20}
                    dividendYield={calc.bepDropPct}
                    label={`${sc.pct}%`}
                  />
                ))}
              </div>

              <div className="flex items-center gap-4 mt-3 text-xs text-gray-600">
                <span className="flex items-center gap-1"><span className="w-3 h-1.5 bg-green-500 rounded opacity-70"></span> 배당금으로 방어 가능</span>
                <span className="flex items-center gap-1"><span className="w-3 h-1.5 bg-red-500 rounded opacity-50"></span> 실질 손실 구간</span>
                <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-yellow-400"></span> BEP 라인</span>
              </div>

              {/* Detail Table */}
              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-gray-800">
                      <th className="text-left py-1.5 px-2 text-gray-500">하락률</th>
                      <th className="text-right py-1.5 px-2 text-gray-500">예상 주가</th>
                      <th className="text-right py-1.5 px-2 text-gray-500">주가 손실</th>
                      <th className="text-right py-1.5 px-2 text-gray-500">배당금</th>
                      <th className="text-right py-1.5 px-2 text-gray-500">순손익</th>
                      <th className="text-center py-1.5 px-2 text-gray-500">판정</th>
                    </tr>
                  </thead>
                  <tbody>
                    {calc.scenarios.map((sc) => (
                      <tr key={sc.pct} className="border-b border-gray-800">
                        <td className="py-1.5 px-2 text-gray-300 font-mono">{sc.pct}%</td>
                        <td className="text-right py-1.5 px-2 text-gray-300 font-mono">{fmt(sc.newPrice, stock.currency)}</td>
                        <td className="text-right py-1.5 px-2 text-red-400 font-mono">-{fmt(calc.toDisplay(sc.priceLoss), displayCurrency)}</td>
                        <td className="text-right py-1.5 px-2 text-green-400 font-mono">+{fmt(calc.toDisplay(calc.annualDividend), displayCurrency)}</td>
                        <td className={`text-right py-1.5 px-2 font-mono font-semibold ${sc.netPnL >= 0 ? "text-green-400" : "text-red-400"}`}>
                          {sc.netPnL >= 0 ? "+" : ""}{fmt(calc.toDisplay(sc.netPnL), displayCurrency)}
                        </td>
                        <td className="text-center py-1.5 px-2">
                          <span className={`px-1.5 py-0.5 rounded text-xs ${sc.defended ? "bg-green-900 bg-opacity-50 text-green-300" : "bg-red-900 bg-opacity-50 text-red-300"}`}>
                            {sc.defended ? "방어" : "손실"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Tax Note */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-3 text-xs text-gray-600">
              <span className="text-yellow-500 font-semibold">참고</span> &middot;
              미국 주식 배당소득세 15% (원천징수), 한국 주식 배당소득세 15.4% 별도 &middot;
              위 금액은 세전 기준이며 실제 수령액은 다를 수 있음 &middot;
              주가, 배당금, 환율은 예시 데이터이며 실제와 다를 수 있음 &middot;
              기준환율: 1 USD = {EXCHANGE_RATE.toLocaleString()}원
            </div>
          </>
        )}

        {!stock && (
          <div className="text-center py-16 text-gray-700">
            <div className="text-4xl mb-3">$</div>
            <p className="text-sm">위 테이블에서 종목을 선택하고 투자금액을 입력하세요</p>
          </div>
        )}
      </div>
    </div>
  );
}
