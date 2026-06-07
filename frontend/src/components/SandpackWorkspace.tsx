"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  SandpackProvider,
  SandpackLayout,
  SandpackCodeEditor,
  SandpackPreview,
  useSandpack,
} from "@codesandbox/sandpack-react";
import {
  FileCode,
  Terminal,
  Download,
  Sparkles,
  RefreshCw,
  FolderIcon,
  ChevronRight,
  Code2,
  Layers,
  MonitorPlay,
  Settings,
  Flame,
} from "lucide-react";
import JSZip from "jszip";
import { motion, AnimatePresence } from "framer-motion";

interface SandpackWorkspaceProps {
  initialFiles: Record<string, string>;
  onReset: () => void;
}

function WorkspaceInner({ onReset }: { onReset: () => void }) {
  const { sandpack } = useSandpack();
  const [activeFile, setActiveFile] = useState<string>("/pages/portfolio.tsx");
  const [prompt, setPrompt] = useState("");
  const [isModifying, setIsModifying] = useState(false);
  const [modifyStatus, setModifyStatus] = useState<string[]>([]);
  const [showExplorer, setShowExplorer] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  
  const terminalEndRef = useRef<HTMLDivElement>(null);
  const lastHealedErrorRef = useRef<string | null>(null);

  // Keep a stable ref to the sandpack object to avoid stale closures in listeners
  const sandpackRef = useRef(sandpack);
  useEffect(() => {
    sandpackRef.current = sandpack;
  }, [sandpack]);

  // Set the active file inside Sandpack whenever user clicks in our custom tree
  // Bound to sandpack.activeFile primitive instead of the whole sandpack object reference
  useEffect(() => {
    if (sandpack.files[activeFile] && sandpack.activeFile !== activeFile) {
      sandpack.openFile(activeFile);
    }
  }, [activeFile, sandpack.activeFile]);

  // Scroll to bottom of refinement terminal logs
  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [modifyStatus]);

  // Unified, robust non-looping Auto-Healer streamer
  const autoHeal = async (errorText: string) => {
    if (isModifying) return;

    // Standardize JSX/TSX syntax error messages slightly to catch duplicates
    const normalizedError = errorText.trim().replace(/\s+/g, " ");

    if (lastHealedErrorRef.current === normalizedError) {
      console.warn("[Auto-Healer] Halting to prevent infinite healing loop for identical error:", errorText);
      return;
    }
    lastHealedErrorRef.current = normalizedError;

    setIsModifying(true);
    setModifyStatus((prev) => [
      ...prev, 
      `[Auto-Healer] ⚡ Intercepted code compilation/runtime exception:`,
      `[Error Log] ${errorText}`,
      `[Auto-Healer] Ingesting sandbox state & spawning Multi-Agent Modifier... 🛠️`
    ]);
    
    try {
      const filesForBackend: Record<string, string> = {};
      Object.entries(sandpackRef.current.files).forEach(([path, fileObj]) => {
        if (path === "/App.js") return; // Exclude virtual App.js
        const cleanPath = path.startsWith("/") ? path.substring(1) : path;
        filesForBackend[cleanPath] = fileObj.code;
      });

      const response = await fetch("http://localhost:8000/api/modify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          current_html: JSON.stringify(filesForBackend),
          modification: `FIX THIS COMPILATION/RUNTIME ERROR IN THE CODE:\n${errorText}`,
        }),
      });

      if (!response.ok) throw new Error("Auto-healer backend returned status error");

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) throw new Error("Auto-healer response is not readable");

      let buffer = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.trim().startsWith("data: ")) {
            const dataStr = line.trim().slice(6);
            if (!dataStr) continue;

            const parsed = JSON.parse(dataStr);
            if (parsed.status) {
              setModifyStatus((prev) => [...prev, `[Auto-Healer Agent] ${parsed.status}`]);
            }

            if (parsed.html && parsed.status === "complete") {
              setModifyStatus((prev) => [...prev, "[Auto-Healer] Integrating updated files..."]);
              const updatedFiles = JSON.parse(parsed.html);
              
              Object.entries(updatedFiles).forEach(([filePath, code]) => {
                const sandpackPath = filePath.startsWith("/") ? filePath : `/${filePath}`;
                sandpackRef.current.updateFile(sandpackPath, code as string);
              });
              setModifyStatus((prev) => [...prev, "✔ Auto-healing complete! Workspace hot-reloaded."]);
              lastHealedErrorRef.current = null; // Clear on success
            }
          }
        }
      }
    } catch (err: any) {
      console.error("Auto-healing failed:", err);
      setModifyStatus((prev) => [...prev, `❌ Self-fixing aborted: ${err?.message || "Modifier agent failure"}`]);
    } finally {
      setIsModifying(false);
    }
  };

  // 1. Watch for Compile/Syntax errors from the Sandpack bundler in real-time
  useEffect(() => {
    if (sandpack.error && !isModifying) {
      const errorText = sandpack.error.message;
      autoHeal(errorText);
    }
  }, [sandpack.error, isModifying]);

  // 2. Watch for Runtime errors from the iframe ErrorBoundary postMessage
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data && event.data.type === "sandpack-error") {
        const errorText = event.data.error;
        console.warn("Captured runtime exception in sandbox:", errorText);
        autoHeal(errorText);
      }
    };

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [isModifying]);

  // Exporter: Generate Zip
  const handleExportZip = async () => {
    try {
      setIsExporting(true);
      const zip = new JSZip();
      
      Object.entries(sandpack.files).forEach(([path, fileObj]) => {
        // Exclude virtual /App.js from downloaded Next.js project
        if (path === "/App.js") return;

        // Strip leading slash for zip folder structure consistency
        const cleanPath = path.startsWith("/") ? path.substring(1) : path;
        zip.file(cleanPath, fileObj.code);
      });

      const blob = await zip.generateAsync({ type: "blob" });
      const downloadUrl = URL.createObjectURL(blob);
      
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = "portfolio-nextjs-project.zip";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      console.error("Failed to generate zip", err);
      alert("Export failed. Please check the logs.");
    } finally {
      setIsExporting(false);
    }
  };

  // AI Refine SSE Call
  const handleAIRefine = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isModifying) return;

    setIsModifying(true);
    setModifyStatus(["[System] Compiling workspace files for refinement...", "[System] Initiating backend Modifier agent..."]);
    
    try {
      // 1. Prepare files: strip leading slash for backend compatibility
      const filesForBackend: Record<string, string> = {};
      Object.entries(sandpack.files).forEach(([path, fileObj]) => {
        // Exclude App.js virtual entry
        if (path === "/App.js") return;

        const cleanPath = path.startsWith("/") ? path.substring(1) : path;
        filesForBackend[cleanPath] = fileObj.code;
      });

      // 2. Fetch the stream from FastAPI
      const response = await fetch("http://localhost:8000/api/modify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          current_html: JSON.stringify(filesForBackend),
          modification: prompt,
        }),
      });

      if (!response.ok) {
        throw new Error(`Server returned code ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) {
        throw new Error("Response body is not readable");
      }

      let buffer = "";
      setPrompt("");

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || ""; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.trim().startsWith("data: ")) {
            const dataStr = line.trim().slice(6);
            if (!dataStr) continue;
            
            try {
              const parsed = JSON.parse(dataStr);
              
              if (parsed.status) {
                setModifyStatus((prev) => [...prev, `[Agent] ${parsed.status}`]);
              }

              // On completion, inject new code back into sandpack files!
              if (parsed.html && parsed.status === "complete") {
                setModifyStatus((prev) => [...prev, "[System] Synchronizing workspace with agent changes..."]);
                const updatedFiles = JSON.parse(parsed.html);
                
                Object.entries(updatedFiles).forEach(([filePath, code]) => {
                  const sandpackPath = filePath.startsWith("/") ? filePath : `/${filePath}`;
                  sandpack.updateFile(sandpackPath, code as string);
                });
                
                setModifyStatus((prev) => [...prev, "✔ Modification completed! Code hot-reloaded successfully."]);
              }
            } catch (err) {
              console.error("Failed to parse SSE line", err);
            }
          }
        }
      }
    } catch (error: any) {
      console.error(error);
      setModifyStatus((prev) => [...prev, `❌ Error: ${error?.message || "Failed to contact refinement server."}`]);
    } finally {
      setIsModifying(false);
    }
  };

  // Group files into structural view categories (excluding /App.js virtual page)
  const fileCategories = {
    pages: Object.keys(sandpack.files).filter((p) => p.startsWith("/pages/") && p !== "/App.js"),
    components: Object.keys(sandpack.files).filter((p) => p.startsWith("/components/")),
    styles: Object.keys(sandpack.files).filter((p) => p.startsWith("/styles/") || p.includes("css")),
    config: Object.keys(sandpack.files).filter(
      (p) => !p.startsWith("/pages/") && !p.startsWith("/components/") && !p.startsWith("/styles/") && !p.includes("css") && p !== "/App.js"
    ),
  };

  const getFileName = (path: string) => path.split("/").pop() || path;

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#030303]">
      {/* Top Premium Navbar */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-white/5 glass-panel bg-black/40 z-20">
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-violet-600 to-emerald-500 shadow-md">
            <Sparkles className="w-5 h-5 text-white animate-pulse" />
          </div>
          <div>
            <h1 className="text-md font-semibold tracking-wide text-white flex items-center gap-2">
              autoFolio <span className="text-xs px-2 py-0.5 rounded-full bg-violet-500/10 text-violet-400 border border-violet-500/20">Sandbox IDE</span>
            </h1>
            <p className="text-[10px] text-zinc-400">Multi-agent Developer Workspace</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onReset}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg border border-white/5 bg-white/5 text-xs text-zinc-300 hover:bg-white/10 hover:text-white transition-all"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Generate New
          </button>
          
          <button
            onClick={handleExportZip}
            disabled={isExporting}
            className="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-xs font-medium text-white shadow-lg hover:shadow-violet-600/15 transition-all disabled:opacity-50"
          >
            {isExporting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
            Export Project (.zip)
          </button>
        </div>
      </header>

      {/* Editor & Preview Split Panel */}
      <div className="flex flex-1 overflow-hidden relative">
        <SandpackLayout className="w-full h-full border-none! bg-[#030303]! flex flex-1">
          
          {/* File Explorer Tree Panel */}
          <AnimatePresence initial={false}>
            {showExplorer && (
              <motion.div
                initial={{ width: 0, opacity: 0 }}
                animate={{ width: 260, opacity: 1 }}
                exit={{ width: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="h-full border-r border-white/5 bg-[#050507] flex flex-col flex-shrink-0 select-none overflow-y-auto"
              >
                <div className="p-4 border-b border-white/5 flex items-center justify-between bg-black/20">
                  <span className="text-xs font-semibold tracking-wider text-zinc-400 uppercase">Explorer</span>
                  <FolderIcon className="w-4 h-4 text-violet-400" />
                </div>
                
                <div className="p-3 space-y-4">
                  {/* Category: Pages */}
                  {fileCategories.pages.length > 0 && (
                    <div className="space-y-1">
                      <div className="flex items-center gap-1.5 text-zinc-400 text-xs font-medium px-2 py-1">
                        <Code2 className="w-3.5 h-3.5 text-emerald-400" />
                        <span>Pages</span>
                      </div>
                      <div className="pl-3 space-y-0.5">
                        {fileCategories.pages.map((p) => (
                          <button
                            key={p}
                            onClick={() => setActiveFile(p)}
                            className={`flex items-center w-full px-2 py-1.5 text-xs rounded-md text-left transition-all ${
                              activeFile === p
                                ? "bg-violet-500/10 text-violet-300 border-l-2 border-violet-500 font-medium"
                                : "text-zinc-400 hover:bg-white/5 hover:text-zinc-200"
                            }`}
                          >
                            <ChevronRight className={`w-3 h-3 mr-1 transition-transform ${activeFile === p ? "rotate-90 text-violet-400" : "text-zinc-500"}`} />
                            <span className="truncate">{getFileName(p)}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Category: Components */}
                  {fileCategories.components.length > 0 && (
                    <div className="space-y-1">
                      <div className="flex items-center gap-1.5 text-zinc-400 text-xs font-medium px-2 py-1">
                        <Layers className="w-3.5 h-3.5 text-sky-400" />
                        <span>React Bits Components</span>
                      </div>
                      <div className="pl-3 space-y-0.5 max-h-48 overflow-y-auto pr-1">
                        {fileCategories.components.map((p) => (
                          <button
                            key={p}
                            onClick={() => setActiveFile(p)}
                            className={`flex items-center w-full px-2 py-1.5 text-xs rounded-md text-left transition-all ${
                              activeFile === p
                                ? "bg-violet-500/10 text-violet-300 border-l-2 border-violet-500 font-medium"
                                : "text-zinc-400 hover:bg-white/5 hover:text-zinc-200"
                            }`}
                          >
                            <span className="truncate pl-4">{p.replace("/components/", "")}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Category: Styles */}
                  {fileCategories.styles.length > 0 && (
                    <div className="space-y-1">
                      <div className="flex items-center gap-1.5 text-zinc-400 text-xs font-medium px-2 py-1">
                        <Flame className="w-3.5 h-3.5 text-orange-400" />
                        <span>Styles</span>
                      </div>
                      <div className="pl-3 space-y-0.5">
                        {fileCategories.styles.map((p) => (
                          <button
                            key={p}
                            onClick={() => setActiveFile(p)}
                            className={`flex items-center w-full px-2 py-1.5 text-xs rounded-md text-left transition-all ${
                              activeFile === p
                                ? "bg-violet-500/10 text-violet-300 border-l-2 border-violet-500 font-medium"
                                : "text-zinc-400 hover:bg-white/5 hover:text-zinc-200"
                            }`}
                          >
                            <span className="truncate pl-4">{getFileName(p)}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Category: Configuration */}
                  {fileCategories.config.length > 0 && (
                    <div className="space-y-1">
                      <div className="flex items-center gap-1.5 text-zinc-400 text-xs font-medium px-2 py-1">
                        <Settings className="w-3.5 h-3.5 text-indigo-400" />
                        <span>Configs</span>
                      </div>
                      <div className="pl-3 space-y-0.5">
                        {fileCategories.config.map((p) => (
                          <button
                            key={p}
                            onClick={() => setActiveFile(p)}
                            className={`flex items-center w-full px-2 py-1.5 text-xs rounded-md text-left transition-all ${
                              activeFile === p
                                ? "bg-violet-500/10 text-violet-300 border-l-2 border-violet-500 font-medium"
                                : "text-zinc-400 hover:bg-white/5 hover:text-zinc-200"
                            }`}
                          >
                            <span className="truncate pl-4">{getFileName(p)}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Code Editor Container */}
          <div className="flex flex-col flex-1 h-full overflow-hidden min-w-0">
            {/* Editor Tab Headers */}
            <div className="flex items-center justify-between px-4 py-2 bg-[#070709] border-b border-white/5 h-11 flex-shrink-0 select-none">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowExplorer(!showExplorer)}
                  className="p-1 text-zinc-400 hover:text-white rounded hover:bg-white/5 transition-all mr-2"
                  title="Toggle Explorer"
                >
                  <FolderIcon className="w-4 h-4" />
                </button>
                <div className="flex items-center gap-2 px-3 py-1 bg-white/5 rounded-md border border-white/5">
                  <FileCode className="w-3.5 h-3.5 text-violet-400" />
                  <span className="text-xs text-zinc-300 font-mono">{activeFile}</span>
                </div>
              </div>
              <div className="flex items-center gap-1.5 text-[10px] text-zinc-500 font-mono">
                <span>Tab size: 2</span>
                <span className="text-zinc-700">|</span>
                <span>TypeScript</span>
              </div>
            </div>

            {/* CodeEditor itself */}
            <div className="flex-1 overflow-hidden relative bg-[#09090b]">
              <SandpackCodeEditor
                showLineNumbers
                showTabs={false}
                closableTabs={false}
                className="w-full h-full font-mono text-sm bg-transparent! outline-none!"
              />
            </div>

            {/* Bottom AI Refinement Console Panel */}
            <div className="h-64 border-t border-white/5 bg-[#050508] flex flex-col flex-shrink-0">
              {/* Console header */}
              <div className="flex items-center justify-between px-4 py-2 border-b border-white/5 bg-black/20 flex-shrink-0 select-none">
                <div className="flex items-center gap-2 text-xs font-semibold text-violet-400">
                  <Terminal className="w-3.5 h-3.5" />
                  <span>AI Refinement & Auto-Fix Console</span>
                </div>
                {isModifying && (
                  <div className="flex items-center gap-1.5 text-[10px] text-emerald-400 font-mono">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
                    <span>AI Stream Active</span>
                  </div>
                )}
              </div>

              {/* Console log outputs */}
              <div className="flex-1 p-3 overflow-y-auto font-mono text-xs text-zinc-400 space-y-1 bg-black/40">
                {modifyStatus.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-zinc-600 gap-1.5">
                    <Sparkles className="w-5 h-5 text-zinc-700" />
                    <span>No active logs. Ask the AI modifier below to edit code.</span>
                  </div>
                ) : (
                  modifyStatus.map((log, i) => (
                    <div
                      key={i}
                      className={
                        log.startsWith("❌")
                          ? "text-rose-400 font-medium animate-pulse"
                          : log.startsWith("✔")
                          ? "text-emerald-400 font-medium"
                          : log.includes("[Auto-Healer]")
                          ? "text-rose-300 font-bold"
                          : log.includes("[System]")
                          ? "text-indigo-400 font-medium"
                          : "text-zinc-300"
                      }
                    >
                      {log}
                    </div>
                  ))
                )}
                <div ref={terminalEndRef} />
              </div>

              {/* Refinement input box */}
              <form
                onSubmit={handleAIRefine}
                className="p-3 border-t border-white/5 bg-[#050508] flex items-center gap-2 flex-shrink-0"
              >
                <div className="relative flex-1">
                  <input
                    type="text"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    disabled={isModifying}
                    placeholder={
                      isModifying
                        ? "AI Agent is compiling changes, please wait..."
                        : "Ask AI to modify portfolio (e.g. 'Add a skills progress bar', 'change styling to neon-pink theme')"
                    }
                    className="w-full px-4 py-2.5 pl-10 rounded-lg border border-white/5 bg-white/5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-violet-500/50 focus:ring-1 focus:ring-violet-500/20 transition-all font-sans"
                  />
                  <Sparkles className="absolute left-3.5 top-3 w-4 h-4 text-violet-500" />
                </div>
                <button
                  type="submit"
                  disabled={isModifying || !prompt.trim()}
                  className="px-4 py-2.5 rounded-lg bg-violet-600 hover:bg-violet-500 disabled:bg-white/5 text-white disabled:text-zinc-600 font-semibold text-xs flex items-center gap-1.5 transition-all shadow-md active:scale-95 flex-shrink-0"
                >
                  {isModifying ? (
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <>
                      <Sparkles className="w-3.5 h-3.5" />
                      Refine Layout
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>

          {/* Right Preview Frame */}
          <div className="flex flex-col w-[48%] border-l border-white/5 h-full bg-[#050507] overflow-hidden min-w-0">
            <div className="flex items-center justify-between px-4 py-2 bg-[#070709] border-b border-white/5 h-11 flex-shrink-0 select-none">
              <div className="flex items-center gap-2">
                <MonitorPlay className="w-4 h-4 text-emerald-400 animate-pulse" />
                <span className="text-xs font-semibold text-zinc-300">Live Application Preview</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                <span className="text-[10px] text-zinc-400 font-mono">Hot Reloading</span>
              </div>
            </div>
            
            <div className="flex-1 bg-[#09090b] relative">
              <SandpackPreview
                showNavigator={false}
                showOpenInCodeSandbox={false}
                className="w-full h-full border-none! rounded-none! overflow-hidden bg-transparent!"
              />
            </div>
          </div>

        </SandpackLayout>
      </div>
    </div>
  );
}

export default function SandpackWorkspace({
  initialFiles,
  onReset,
}: SandpackWorkspaceProps) {
  // Convert backend file paths (e.g. pages/portfolio.tsx) to Sandpack paths (e.g. /pages/portfolio.tsx)
  const sandpackFiles: Record<string, string> = {};
  
  Object.entries(initialFiles).forEach(([path, code]) => {
    const formattedPath = path.startsWith("/") ? path : `/${path}`;
    sandpackFiles[formattedPath] = code;
  });

  // Inject App.js with our customized ErrorBoundary wrapper to capture sandbox runtime exceptions and post them back for auto-healing!
  sandpackFiles["/App.js"] = `import React from 'react';
import Portfolio from "./pages/portfolio";
import "./styles/globals.css";

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: '' };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error: error.message };
  }
  componentDidCatch(error) {
    try {
      window.parent.postMessage({ type: 'sandpack-error', error: error.message }, '*');
    } catch(e) {}
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{background:'#09090b',color:'#ef4444',minHeight:'100vh',display:'flex',alignItems:'center',justifyContent:'center',padding:'2rem',fontFamily:'monospace'}}>
          <div style={{maxWidth:'600px',textAlign:'center'}}>
            <h2 style={{fontSize:'1.25rem',marginBottom:'0.75rem',color:'#f43f5e'}}>Runtime Error Detected</h2>
            <p style={{color:'#facc15',fontSize:'0.85rem',lineHeight:'1.5'}}>{this.state.error}</p>
            <p style={{color:'#71717a',marginTop:'1.25rem',fontSize:'0.75rem'}}>AI Auto-Healer is automatically resolving this in the background...</p>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function App() {
  return (
    <ErrorBoundary>
      <div className="bg-neutral-950 text-neutral-50 min-h-screen">
        <Portfolio />
      </div>
    </ErrorBoundary>
  );
}
`;

  // Inject a .babelrc to support private class methods used by complex React Bits components
  sandpackFiles["/.babelrc"] = JSON.stringify({
    plugins: [
      "@babel/plugin-proposal-class-properties",
      "@babel/plugin-proposal-private-methods"
    ]
  }, null, 2);

  // Parse dynamic dependencies from the generated package.json
  let dynamicDependencies = {};
  try {
    if (sandpackFiles["/package.json"]) {
      const pkg = JSON.parse(sandpackFiles["/package.json"]);
      if (pkg.dependencies) {
        dynamicDependencies = pkg.dependencies;
      }
    }
  } catch (e) {
    console.error("Failed to parse package.json dependencies", e);
  }

  return (
    <SandpackProvider
      template="react-ts"
      files={sandpackFiles}
      options={{
        visibleFiles: ["/pages/portfolio.tsx"],
        activeFile: "/pages/portfolio.tsx",
        externalResources: ["https://cdn.tailwindcss.com"],
      }}
      customSetup={{
        dependencies: {
          "react": "^18.2.0",
          "react-dom": "^18.2.0",
          "lucide-react": "^0.263.1",
          "framer-motion": "^10.16.4",
          "clsx": "^2.0.0",
          "tailwind-merge": "^1.14.0",
          "tailwindcss": "^3.4.1",
          "@babel/plugin-proposal-class-properties": "^7.18.6",
          "@babel/plugin-proposal-private-methods": "^7.18.6",
          ...dynamicDependencies,
        },
      }}
    >
      <WorkspaceInner onReset={onReset} />
    </SandpackProvider>
  );
}
