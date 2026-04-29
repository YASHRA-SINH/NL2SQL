import { useEffect, useMemo, useRef, useState } from "react";
import Plot from "react-plotly.js";
import {
  Activity,
  AlertTriangle,
  Bot,
  Database,
  Moon,
  Search,
  Send,
  Sparkles,
  Sun,
  Table2,
  User,
  X,
} from "lucide-react";

const defaultSuggestions = ["What tables are available?", "Show a summary of this database"];

const baseWelcomeMessage = {
  id: "welcome",
  role: "assistant",
  summary: "Choose a database profile, then ask a question. I can return SQL, data tables, and visualizations.",
};

function App() {
  const [messages, setMessages] = useState([baseWelcomeMessage]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [showDatabase, setShowDatabase] = useState(false);
  const [databases, setDatabases] = useState([]);
  const [activeDatabaseId, setActiveDatabaseId] = useState("clinic");
  const [databaseMetadata, setDatabaseMetadata] = useState(null);
  const [metadataError, setMetadataError] = useState("");
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem("healthquery-theme");
    if (saved) return saved === "dark";
    return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? true;
  });

  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
    localStorage.setItem("healthquery-theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isLoading]);

  useEffect(() => {
    async function loadDatabases() {
      try {
        const response = await fetch("/api/databases");
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Could not load database profiles");
        setDatabases(data);
        if (data.length && !data.some((database) => database.id === activeDatabaseId)) {
          setActiveDatabaseId(data[0].id);
        }
      } catch (error) {
        setMetadataError(error.message);
      }
    }
    loadDatabases();
  }, []);

  useEffect(() => {
    async function loadDatabaseMetadata() {
      setMetadataError("");
      setDatabaseMetadata(null);
      try {
        const response = await fetch(`/api/databases/${activeDatabaseId}`);
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Could not load database metadata");
        setDatabaseMetadata(data);
        setMessages([
          {
            ...baseWelcomeMessage,
            summary: `Connected to ${data.name}. Ask about ${data.tables.map((table) => table.name).slice(0, 6).join(", ")}.`,
          },
        ]);
        setConversationId(null);
      } catch (error) {
        setMetadataError(error.message);
        setMessages([
          {
            ...baseWelcomeMessage,
            summary: `I could not inspect the ${activeDatabaseId} database profile. ${error.message}`,
            error: "Database metadata unavailable",
          },
        ]);
      }
    }
    loadDatabaseMetadata();
  }, [activeDatabaseId]);

  const statusText = isLoading ? "Analyzing" : "Ready";
  const suggestions = databaseMetadata?.suggestions?.length ? databaseMetadata.suggestions : defaultSuggestions;
  const activeDatabase = databases.find((database) => database.id === activeDatabaseId);

  const chartTheme = useMemo(
    () => ({
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      font: { color: darkMode ? "#cbd5e1" : "#334155" },
      margin: { t: 48, r: 24, b: 56, l: 56 },
      autosize: true,
      legend: {
        orientation: "h",
        y: -0.18,
      },
      xaxis: {
        gridcolor: darkMode ? "rgba(148, 163, 184, 0.18)" : "rgba(100, 116, 139, 0.18)",
      },
      yaxis: {
        gridcolor: darkMode ? "rgba(148, 163, 184, 0.18)" : "rgba(100, 116, 139, 0.18)",
      },
    }),
    [darkMode]
  );

  async function submitPrompt(prompt) {
    const message = prompt.trim();
    if (!message || isLoading) return;

    const userMessage = {
      id: crypto.randomUUID(),
      role: "user",
      summary: message,
    };

    setMessages((current) => [...current, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          conversation_id: conversationId,
          database_id: activeDatabaseId,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Request failed");
      }

      if (data.conversation_id) {
        setConversationId(data.conversation_id);
      }

      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          ...data,
        },
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          error: error.message,
          summary: "I could not complete that request. Please make sure the FastAPI backend is running.",
        },
      ]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    submitPrompt(input);
  }

  return (
    <div className="app-surface min-h-screen text-slate-950 transition-colors dark:text-slate-100">
      <div className="relative mx-auto flex min-h-screen w-full max-w-[1440px] flex-col px-3 py-3 sm:px-5 sm:py-5 lg:px-8">
        <header className="mb-4 flex shrink-0 flex-wrap items-center justify-between gap-3 rounded-[1.35rem] border border-white/80 bg-white/86 px-4 py-3 shadow-[0_16px_42px_rgba(15,23,42,0.08)] backdrop-blur-xl dark:border-white/10 dark:bg-slate-900/86 dark:shadow-[0_18px_50px_rgba(0,0,0,0.28)] sm:px-5">
          <div className="flex min-w-0 items-center gap-3">
            <div className="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-slate-950 text-white shadow-sm dark:bg-white dark:text-slate-950">
              <Sparkles size={21} />
            </div>
            <div className="min-w-0">
              <h1 className="truncate text-lg font-semibold tracking-tight text-slate-950 dark:text-white sm:text-2xl">HealthQuery AI</h1>
              <p className="truncate text-xs font-medium text-slate-500 dark:text-slate-400 sm:text-sm">{databaseMetadata?.name || activeDatabase?.name || "Database workspace"}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {databases.length > 0 && (
              <select
                value={activeDatabaseId}
                onChange={(event) => setActiveDatabaseId(event.target.value)}
                disabled={isLoading}
                className="h-10 rounded-full border border-slate-200/90 bg-white px-3 text-sm font-semibold text-slate-700 shadow-sm outline-none transition hover:border-teal-300 focus:ring-4 focus:ring-teal-100 disabled:opacity-60 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:focus:ring-teal-950"
                aria-label="Select database profile"
              >
                {databases.map((database) => (
                  <option key={database.id} value={database.id}>
                    {database.name}
                  </option>
                ))}
              </select>
            )}
            <div className="hidden h-10 items-center gap-2 rounded-full border border-slate-200/80 bg-slate-50/90 px-3 text-sm font-medium text-slate-600 dark:border-slate-700 dark:bg-slate-800/90 dark:text-slate-300 sm:flex">
              <span className={`h-2.5 w-2.5 rounded-full ${isLoading ? "bg-amber-400 shadow-[0_0_0_4px_rgba(251,191,36,0.16)]" : "bg-emerald-500 shadow-[0_0_0_4px_rgba(16,185,129,0.14)]"}`} />
              {statusText}
            </div>
            <button
              type="button"
              onClick={() => setShowDatabase(true)}
              className="inline-flex h-10 items-center gap-2 rounded-full border border-slate-200/90 bg-white px-3.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-teal-300 hover:bg-teal-50 hover:text-teal-800 focus:outline-none focus:ring-4 focus:ring-teal-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:border-teal-500 dark:hover:bg-teal-950/45 dark:hover:text-teal-200 dark:focus:ring-teal-950"
            >
              <Database size={17} />
              <span className="hidden sm:inline">Database Details</span>
            </button>
            <button
              type="button"
              onClick={() => setDarkMode((value) => !value)}
              className="grid h-10 w-10 place-items-center rounded-full border border-slate-200/90 bg-white text-slate-700 shadow-sm transition hover:border-teal-300 hover:bg-teal-50 hover:text-teal-800 focus:outline-none focus:ring-4 focus:ring-teal-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:border-teal-500 dark:hover:bg-teal-950/45 dark:hover:text-teal-200 dark:focus:ring-teal-950"
              aria-label="Toggle theme"
            >
              {darkMode ? <Sun size={18} /> : <Moon size={18} />}
            </button>
          </div>
        </header>

        <main className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-[2rem] border border-white/80 bg-white/82 shadow-[0_24px_70px_rgba(15,23,42,0.12)] backdrop-blur-xl dark:border-white/10 dark:bg-slate-900/82 dark:shadow-[0_24px_80px_rgba(0,0,0,0.34)]">
          <section className="chat-canvas min-h-0 flex-1 overflow-y-auto px-3 py-5 sm:px-6 sm:py-7 lg:px-10">
            <div className="mx-auto flex max-w-5xl flex-col gap-6">
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} chartTheme={chartTheme} darkMode={darkMode} />
              ))}
              {isLoading && <TypingBubble />}
              <div ref={scrollRef} />
            </div>
          </section>

          <section className="border-t border-slate-200/80 bg-white/92 px-3 py-3 backdrop-blur-xl dark:border-slate-800 dark:bg-slate-950/72 sm:px-6 sm:py-4 lg:px-10">
            <div className="mx-auto max-w-5xl">
              <div className="mb-3 flex gap-2 overflow-x-auto pb-1">
                {suggestions.map((question) => (
                  <button
                    key={question}
                    type="button"
                    onClick={() => submitPrompt(question)}
                    disabled={isLoading}
                    className="shrink-0 rounded-full border border-slate-200/90 bg-slate-50 px-3.5 py-2 text-xs font-semibold text-slate-600 shadow-sm transition hover:border-teal-300 hover:bg-teal-50 hover:text-teal-800 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-teal-500 dark:hover:bg-teal-950/50 dark:hover:text-teal-200 sm:text-sm"
                  >
                    {question}
                  </button>
                ))}
              </div>

              <form onSubmit={handleSubmit} className="flex items-end gap-2 rounded-[1.4rem] border border-slate-200 bg-white p-2 shadow-[0_12px_30px_rgba(15,23,42,0.08)] transition focus-within:border-teal-400 focus-within:ring-4 focus-within:ring-teal-100 dark:border-slate-700 dark:bg-slate-900 dark:shadow-[0_12px_34px_rgba(0,0,0,0.24)] dark:focus-within:border-teal-500 dark:focus-within:ring-teal-950">
                <div className="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-300">
                  <Search size={19} />
                </div>
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && !event.shiftKey) {
                      event.preventDefault();
                      submitPrompt(input);
                    }
                  }}
                  placeholder={`Ask about ${databaseMetadata?.domain || "this database"}...`}
                  rows={1}
                  className="max-h-32 min-h-11 flex-1 resize-none bg-transparent px-1 py-3 text-sm leading-5 text-slate-900 outline-none placeholder:text-slate-400 dark:text-slate-100 sm:text-[15px]"
                />
                <button
                  type="submit"
                  disabled={isLoading || !input.trim()}
                  className="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-teal-600 text-white shadow-[0_12px_24px_rgba(13,148,136,0.24)] transition hover:bg-teal-500 focus:outline-none focus:ring-4 focus:ring-teal-100 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none dark:focus:ring-teal-950 dark:disabled:bg-slate-700"
                  aria-label="Send prompt"
                >
                  <Send size={19} />
                </button>
              </form>
            </div>
          </section>
        </main>
      </div>

      {showDatabase && <DatabasePanel metadata={databaseMetadata} error={metadataError} onClose={() => setShowDatabase(false)} />}
    </div>
  );
}

