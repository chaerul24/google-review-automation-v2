import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  Star,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Sparkles,
  BarChart3,
  Calendar,
  Zap,
} from 'lucide-react';
import { api } from '../api/client';

export default function AnalyticsCharts() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [hoveredPoint, setHoveredPoint] = useState(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const res = await api.getAnalytics();
        if (res && res.analytics) {
          setAnalytics(res.analytics);
        }
      } catch (err) {
        console.debug('Analytics fetch error:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 flex items-center justify-center min-h-[200px]">
        <div className="flex items-center gap-2 text-xs text-slate-400 font-mono">
          <div className="w-4 h-4 border-2 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin"></div>
          <span>Menganalisis performa kampanye...</span>
        </div>
      </div>
    );
  }

  const starDist = analytics?.star_distribution || { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
  const dailyTrends = analytics?.daily_trends || [];
  const totalReviewed = analytics?.total_reviewed || 0;
  const successRate = analytics?.success_rate || 100;
  const cookieHealth = analytics?.cookie_health || 100;

  // Chart dimensions & calculations
  const chartHeight = 120;
  const chartWidth = 460;
  const maxCount = Math.max(5, ...dailyTrends.map((d) => d.count || 0));

  const points = dailyTrends.map((d, index) => {
    const x = dailyTrends.length > 1 ? (index / (dailyTrends.length - 1)) * (chartWidth - 40) + 20 : chartWidth / 2;
    const y = chartHeight - ((d.count || 0) / maxCount) * (chartHeight - 30) - 15;
    return { x, y, count: d.count, day: d.day };
  });

  // Build SVG path
  const pathD = points.length > 1
    ? points.reduce((acc, pt, i, arr) => {
        if (i === 0) return `M ${pt.x} ${pt.y}`;
        const prev = arr[i - 1];
        const cx = (prev.x + pt.x) / 2;
        return `${acc} C ${cx} ${prev.y}, ${cx} ${pt.y}, ${pt.x} ${pt.y}`;
      }, '')
    : `M 20 ${chartHeight - 20} L ${chartWidth - 20} ${chartHeight - 20}`;

  const fillD = points.length > 1
    ? `${pathD} L ${points[points.length - 1].x} ${chartHeight} L ${points[0].x} ${chartHeight} Z`
    : '';

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
      {/* Left (7 cols): Review Velocity Curve */}
      <div className="lg:col-span-7 bg-slate-900/80 border border-slate-800/80 rounded-2xl p-5 shadow-xl relative overflow-hidden flex flex-col justify-between">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
          <div>
            <h3 className="font-extrabold text-sm text-white flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span>Review Velocity (7 Hari Terakhir)</span>
            </h3>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Intensitas penyebaran ulasan bot pada target Google Maps.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-bold flex items-center gap-1">
              <Zap className="w-3 h-3 text-emerald-400" />
              Live Velocity
            </span>
          </div>
        </div>

        {/* SVG Chart Area */}
        <div className="relative pt-6 pb-2">
          {hoveredPoint && (
            <div
              className="absolute pointer-events-none z-10 px-2.5 py-1 rounded-lg bg-slate-950 border border-emerald-500/40 text-[11px] font-mono text-emerald-300 shadow-xl"
              style={{
                left: `${(hoveredPoint.x / chartWidth) * 100}%`,
                top: `${hoveredPoint.y - 30}px`,
                transform: 'translateX(-50%)',
              }}
            >
              <span className="font-bold">{hoveredPoint.count} ulasan</span>
              <span className="text-slate-400 text-[10px] ml-1.5">({hoveredPoint.day})</span>
            </div>
          )}

          <svg
            viewBox={`0 0 ${chartWidth} ${chartHeight}`}
            className="w-full h-32 overflow-visible"
          >
            <defs>
              <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#10b981" stopOpacity="0.35" />
                <stop offset="100%" stopColor="#10b981" stopOpacity="0.0" />
              </linearGradient>
            </defs>

            {/* Grid lines */}
            <line x1="20" y1={chartHeight - 15} x2={chartWidth - 20} y2={chartHeight - 15} stroke="rgba(255,255,255,0.06)" strokeDasharray="4" />
            <line x1="20" y1={chartHeight / 2} x2={chartWidth - 20} y2={chartHeight / 2} stroke="rgba(255,255,255,0.06)" strokeDasharray="4" />

            {/* Area fill & curve line */}
            {fillD && <path d={fillD} fill="url(#areaGradient)" />}
            <path
              d={pathD}
              fill="none"
              stroke="#10b981"
              strokeWidth="2.5"
              strokeLinecap="round"
            />

            {/* Interactive Data Points */}
            {points.map((pt, idx) => (
              <g
                key={idx}
                onMouseEnter={() => setHoveredPoint(pt)}
                onMouseLeave={() => setHoveredPoint(null)}
                className="cursor-pointer"
              >
                <circle
                  cx={pt.x}
                  cy={pt.y}
                  r="4"
                  fill="#0b0f17"
                  stroke="#10b981"
                  strokeWidth="2"
                  className="transition-all hover:r-6"
                />
              </g>
            ))}
          </svg>

          {/* X Axis Date labels */}
          <div className="flex justify-between items-center text-[10px] font-mono text-slate-500 pt-2 px-3">
            {dailyTrends.slice(0, 5).map((d, i) => (
              <span key={i}>{d.day.slice(5)}</span>
            ))}
          </div>
        </div>

        {/* Footer KPI Mini Bar */}
        <div className="grid grid-cols-3 gap-2 pt-3 border-t border-slate-800/80 text-center">
          <div className="p-2 rounded-xl bg-slate-950/60 border border-slate-800/60">
            <span className="text-[10px] text-slate-400 block font-mono">Total Posted</span>
            <span className="text-sm font-extrabold text-white">{totalReviewed}</span>
          </div>
          <div className="p-2 rounded-xl bg-slate-950/60 border border-slate-800/60">
            <span className="text-[10px] text-slate-400 block font-mono">Success Rate</span>
            <span className="text-sm font-extrabold text-emerald-400">{successRate}%</span>
          </div>
          <div className="p-2 rounded-xl bg-slate-950/60 border border-slate-800/60">
            <span className="text-[10px] text-slate-400 block font-mono">Cookie Health</span>
            <span className="text-sm font-extrabold text-teal-400">{cookieHealth}%</span>
          </div>
        </div>
      </div>

      {/* Right (5 cols): Star Rating Breakdown Bars */}
      <div className="lg:col-span-5 bg-slate-900/80 border border-slate-800/80 rounded-2xl p-5 shadow-xl flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
            <div>
              <h3 className="font-extrabold text-sm text-white flex items-center gap-2">
                <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
                <span>Distribusi Bintang Global</span>
              </h3>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Keseimbangan rating ulasan seluruh listing.
              </p>
            </div>
            <span className="text-xs font-bold font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
              5★ Dominan
            </span>
          </div>

          {/* Breakdown Bars */}
          <div className="space-y-2.5 pt-4">
            {[5, 4, 3, 2, 1].map((star) => {
              const count = starDist[star] || 0;
              const pct = totalReviewed > 0 ? Math.round((count / totalReviewed) * 100) : star === 5 ? 100 : 0;

              return (
                <div key={star} className="flex items-center gap-3 text-xs">
                  <div className="flex items-center gap-1 w-10 text-amber-400 font-bold shrink-0">
                    <span>{star}</span>
                    <Star className="w-3 h-3 fill-current" />
                  </div>

                  <div className="flex-1 h-2 rounded-full bg-slate-950 overflow-hidden border border-slate-800">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        star === 5
                          ? 'bg-gradient-to-r from-emerald-500 to-teal-400'
                          : star === 4
                          ? 'bg-teal-500'
                          : star === 3
                          ? 'bg-amber-400'
                          : 'bg-rose-400'
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>

                  <span className="text-[11px] font-mono text-slate-400 w-12 text-right shrink-0">
                    {count} ({pct}%)
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Quality Notice */}
        <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center gap-2 text-[11px] text-slate-400">
          <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>Rasio ulasan bintang 5 & 4 terjaga natural untuk optimasi Local SEO Google Maps.</span>
        </div>
      </div>
    </div>
  );
}
