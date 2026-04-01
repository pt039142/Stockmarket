import csv
import json
from dataclasses import dataclass, asdict, fields
from datetime import datetime
from html import escape
from pathlib import Path


@dataclass
class TradeRecord:
    trade_id: int
    symbol: str
    side: str
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    quantity: int
    pnl: float
    reason: str
    regime: str = ''
    confidence: float = 0.0
    stop_loss: float = 0.0
    target: float = 0.0


class TradeJournal:
    """Stores trades, session events, and exports performance reports."""

    def __init__(self):
        self.trades = []
        self.events = []
        self._next_trade_id = 1

    def record_event(self, event_type, message, **payload):
        self.events.append({
            'timestamp': datetime.now().isoformat(timespec='seconds'),
            'event_type': event_type,
            'message': message,
            'payload': payload,
        })

    def record_trade(self, **kwargs):
        record = TradeRecord(
            trade_id=self._next_trade_id,
            symbol=kwargs['symbol'],
            side=kwargs['side'],
            entry_time=self._fmt_time(kwargs['entry_time']),
            exit_time=self._fmt_time(kwargs['exit_time']),
            entry_price=float(kwargs['entry_price']),
            exit_price=float(kwargs['exit_price']),
            quantity=int(kwargs['quantity']),
            pnl=float(kwargs['pnl']),
            reason=kwargs.get('reason', 'EXIT'),
            regime=kwargs.get('regime', ''),
            confidence=float(kwargs.get('confidence', 0.0)),
            stop_loss=float(kwargs.get('stop_loss', 0.0)),
            target=float(kwargs.get('target', 0.0)),
        )
        self._next_trade_id += 1
        self.trades.append(record)
        return record

    def _fmt_time(self, value):
        if value is None:
            return ''
        if isinstance(value, str):
            return value
        if hasattr(value, 'isoformat'):
            return value.isoformat(timespec='seconds')
        return str(value)

    def trade_dicts(self):
        return [asdict(trade) for trade in self.trades]

    def summary(self):
        pnls = [trade.pnl for trade in self.trades]
        total_trades = len(pnls)
        winning = sum(1 for pnl in pnls if pnl > 0)
        losing = sum(1 for pnl in pnls if pnl < 0)
        gross_profit = sum(pnl for pnl in pnls if pnl > 0)
        gross_loss = abs(sum(pnl for pnl in pnls if pnl < 0))
        net_pnl = sum(pnls)
        win_rate = (winning / total_trades * 100) if total_trades else 0.0
        profit_factor = (gross_profit / gross_loss) if gross_loss else (float('inf') if gross_profit > 0 else 0.0)
        equity_curve = self.equity_curve()
        max_drawdown = self._max_drawdown(equity_curve)

        return {
            'total_trades': total_trades,
            'winning_trades': winning,
            'losing_trades': losing,
            'win_rate': round(win_rate, 2),
            'gross_profit': round(gross_profit, 2),
            'gross_loss': round(gross_loss, 2),
            'net_pnl': round(net_pnl, 2),
            'profit_factor': round(profit_factor, 2) if profit_factor not in (float('inf'),) else 'inf',
            'max_drawdown': round(max_drawdown, 2),
            'last_trade_time': self.trades[-1].exit_time if self.trades else '',
        }

    def equity_curve(self):
        equity = []
        running = 0.0
        for trade in self.trades:
            running += trade.pnl
            equity.append(running)
        return equity

    def _max_drawdown(self, equity_curve):
        peak = float('-inf')
        max_dd = 0.0
        for value in equity_curve:
            peak = max(peak, value)
            if peak == float('-inf'):
                peak = value
            drawdown = peak - value
            max_dd = max(max_dd, drawdown)
        return max_dd

    def save_json(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            'generated_at': datetime.now().isoformat(timespec='seconds'),
            'summary': self.summary(),
            'trades': self.trade_dicts(),
            'events': self.events,
        }
        path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
        return path

    def save_csv(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [field.name for field in fields(TradeRecord)]
        with path.open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for trade in self.trades:
                writer.writerow(asdict(trade))
        return path

    def export_html_report(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        summary = self.summary()
        trades = self.trade_dicts()
        equity_curve = self.equity_curve()
        chart = self._svg_chart(equity_curve)

        rows = []
        for trade in trades:
            rows.append(
                '<tr>'
                f'<td>{trade["trade_id"]}</td>'
                f'<td>{escape(str(trade["symbol"]))}</td>'
                f'<td>{escape(str(trade["side"]))}</td>'
                f'<td>{trade["entry_time"]}</td>'
                f'<td>{trade["exit_time"]}</td>'
                f'<td>{trade["entry_price"]:.2f}</td>'
                f'<td>{trade["exit_price"]:.2f}</td>'
                f'<td>{trade["quantity"]}</td>'
                f'<td>{trade["pnl"]:.2f}</td>'
                f'<td>{escape(str(trade["reason"]))}</td>'
                f'</tr>'
            )

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>PrinceStockExhange - Paper Trading Report</title>
<style>
  :root {{
    --bg: #0b1020;
    --panel: #111831;
    --panel-2: #18213d;
    --text: #f4f7fb;
    --muted: #9fb0d0;
    --accent: #6ee7b7;
    --danger: #f87171;
    --warn: #fbbf24;
  }}
  body {{
    margin: 0;
    font-family: Segoe UI, Arial, sans-serif;
    background: radial-gradient(circle at top, #18213d 0%, var(--bg) 55%);
    color: var(--text);
    padding: 24px;
  }}
  .wrap {{ max-width: 1200px; margin: 0 auto; }}
  h1 {{ margin: 0 0 8px; font-size: 32px; }}
  .muted {{ color: var(--muted); }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 20px 0; }}
  .card {{ background: rgba(17, 24, 49, 0.95); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 16px; }}
  .card h3 {{ margin: 0 0 6px; font-size: 12px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }}
  .card .value {{ font-size: 24px; font-weight: 700; }}
  .good {{ color: var(--accent); }}
  .bad {{ color: var(--danger); }}
  .chart {{ background: rgba(17, 24, 49, 0.95); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 16px; margin: 20px 0; }}
  table {{ width: 100%; border-collapse: collapse; background: rgba(17,24,49,0.95); border-radius: 16px; overflow: hidden; }}
  th, td {{ padding: 10px 12px; border-bottom: 1px solid rgba(255,255,255,0.06); text-align: left; font-size: 14px; }}
  th {{ color: var(--muted); font-weight: 600; background: rgba(255,255,255,0.03); }}
  .footer {{ margin-top: 18px; color: var(--muted); font-size: 12px; }}
</style>
</head>
<body>
  <div class="wrap">
    <h1>PrinceStockExhange</h1>
    <div class="muted">Paper Trading Report generated at {escape(datetime.now().isoformat(timespec='seconds'))}</div>
    <div class="grid">
      <div class="card"><h3>Total Trades</h3><div class="value">{summary["total_trades"]}</div></div>
      <div class="card"><h3>Net P&L</h3><div class="value {'good' if summary['net_pnl'] >= 0 else 'bad'}">{summary["net_pnl"]:.2f}</div></div>
      <div class="card"><h3>Win Rate</h3><div class="value">{summary["win_rate"]:.2f}%</div></div>
      <div class="card"><h3>Profit Factor</h3><div class="value">{summary["profit_factor"]}</div></div>
      <div class="card"><h3>Max Drawdown</h3><div class="value bad">{summary["max_drawdown"]:.2f}</div></div>
    </div>
    <div class="chart">
      <h3 style="margin-top:0;">Equity Curve</h3>
      {chart}
    </div>
    <table>
      <thead>
        <tr>
          <th>ID</th><th>Symbol</th><th>Side</th><th>Entry</th><th>Exit</th>
          <th>Entry Price</th><th>Exit Price</th><th>Qty</th><th>P&L</th><th>Reason</th>
        </tr>
      </thead>
      <tbody>
        {''.join(rows) if rows else '<tr><td colspan="10">No trades recorded</td></tr>'}
      </tbody>
    </table>
    <div class="footer">This report is for simulation and validation only. It is not a guarantee of live performance.</div>
  </div>
</body>
</html>
"""
        path.write_text(html, encoding='utf-8')
        return path

    def _svg_chart(self, values, width=1100, height=220):
        if not values:
            return '<div class="muted">No equity points yet.</div>'

        min_v = min(values)
        max_v = max(values)
        span = max(max_v - min_v, 1e-9)
        pad = 20
        points = []
        for idx, value in enumerate(values):
            x = pad + (idx / max(len(values) - 1, 1)) * (width - pad * 2)
            y = pad + (1 - ((value - min_v) / span)) * (height - pad * 2)
            points.append(f"{x:.2f},{y:.2f}")

        baseline_y = pad + (1 - ((0 - min_v) / span)) * (height - pad * 2)
        svg = f"""
<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" role="img" aria-label="Equity curve">
  <rect x="0" y="0" width="{width}" height="{height}" rx="14" fill="#0f172a" />
  <line x1="{pad}" y1="{baseline_y:.2f}" x2="{width - pad}" y2="{baseline_y:.2f}" stroke="#334155" stroke-width="1" stroke-dasharray="4 4" />
  <polyline fill="none" stroke="#6ee7b7" stroke-width="3" stroke-linejoin="round" stroke-linecap="round" points="{' '.join(points)}" />
</svg>
"""
        return svg