function ChatMessage({ message, chartTheme, darkMode }) {
  const isUser = message.role === "user";

  return (
    <article className={`flex w-full gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && <Avatar icon={<Bot size={18} />} tone="assistant" />}
      <div className={`flex max-w-[94%] flex-col gap-3 sm:max-w-[84%] lg:max-w-[78%] ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`px-4 py-3 text-sm leading-6 shadow-sm sm:px-5 ${
            isUser
              ? "rounded-[1.35rem] rounded-br-md bg-slate-950 text-white dark:bg-teal-600"
              : "rounded-[1.35rem] rounded-bl-md border border-slate-200/90 bg-white text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
          }`}
        >
          {message.error && <p className="mb-2 text-sm font-semibold text-rose-500 dark:text-rose-300">{message.error}</p>}
          <p className="whitespace-pre-wrap text-[15px]">{message.summary || "Done."}</p>
          {Array.isArray(message.warnings) && message.warnings.length > 0 && (
            <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-medium leading-5 text-amber-800 dark:border-amber-700/60 dark:bg-amber-950/35 dark:text-amber-200">
              <div className="mb-1 flex items-center gap-1.5 font-semibold">
                <AlertTriangle size={14} />
                Result validation
              </div>
              {message.warnings.map((warning) => (
                <p key={warning}>{warning}</p>
              ))}
            </div>
          )}
        </div>

        {!isUser && message.sql && <SqlBlock sql={message.sql} />}
        {!isUser && message.chart && <ChartBlock chart={message.chart} chartTheme={chartTheme} darkMode={darkMode} />}
        {!isUser && Array.isArray(message.data) && message.data.length > 0 && <DataTable data={message.data} columns={message.columns} />}
      </div>
      {isUser && <Avatar icon={<User size={18} />} tone="user" />}
    </article>
  );
}

