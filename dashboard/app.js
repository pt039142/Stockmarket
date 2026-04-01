const reportPath = '../reports/paper_trading/paper_trading_report.json';

const dom = {
  connectionDot: document.getElementById('connectionDot'),
  connectionLabel: document.getElementById('connectionLabel'),
  modeChip: document.getElementById('modeChip'),
  refreshChip: document.getElementById('refreshChip'),
  lastSeenChip: document.getElementById('lastSeenChip'),
  profitTarget: document.getElementById('profitTarget'),
  lossCap: document.getElementById('lossCap'),
  sessionMode: document.getElementById('sessionMode'),
  totalTrades: document.getElementById('totalTrades'),
  totalTradesHint: document.getElementById('totalTradesHint'),
  winRate: document.getElementById('winRate'),
  netPnl: document.getElementById('netPnl'),
  netPnlHint: document.getElementById('netPnlHint'),
  drawdown: document.getElementById('drawdown'),
  chartWrap: document.getElementById('chartWrap'),
  summaryList: document.getElementById('summaryList'),
  tradeTableBody: document.getElementById('tradeTableBody'),
  eventsList: document.getElementById('eventsList'),
  reportStamp: document.getElementById('reportStamp'),
  regimePill: document.getElementById('regimePill'),
  quickNote: document.getElementById('quickNote'),
  chartCaption: document.getElementById('chartCaption'),
  miniGrid: document.getElementById('miniGrid'),
  pulseBadge: document.getElementById('pulseBadge'),
  pulseHeadline: document.getElementById('pulseHeadline'),
  pulseSummary: document.getElementById('pulseSummary'),
  pulseStats: document.getElementById('pulseStats'),
  refreshBtn: document.getElementById('refreshBtn'),
  demoBtn: document.getElementById('demoBtn'),
  openJsonBtn: document.getElementById('openJsonBtn'),
};

function formatCurrency(value) {
  const amount = Number(value || 0);
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
  }).format(amount);
}

function makeFallbackReport() {
  return {
    generated_at: new Date().toISOString(),
    summary: {
      total_trades: 3,
      winning_trades: 2,
      losing_trades: 1,
      win_rate: 66.67,
      gross_profit: 1750,
      gross_loss: 420,
      net_pnl: 1330,
      profit_factor: 4.17,
      max_drawdown: 210,
      last_trade_time: new Date().toISOString(),
    },
    trades: [
      {
        trade_id: 1,
        symbol: 'BANKNIFTY',
        side: 'BUY',
        entry_time: '2026-04-01T09:35:00',
        exit_time: '2026-04-01T10:10:00',
        entry_price: 50012.0,
        exit_price: 50205.0,
        quantity: 1,
        pnl: 193.0,
        reason: 'TARGET',
        confidence: 0.91,
      },
      {
        trade_id: 2,
        symbol: 'BANKNIFTY',
        side: 'SELL',
        entry_time: '2026-04-01T11:05:00',
        exit_time: '2026-04-01T11:40:00',
        entry_price: 50310.0,
        exit_price: 50080.0,
        quantity: 1,
        pnl: 230.0,
        reason: 'TARGET',
        confidence: 0.88,
      },
      {
        trade_id: 3,
        symbol: 'NIFTY',
        side: 'BUY',
        entry_time: '2026-04-01T13:20:00',
        exit_time: '2026-04-01T13:55:00',
        entry_price: 24210.0,
        exit_price: 23790.0,
        quantity: 1,
        pnl: -420.0,
        reason: 'STOP_LOSS',
        confidence: 0.76,
      },
    ],
    events: [
      {
        timestamp: '2026-04-01T09:15:00',
        event_type: 'session_start',
        message: 'Session started',
      },
      {
        timestamp: '2026-04-01T09:35:00',
        event_type: 'entry',
        message: 'Paper trade opened',
      },
      {
        timestamp: '2026-04-01T13:55:00',
        event_type: 'exit',
        message: 'Paper trade closed: STOP_LOSS',
      },
    ],
    session_summaries: [
      {
        session_date: '2026-04-01',
        daily_pnl: 1330,
        current_capital: 101330,
        profit_target_reached: false,
        loss_limit_hit: false,
      },
    ],
  };
}

