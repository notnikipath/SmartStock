import { useEffect, useMemo, useRef } from "react";
import { useDispatch, useSelector } from "react-redux";
import * as echarts from "echarts/core";
import { LineChart } from "echarts/charts";
import { GridComponent, TooltipComponent, AriaComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
echarts.use([LineChart, GridComponent, TooltipComponent, AriaComponent, CanvasRenderer]);
import { fetchHealth, setLanguage, setRole } from "../store/dashboardSlice";
import { KpiCard } from "../components/KpiCard";

const TEXT = {
  ru: {
    title: "SmartStock: Центр управления запасами",
    subtitle: "Прогноз, оптимизация и контроль складов в реальном времени",
    language: "Язык",
    role: "Роль",
    refresh: "Обновить",
    loading: "Загрузка...",
    unavailable: "недоступно",
    mape: "MAPE 7 дней",
    sku: "SKU под контролем",
    users: "Активные пользователи",
    tx: "Транзакций/сек",
  },
  en: {
    title: "SmartStock: Inventory Control Center",
    subtitle: "Demand forecast, optimization and warehouse control in real-time",
    language: "Language",
    role: "Role",
    refresh: "Refresh",
    loading: "Loading...",
    unavailable: "unavailable",
    mape: "MAPE 7 days",
    sku: "Tracked SKU",
    users: "Active users",
    tx: "Transactions/sec",
  },
};

export function DashboardPage() {
  const dispatch = useDispatch();
  const chartRef = useRef(null);
  const { language, role, health, loading } = useSelector((state) => state.dashboard);
  const t = TEXT[language];

  useEffect(() => {
    dispatch(fetchHealth());
  }, [dispatch]);

  useEffect(() => {
    if (!chartRef.current) return undefined;
    const chart = echarts.init(chartRef.current);
    chart.setOption({
      backgroundColor: "transparent",
      aria: { enabled: true },
      tooltip: { trigger: "axis" },
      xAxis: {
        type: "category",
        data: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
      },
      yAxis: { type: "value" },
      series: [
        {
          name: "Forecast",
          type: "line",
          smooth: true,
          data: [120, 126, 132, 140, 138, 150, 158],
          lineStyle: { width: 3, color: "#0f766e" },
          areaStyle: { color: "rgba(15, 118, 110, 0.22)" },
        },
      ],
    });
    const onResize = () => chart.resize();
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      chart.dispose();
    };
  }, []);

  const serviceRows = useMemo(
    () =>
      Object.entries(health || {}).map(([service, state]) => ({
        service,
        status: state?.body?.status || t.unavailable,
      })),
    [health, t.unavailable]
  );

  return (
    <div className="layout">
      <header className="hero">
        <div>
          <h1>{t.title}</h1>
          <p>{t.subtitle}</p>
        </div>
        <div className="toolbar">
          <label>
            {t.language}
            <select value={language} onChange={(e) => dispatch(setLanguage(e.target.value))}>
              <option value="ru">RU</option>
              <option value="en">EN</option>
            </select>
          </label>
          <label>
            {t.role}
            <select value={role} onChange={(e) => dispatch(setRole(e.target.value))}>
              <option value="warehouse_worker">Warehouse</option>
              <option value="logistician">Logistician</option>
              <option value="analyst">Analyst</option>
              <option value="admin">Admin</option>
            </select>
          </label>
          <button onClick={() => dispatch(fetchHealth())}>{t.refresh}</button>
        </div>
      </header>

      <section className="kpi-grid">
        <KpiCard title={t.mape} value="< 15%" note="target" />
        <KpiCard title={t.sku} value="10 000+" note="multi warehouse" />
        <KpiCard title={t.users} value="100+" note="concurrent" />
        <KpiCard title={t.tx} value="1000" note="peak throughput" />
      </section>

      <section className="panel">
        <h2>Demand Trend</h2>
        <div className="chart" ref={chartRef} />
      </section>

      <section className="panel">
        <h2>Service Health</h2>
        {loading ? (
          <p>{t.loading}</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Service</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {serviceRows.map((row) => (
                <tr key={row.service}>
                  <td>{row.service}</td>
                  <td>{row.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