function Avatar({ icon, tone }) {
  return (
    <div
      className={`mt-1 hidden h-9 w-9 shrink-0 place-items-center rounded-2xl border shadow-sm sm:grid ${
        tone === "user" ? "border-slate-900 bg-slate-950 text-white dark:border-teal-500 dark:bg-teal-600" : "border-slate-200 bg-white text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
      }`}
    >
      {icon}
    </div>
  );
}

function SqlBlock({ sql }) {
  return (
    <div className="w-full overflow-hidden rounded-[1.35rem] border border-slate-200 bg-slate-950 text-slate-100 shadow-[0_14px_38px_rgba(15,23,42,0.12)] dark:border-slate-700 dark:shadow-[0_16px_42px_rgba(0,0,0,0.24)]">
      <div className="flex items-center gap-2 border-b border-white/10 bg-white/[0.03] px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-slate-400">
        <Activity size={14} />
        Generated SQL
      </div>
      <pre className="overflow-x-auto p-4 text-xs leading-6 sm:text-[13px]">
        <code>{sql}</code>
      </pre>
    </div>
  );
}

function ChartBlock({ chart, chartTheme, darkMode }) {
  const data = Array.isArray(chart.data) ? chart.data : [];
  const layout = {
    ...chartTheme,
    ...(chart.layout || {}),
    paper_bgcolor: chartTheme.paper_bgcolor,
    plot_bgcolor: chartTheme.plot_bgcolor,
    font: chartTheme.font,
  };

  return (
    <div className="w-full overflow-hidden rounded-[1.35rem] border border-slate-200/90 bg-white shadow-[0_14px_38px_rgba(15,23,42,0.1)] dark:border-slate-700 dark:bg-slate-800 dark:shadow-[0_16px_42px_rgba(0,0,0,0.22)]">
      <div className="flex items-center justify-between gap-3 border-b border-slate-200 bg-slate-50/80 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:border-slate-700 dark:bg-slate-900/60 dark:text-slate-400">
        <span className="inline-flex items-center gap-2">
          <Activity size={14} />
          Visualization
        </span>
        <span className="rounded-full bg-teal-50 px-2 py-1 text-[11px] font-bold text-teal-700 dark:bg-teal-950/55 dark:text-teal-300">Plotly</span>
      </div>
      <div className="min-h-[320px] w-full p-3 sm:min-h-[420px] sm:p-4">
        <Plot
          data={data}
          layout={layout}
          config={{
            responsive: true,
            displaylogo: false,
            modeBarButtonsToRemove: ["lasso2d", "select2d"],
          }}
          useResizeHandler
          style={{ width: "100%", height: "clamp(320px, 52vh, 520px)" }}
          className={darkMode ? "plotly-dark" : ""}
        />
      </div>
    </div>
  );
}