function drawCurve(values) {
  if (!values || !values.length) {
    return '<div class="empty-state">No equity curve available.</div>';
  }

  const width = 900;
  const height = 240;
  const padding = 24;
  const min = Math.min(...values, 0);
  const max = Math.max(...values, 0);
  const span = Math.max(max - min, 1);
  const points = values
    .map((value, idx) => {
      const x = padding + ((width - padding * 2) * idx) / Math.max(values.length - 1, 1);
      const y = padding + (1 - (value - min) / span) * (height - padding * 2);
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(' ');

  const zeroY = padding + (1 - (0 - min) / span) * (height - padding * 2);

  return `
    <svg viewBox="0 0 ${width} ${height}" width="100%" height="${height}" role="img" aria-label="Equity curve">
      <rect x="0" y="0" width="${width}" height="${height}" rx="18" fill="#091525" />
      <line x1="${padding}" y1="${zeroY}" x2="${width - padding}" y2="${zeroY}" stroke="#243449" stroke-width="1.2" stroke-dasharray="5 5" />
      <polyline points="${points}" fill="none" stroke="#6ee7c8" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round" />
    </svg>
  `;
}

function renderSummary(summary, report) {
  dom.profitTarget.textContent = formatCurrency(1500);
  dom.lossCap.textContent = formatCurrency(500);
  dom.totalTrades.textContent = summary.total_trades ?? 0;
  dom.winRate.textContent = `${Number(summary.win_rate || 0).toFixed(2)}%`;
  dom.netPnl.textContent = formatCurrency(summary.net_pnl || 0);
  dom.drawdown.textContent = formatCurrency(summary.max_drawdown || 0);
  dom.totalTradesHint.textContent = `${summary.winning_trades || 0} wins and ${summary.losing_trades || 0} losses in the journal.`;
  dom.netPnlHint.textContent = summary.net_pnl >= 0 ? 'Trading day stayed positive.' : 'Review losses and reduce exposure.';
  dom.reportStamp.textContent = report.generated_at ? `Updated ${new Date(report.generated_at).toLocaleString()}` : 'Live report loaded';
  dom.lastSeenChip.textContent = report.generated_at ? `Last refresh ${new Date(report.generated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : 'No refresh time';
  dom.regimePill.textContent = report.session_summaries?.[0]
    ? `Session ${report.session_summaries[0].profit_target_reached ? 'hit target' : report.session_summaries[0].loss_limit_hit ? 'hit loss cap' : 'running'}`
    : 'No session summary';
  dom.modeChip.textContent = report.trades && report.trades.length ? 'Paper report' : 'Demo fallback';

  const latestSession = report.session_summaries?.[0] || {};
  dom.summaryList.innerHTML = [
    {
      label: 'Gross Profit',
      value: formatCurrency(summary.gross_profit || 0),
      tone: 'good',
    },
    {
      label: 'Gross Loss',
      value: formatCurrency(summary.gross_loss || 0),
      tone: 'bad',
    },
    {
      label: 'Profit Factor',
      value: summary.profit_factor ?? '0',
      tone: summary.profit_factor >= 1 ? 'good' : 'bad',
    },
    {
      label: 'Session P&L',
      value: formatCurrency(latestSession.daily_pnl || summary.net_pnl || 0),
      tone: (latestSession.daily_pnl || summary.net_pnl || 0) >= 0 ? 'good' : 'bad',
    },
    {
      label: 'Capital',
      value: formatCurrency(latestSession.current_capital || 100000),
      tone: 'neutral',
    },
    {
      label: 'Last Trade',
      value: summary.last_trade_time ? new Date(summary.last_trade_time).toLocaleString() : 'N/A',
      tone: 'neutral',
    },
  ]
    .map(
      (item) => `
        <div class="summary-item ${item.tone}">
          <div class="label">${item.label}</div>
          <div class="value">${item.value}</div>
        </div>
      `
    )
    .join('');

  const equity = report.trades ? report.trades.reduce((curve, trade) => {
    const next = (curve.length ? curve[curve.length - 1] : 0) + Number(trade.pnl || 0);
    curve.push(next);
    return curve;
  }, []) : [];
  dom.chartWrap.innerHTML = drawCurve(equity);
  dom.chartCaption.textContent = report.trades && report.trades.length
    ? 'Equity curve based on closed trades from the latest report.'
    : 'No closed trades yet, so the demo curve is shown to keep the layout informative.';

  const miniData = [
    ['Profit Target', formatCurrency(1500)],
    ['Loss Cap', formatCurrency(500)],
    ['Open Positions', String(report.session_summaries?.[0]?.open_positions ?? 0)],
    ['Report Mode', report.trades && report.trades.length ? 'Paper' : 'Demo'],
  ];
  dom.miniGrid.innerHTML = miniData
    .map(([label, value]) => `
      <div class="mini-card">
        <div class="label">${label}</div>
        <div class="value">${value}</div>
      </div>
    `)
    .join('');
}

function renderMarketPulse(report, summary) {
  const trades = report.trades || [];
  const winRate = Number(summary.win_rate || 0);
  const netPnl = Number(summary.net_pnl || 0);
  const drawdown = Number(summary.max_drawdown || 0);
  const targetHit = Boolean(report.session_summaries?.[0]?.profit_target_reached);
  const lossHit = Boolean(report.session_summaries?.[0]?.loss_limit_hit);
  const avgConfidence = trades.length
    ? trades.reduce((total, trade) => total + Number(trade.confidence || 0), 0) / trades.length
    : 0;
  const pulseScore = Math.max(0, Math.min(100, Math.round(
    (winRate * 0.45)
    + (netPnl > 0 ? 18 : -12)
    + (avgConfidence * 35)
    + (drawdown < 250 ? 12 : -8)
  )));

  let badge = 'Watching';
  let headline = 'Session is idle';
  let summaryText = 'The dashboard is waiting for a fresh report. Once trades arrive, the pulse will shift to bias, risk, and confidence.';
  let accent = 'neutral';

  if (lossHit) {
    badge = 'Protective stop';
    headline = 'Risk limit already hit';
    summaryText = 'The session has hit its loss guardrail. The safest next step is to stand down and review execution.';
    accent = 'bad';
  } else if (targetHit) {
    badge = 'Target reached';
    headline = 'Daily goal has been achieved';
    summaryText = 'The strategy reached the day target. Best practice is to stop trading and preserve the session result.';
    accent = 'good';
  } else if (trades.length) {
    badge = netPnl >= 0 ? 'Positive bias' : 'Defensive mode';
    headline = netPnl >= 0 ? 'Market structure looks constructive' : 'Market structure is choppy';
    summaryText = netPnl >= 0
      ? 'Current results lean positive, with the system trading from strength instead of forcing entries.'
      : 'The system is being selective and the session is not giving clean follow-through yet.';
    accent = netPnl >= 0 ? 'good' : 'warning';
  }

  dom.pulseBadge.textContent = badge;
  dom.pulseHeadline.textContent = headline;
  dom.pulseSummary.textContent = summaryText;
  dom.pulseBadge.className = `rail-badge ${accent}`;

  const items = [
    { label: 'Pulse Score', value: `${pulseScore}/100`, tone: pulseScore >= 70 ? 'good' : pulseScore >= 45 ? 'warning' : 'bad' },
    { label: 'Bias', value: netPnl >= 0 ? 'Bullish' : 'Defensive', tone: netPnl >= 0 ? 'good' : 'warning' },
    { label: 'Confidence', value: `${Math.round(avgConfidence * 100)}%`, tone: avgConfidence >= 0.8 ? 'good' : 'neutral' },
    { label: 'Risk State', value: drawdown > 300 ? 'Tighten Up' : 'Controlled', tone: drawdown > 300 ? 'warning' : 'good' },
  ];

  dom.pulseStats.innerHTML = items
    .map((item) => `
      <div class="pulse-stat ${item.tone}">
        <span>${item.label}</span>
        <strong>${item.value}</strong>
      </div>
    `)
    .join('');
}

function renderTrades(trades) {
  if (!trades || !trades.length) {
    dom.tradeTableBody.innerHTML = '<tr><td colspan="8" class="muted-cell">No trades recorded yet.</td></tr>';
    return;
  }

  dom.tradeTableBody.innerHTML = trades
    .map((trade) => {
      const sideClass = trade.side === 'BUY' ? 'side-buy' : 'side-sell';
      const pnlClass = Number(trade.pnl || 0) >= 0 ? 'good' : 'bad';
      return `
        <tr>
          <td>${trade.trade_id}</td>
          <td>${trade.symbol}</td>
          <td class="${sideClass}">${trade.side}</td>
          <td>${formatCurrency(trade.entry_price)}</td>
          <td>${formatCurrency(trade.exit_price)}</td>
          <td class="${pnlClass}">${formatCurrency(trade.pnl)}</td>
          <td>${trade.reason || 'EXIT'}</td>
          <td>${Number(trade.confidence || 0).toFixed(2)}</td>
        </tr>
      `;
    })
    .join('');
}

function renderEvents(events) {
  if (!events || !events.length) {
    dom.eventsList.innerHTML = '<div class="empty-state">No events recorded yet.</div>';
    return;
  }

  dom.eventsList.innerHTML = events
    .slice()
    .reverse()
    .map((event) => `
      <article class="timeline-item">
        <div class="timeline-time">${new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
        <div>
          <div class="timeline-title">${event.event_type}</div>
          <div class="timeline-desc">${event.message}</div>
        </div>
      </article>
    `)
    .join('');
}

async function loadReport(useDemo = false, silent = false) {
  try {
    if (!silent) {
      dom.connectionLabel.textContent = 'Loading report...';
      dom.connectionDot.style.background = '#fbbf24';
      dom.connectionDot.style.boxShadow = '0 0 0 6px rgba(251, 191, 36, 0.14)';
    }

    const report = useDemo
      ? makeFallbackReport()
      : await fetch(reportPath, { cache: 'no-store' }).then((response) => {
          if (!response.ok) {
            throw new Error(`Report fetch failed: ${response.status}`);
          }
          return response.json();
        });

    if (!useDemo && (!report.trades || !report.trades.length)) {
      const demoReport = makeFallbackReport();
      renderSummary(demoReport.summary, demoReport);
      renderTrades(demoReport.trades);
      renderEvents(demoReport.events);
      dom.connectionLabel.textContent = 'Live report is empty, showing demo view';
      dom.connectionDot.style.background = '#fbbf24';
      dom.connectionDot.style.boxShadow = '0 0 0 6px rgba(251, 191, 36, 0.14)';
      dom.sessionMode.textContent = 'Demo';
      return;
    }

    const summary = report.summary || {};
    renderSummary(summary, report);
    renderMarketPulse(report, summary);
    renderTrades(report.trades || []);
    renderEvents(report.events || []);

    dom.connectionLabel.textContent = useDemo ? 'Demo view loaded' : 'Report connected';
    dom.connectionDot.style.background = '#86efac';
    dom.connectionDot.style.boxShadow = '0 0 0 6px rgba(134, 239, 172, 0.14)';
    dom.quickNote.textContent = report.trades && report.trades.length
      ? 'Your latest report has real trades. Review the curve, then scan the events for entries and exits.'
      : 'No trades in the latest report yet. That is fine for a quiet session, but demo mode stays available so the dashboard remains useful.';
  } catch (error) {
    console.error(error);
    dom.connectionLabel.textContent = 'Using demo view';
    dom.connectionDot.style.background = '#fbbf24';
    dom.connectionDot.style.boxShadow = '0 0 0 6px rgba(251, 191, 36, 0.14)';
    const report = makeFallbackReport();
    renderSummary(report.summary, report);
    renderMarketPulse(report, report.summary || {});
    renderTrades(report.trades);
    renderEvents(report.events);
    dom.quickNote.textContent = 'Unable to load the live report, so the dashboard is showing a friendly demo session.';
  }
}

dom.refreshBtn.addEventListener('click', () => loadReport(false));
dom.demoBtn.addEventListener('click', () => loadReport(true));
dom.openJsonBtn.addEventListener('click', () => window.open(reportPath, '_blank'));

loadReport(false);
setInterval(() => loadReport(false, true), 30000);