function DataTable({ data, columns }) {
  const tableColumns = columns?.length ? columns : Object.keys(data[0] || {});
  const rows = data.slice(0, 50);

  return (
    <div className="w-full overflow-hidden rounded-[1.35rem] border border-slate-200/90 bg-white shadow-[0_14px_38px_rgba(15,23,42,0.1)] dark:border-slate-700 dark:bg-slate-800 dark:shadow-[0_16px_42px_rgba(0,0,0,0.22)]">
      <div className="flex items-center justify-between gap-3 border-b border-slate-200 bg-slate-50/80 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:border-slate-700 dark:bg-slate-900/60 dark:text-slate-400">
        <span className="inline-flex items-center gap-2">
          <Table2 size={14} />
          Data Results
        </span>
        <span className="rounded-full bg-slate-200/70 px-2 py-1 text-[11px] text-slate-600 dark:bg-slate-700 dark:text-slate-300">{data.length} rows</span>
      </div>
      <div className="max-h-96 overflow-auto">
        <table className="min-w-full border-separate border-spacing-0 text-left text-sm">
          <thead className="sticky top-0 z-10 bg-slate-100 text-xs uppercase text-slate-500 dark:bg-slate-900 dark:text-slate-400">
            <tr>
              {tableColumns.map((column) => (
                <th key={column} className="whitespace-nowrap border-b border-slate-200 px-4 py-3 font-semibold dark:border-slate-700">
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={index} className="transition odd:bg-white even:bg-slate-50/80 hover:bg-teal-50/50 dark:odd:bg-slate-800 dark:even:bg-slate-900/55 dark:hover:bg-teal-950/20">
                {tableColumns.map((column) => (
                  <td key={column} className="whitespace-nowrap border-b border-slate-100 px-4 py-3 text-slate-700 dark:border-slate-700/70 dark:text-slate-200">
                    {row[column] === null || row[column] === undefined ? "NULL" : String(row[column])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {data.length > 50 && <p className="px-4 py-3 text-center text-xs text-slate-500 dark:text-slate-400">Showing first 50 of {data.length} rows</p>}
    </div>
  );
}

function TypingBubble() {
  return (
    <div className="flex justify-start gap-3">
      <Avatar icon={<Bot size={18} />} tone="assistant" />
      <div className="rounded-[1.35rem] rounded-bl-md border border-slate-200 bg-white px-4 py-4 shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 animate-bounce rounded-full bg-teal-500 [animation-delay:-0.2s]" />
          <span className="h-2 w-2 animate-bounce rounded-full bg-teal-500 [animation-delay:-0.1s]" />
          <span className="h-2 w-2 animate-bounce rounded-full bg-teal-500" />
        </div>
      </div>
    </div>
  );
}

function DatabasePanel({ metadata, error, onClose }) {
  const tables = metadata?.tables || [];
  const totalRows = tables.reduce((sum, table) => sum + (Number.isFinite(table.row_count) ? table.row_count : 0), 0);

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/50 p-0 backdrop-blur-md sm:items-center sm:p-4">
      <aside className="max-h-[92vh] w-full max-w-4xl overflow-hidden rounded-t-[2rem] border border-slate-200 bg-white shadow-[0_28px_90px_rgba(15,23,42,0.24)] dark:border-slate-700 dark:bg-slate-900 sm:rounded-[2rem]">
        <div className="flex items-start justify-between gap-4 border-b border-slate-200 bg-slate-50/70 px-5 py-5 dark:border-slate-700 dark:bg-slate-950/40 sm:px-6">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-teal-600 dark:text-teal-300">{metadata?.dialect || "Database"} Profile</p>
            <h2 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">{metadata?.name || "Database Details"}</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600 dark:text-slate-300">
              {metadata?.description || error || "Database metadata is not available yet."}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="grid h-10 w-10 shrink-0 place-items-center rounded-full border border-slate-200 bg-white text-slate-600 transition hover:border-rose-300 hover:bg-rose-50 hover:text-rose-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-rose-950/30"
            aria-label="Close database details"
          >
            <X size={18} />
          </button>
        </div>

        <div className="max-h-[72vh] overflow-y-auto p-5 sm:p-6">
          <div className="grid gap-3 sm:grid-cols-3">
            <Metric label="Database" value={metadata?.database || "N/A"} />
            <Metric label="Tables" value={String(tables.length)} />
            <Metric label="Rows" value={String(totalRows)} />
          </div>

          <div className="mt-5 grid gap-4 md:grid-cols-2">
            {tables.map((table) => (
              <div key={table.name} className="rounded-[1.35rem] border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-800/80">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Database size={17} className="text-teal-600 dark:text-teal-300" />
                    <h3 className="font-semibold text-slate-950 dark:text-white">{table.name}</h3>
                  </div>
                  <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">{table.row_count ?? "?"} rows</span>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {table.columns.map((column) => (
                    <span key={column.name} className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-medium text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">
                      {column.name}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </aside>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded-[1.35rem] border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-800">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{label}</p>
      <p className="mt-1 text-3xl font-semibold tracking-tight text-slate-950 dark:text-white">{value}</p>
    </div>
  );
}

export default App;
