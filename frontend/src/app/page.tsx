"use client";

import React, { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  FileText,
  Sparkles,
  ArrowRight,
  Terminal as TerminalIcon,
  ShieldCheck,
  AlertCircle,
  FileCode,
  Compass,
  Cpu,
  RefreshCw,
} from "lucide-react";
import SandpackWorkspace from "@/components/SandpackWorkspace";

// Custom inline SVG icons for brands removed in latest Lucide React
const GithubIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    viewBox="0 0 24 24"
    width="24"
    height="24"
    stroke="currentColor"
    strokeWidth="2"
    fill="none"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
    <path d="M9 18c-4.51 2-5-2-7-2" />
  </svg>
);

const LinkedinIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    viewBox="0 0 24 24"
    width="24"
    height="24"
    stroke="currentColor"
    strokeWidth="2"
    fill="none"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
    <rect x="2" y="9" width="4" height="12" />
    <circle cx="4" cy="4" r="2" />
  </svg>
);

type ViewMode = "setup" | "generating" | "workspace";

export default function Home() {
  const [viewMode, setViewMode] = useState<ViewMode>("setup");
  
  // Form values
  const [githubUrl, setGithubUrl] = useState("");
  const [linkedinUrl, setLinkedinUrl] = useState("");
  const [cvFile, setCvFile] = useState<File | null>(null);
  
  // Drag and drop state
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // SSE & progress states
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("Initiating systems...");
  const [logs, setLogs] = useState<string[]>([]);
  const [errorMsg, setErrorMsg] = useState("");
  const [generatedFiles, setGeneratedFiles] = useState<Record<string, string> | null>(null);

  // Drag and drop handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type === "application/pdf") {
        setCvFile(file);
      } else {
        alert("Please drop a valid PDF document.");
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setCvFile(e.target.files[0]);
    }
  };

  // SSE Stream Generator Fetcher
  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!githubUrl && !linkedinUrl && !cvFile) {
      setErrorMsg("Please provide at least a GitHub profile, LinkedIn URL, or CV file to synthesize.");
      return;
    }

    setErrorMsg("");
    setViewMode("generating");
    setProgress(5);
    setStatusMessage("Connecting to multi-agent generator node...");
    setLogs(["[System] Initializing connection to LangGraph backend server..."]);

    try {
      const formData = new FormData();
      if (githubUrl) formData.append("github_url", githubUrl);
      if (linkedinUrl) formData.append("linkedin_url", linkedinUrl);
      if (cvFile) formData.append("cv_file", cvFile);

      const response = await fetch("http://localhost:8000/api/generate", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server connection failed (code ${response.status})`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) {
        throw new Error("Event stream is not readable by client browser.");
      }

      let buffer = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || ""; // Save partial chunk

        for (const line of lines) {
          if (line.trim().startsWith("data: ")) {
            const dataStr = line.trim().slice(6);
            if (!dataStr) continue;

            try {
              const parsed = JSON.parse(dataStr);
              
              if (parsed.status) {
                setStatusMessage(parsed.status);
                setLogs((prev) => [...prev, `[Agent] ${parsed.status}`]);
              }
              if (parsed.progress) {
                setProgress(parsed.progress);
              }

              // On complete, save the project files and open sandbox!
              if (parsed.html && parsed.status === "complete") {
                setLogs((prev) => [...prev, "[System] Multi-Agent synthesis completed. Exporting portfolio files..."]);
                const filesObject = JSON.parse(parsed.html);
                setGeneratedFiles(filesObject);
                
                // Wait briefly for logs visualization, then animate workspace entrance
                setTimeout(() => {
                  setViewMode("workspace");
                }, 1200);
              }
            } catch (err) {
              console.error("Stream parse error", err);
            }
          }
        }
      }
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || "Failed to generate portfolio. Make sure your local API is running.");
      setViewMode("setup");
    }
  };

  const handleReset = () => {
    setGithubUrl("");
    setLinkedinUrl("");
    setCvFile(null);
    setGeneratedFiles(null);
    setProgress(0);
    setLogs([]);
    setViewMode("setup");
  };

  // Setup View Components
  return (
    <div className="flex-1 flex flex-col min-h-screen relative overflow-x-hidden bg-[#030303]">
      
      {/* Decorative subtle background grid & glows */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#111115_1px,transparent_1px),linear-gradient(to_bottom,#111115_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none z-0" />
      
      <AnimatePresence mode="wait">
        
        {/* State 1: SETUP PANEL */}
        {viewMode === "setup" && (
          <motion.main
            key="setup-pane"
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.4 }}
            className="flex-1 flex flex-col items-center justify-center px-4 py-12 md:py-24 max-w-4xl mx-auto w-full z-10"
          >
            {/* Logo Badge */}
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-violet-500/20 bg-violet-500/10 text-violet-400 text-xs font-semibold tracking-wide mb-6">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Next.js Agentic Developer Environment</span>
            </div>

            {/* Typography Header */}
            <div className="text-center mb-10 space-y-4">
              <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-white leading-none">
                Generate Premium <br />
                <span className="gradient-text">Portfolio Sandboxes</span>
              </h1>
              <p className="max-w-xl mx-auto text-zinc-400 text-sm md:text-base font-medium">
                Provide GitHub details, LinkedIn profiles, or upload your resume PDF. Cooperative AI agents will scrape, analyze, construct, and boot a fully customizable Next.js sandbox project in seconds.
              </p>
            </div>

            {/* Inputs Panel Card */}
            <div className="w-full glass-panel rounded-2xl p-6 md:p-8 relative">
              <div className="absolute top-0 right-10 w-24 h-1 bg-gradient-to-r from-violet-500 to-emerald-400 rounded-full" />
              
              <form onSubmit={handleGenerate} className="space-y-6">
                
                {/* Visual Error Message Box */}
                {errorMsg && (
                  <div className="flex items-start gap-3 p-3.5 rounded-lg border border-red-500/20 bg-red-500/10 text-rose-400 text-xs font-medium">
                    <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <p>{errorMsg}</p>
                  </div>
                )}

                {/* Input Fields */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  {/* GitHub Input */}
                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-zinc-400 tracking-wider uppercase block">
                      GitHub Profile URL
                    </label>
                    <div className="relative group">
                      <input
                        type="url"
                        value={githubUrl}
                        onChange={(e) => setGithubUrl(e.target.value)}
                        placeholder="e.g. https://github.com/octocat"
                        className="w-full px-4 py-3 pl-11 rounded-xl border border-white/5 bg-white/5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-violet-500/50 focus:ring-1 focus:ring-violet-500/20 transition-all font-sans group-hover:border-white/10"
                      />
                      <GithubIcon className="absolute left-3.5 top-3.5 w-4 h-4 text-zinc-500 group-focus-within:text-violet-400 transition-colors" />
                    </div>
                  </div>

                  {/* LinkedIn Input */}
                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-zinc-400 tracking-wider uppercase block">
                      LinkedIn URL (Optional)
                    </label>
                    <div className="relative group">
                      <input
                        type="url"
                        value={linkedinUrl}
                        onChange={(e) => setLinkedinUrl(e.target.value)}
                        placeholder="e.g. https://linkedin.com/in/octocat"
                        className="w-full px-4 py-3 pl-11 rounded-xl border border-white/5 bg-white/5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-violet-500/50 focus:ring-1 focus:ring-violet-500/20 transition-all font-sans group-hover:border-white/10"
                      />
                      <LinkedinIcon className="absolute left-3.5 top-3.5 w-4 h-4 text-zinc-500 group-focus-within:text-violet-400 transition-colors" />
                    </div>
                  </div>
                </div>

                {/* PDF Drag and Drop Area */}
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-zinc-400 tracking-wider uppercase block">
                    Upload CV (PDF)
                  </label>
                  <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                    className={`border border-dashed rounded-xl p-6 md:p-8 text-center cursor-pointer transition-all flex flex-col items-center justify-center gap-3 relative overflow-hidden select-none ${
                      isDragOver
                        ? "border-violet-500 bg-violet-500/5"
                        : cvFile
                        ? "border-emerald-500/40 bg-emerald-500/[0.02]"
                        : "border-white/10 bg-white/[0.01] hover:border-white/20 hover:bg-white/[0.02]"
                    }`}
                  >
                    <input
                      type="file"
                      ref={fileInputRef}
                      onChange={handleFileChange}
                      accept="application/pdf"
                      className="hidden"
                    />
                    
                    {cvFile ? (
                      <>
                        <div className="relative flex items-center justify-center w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-400">
                          <FileText className="w-6 h-6" />
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-zinc-200">{cvFile.name}</p>
                          <p className="text-[10px] text-zinc-500 mt-1 font-mono">
                            {(cvFile.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setCvFile(null);
                          }}
                          className="px-2.5 py-1 rounded bg-rose-500/10 border border-rose-500/20 hover:bg-rose-500/20 text-[10px] font-semibold text-rose-400 transition-all mt-1"
                        >
                          Remove CV
                        </button>
                      </>
                    ) : (
                      <>
                        <div className="relative flex items-center justify-center w-12 h-12 rounded-xl bg-zinc-800 text-zinc-400 group-hover:text-zinc-200">
                          <FileText className="w-5 h-5" />
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-zinc-300">
                            Drag & drop your resume PDF here, or <span className="text-violet-400 font-medium hover:underline">browse</span>
                          </p>
                          <p className="text-[10px] text-zinc-500 mt-1">Supports standard PDF formats up to 10MB</p>
                        </div>
                      </>
                    )}
                  </div>
                </div>

                {/* Submit Action Button */}
                <div className="pt-2">
                  <button
                    type="submit"
                    className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-gradient-to-r from-violet-600 to-emerald-500 hover:from-violet-500 hover:to-emerald-400 text-xs font-semibold text-white tracking-wider shadow-lg hover:shadow-violet-600/10 transition-all duration-300 cursor-pointer active:scale-[0.99]"
                  >
                    <Cpu className="w-4 h-4" />
                    <span>SYNTHESIZE NEXT.JS PORTFOLIO</span>
                    <ArrowRight className="w-4 h-4 ml-1" />
                  </button>
                </div>

              </form>
            </div>

            {/* Bottom Footer Info Badges */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mt-12 w-full text-center">
              <div className="p-4 rounded-xl bg-white/[0.01] border border-white/5 flex flex-col items-center">
                <Compass className="w-5 h-5 text-emerald-400 mb-2" />
                <span className="text-xs font-bold text-zinc-200 block">Agent Scraping</span>
                <span className="text-[10px] text-zinc-500 mt-1">Gathers context from GitHub repositories and public URLs automatically.</span>
              </div>
              <div className="p-4 rounded-xl bg-white/[0.01] border border-white/5 flex flex-col items-center">
                <FileCode className="w-5 h-5 text-violet-400 mb-2" />
                <span className="text-xs font-bold text-zinc-200 block">In-browser Compiler</span>
                <span className="text-[10px] text-zinc-500 mt-1">Compiles full frameworks instantly in-browser using isolated sandboxes.</span>
              </div>
              <div className="p-4 rounded-xl bg-white/[0.01] border border-white/5 flex flex-col items-center">
                <ShieldCheck className="w-5 h-5 text-sky-400 mb-2" />
                <span className="text-xs font-bold text-zinc-200 block">AI Refinements</span>
                <span className="text-[10px] text-zinc-500 mt-1">Refine and rewrite generated elements in real time with our live agents.</span>
              </div>
            </div>
          </motion.main>
        )}

        {/* State 2: GENERATION TIMELINE */}
        {viewMode === "generating" && (
          <motion.div
            key="generating-pane"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            className="flex-1 flex flex-col items-center justify-center p-6 max-w-2xl mx-auto w-full z-10"
          >
            {/* Main generation card */}
            <div className="w-full glass-panel rounded-2xl p-6 md:p-8 space-y-6 text-center shadow-2xl relative overflow-hidden">
              <div className="absolute -top-12 -left-12 w-28 h-28 rounded-full bg-violet-600/10 blur-xl animate-pulse" />
              <div className="absolute -bottom-12 -right-12 w-28 h-28 rounded-full bg-emerald-500/10 blur-xl animate-pulse" />
              
              {/* Spinner */}
              <div className="relative inline-flex items-center justify-center">
                <div className="w-16 h-16 rounded-full border border-violet-500/20 border-t-violet-500 animate-spin" />
                <TerminalIcon className="absolute w-5 h-5 text-violet-400 animate-pulse" />
              </div>

              {/* Status Header */}
              <div className="space-y-1.5">
                <h2 className="text-lg font-bold text-white tracking-wide">Multi-Agent Synthesis Nodes Active</h2>
                <p className="text-xs text-zinc-400 font-mono h-4 select-none">{statusMessage}</p>
              </div>

              {/* Horizontal visual progress nodes */}
              <div className="flex items-center justify-between px-6 py-4 rounded-xl bg-black/40 border border-white/5 text-[10px] font-mono text-zinc-400 select-none">
                <div className={`flex flex-col items-center gap-1 ${progress >= 10 ? "text-violet-400 font-bold" : "text-zinc-600"}`}>
                  <div className={`w-3.5 h-3.5 rounded-full flex items-center justify-center ${progress >= 10 ? "bg-violet-500 text-black" : "bg-zinc-800"}`}>1</div>
                  <span>Scraper</span>
                </div>
                <div className="w-10 h-0.5 bg-zinc-800 relative">
                  <div className="absolute top-0 left-0 h-full bg-gradient-to-r from-violet-500 to-emerald-400" style={{ width: progress > 15 ? "100%" : "0%" }} />
                </div>
                
                <div className={`flex flex-col items-center gap-1 ${progress >= 40 ? "text-violet-400 font-bold" : "text-zinc-600"}`}>
                  <div className={`w-3.5 h-3.5 rounded-full flex items-center justify-center ${progress >= 40 ? "bg-violet-500 text-black" : "bg-zinc-800"}`}>2</div>
                  <span>Analyzer</span>
                </div>
                <div className="w-10 h-0.5 bg-zinc-800 relative">
                  <div className="absolute top-0 left-0 h-full bg-gradient-to-r from-violet-500 to-emerald-400" style={{ width: progress > 55 ? "100%" : "0%" }} />
                </div>
                
                <div className={`flex flex-col items-center gap-1 ${progress >= 60 ? "text-violet-400 font-bold" : "text-zinc-600"}`}>
                  <div className={`w-3.5 h-3.5 rounded-full flex items-center justify-center ${progress >= 60 ? "bg-violet-500 text-black" : "bg-zinc-800"}`}>3</div>
                  <span>Writer</span>
                </div>
                <div className="w-10 h-0.5 bg-zinc-800 relative">
                  <div className="absolute top-0 left-0 h-full bg-gradient-to-r from-violet-500 to-emerald-400" style={{ width: progress > 75 ? "100%" : "0%" }} />
                </div>
                
                <div className={`flex flex-col items-center gap-1 ${progress >= 80 ? "text-violet-400 font-bold" : "text-zinc-600"}`}>
                  <div className={`w-3.5 h-3.5 rounded-full flex items-center justify-center ${progress >= 80 ? "bg-violet-500 text-black" : "bg-zinc-800"}`}>4</div>
                  <span>Generator</span>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="space-y-1">
                <div className="w-full h-1.5 rounded-full bg-zinc-900 border border-white/5 overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-violet-600 to-emerald-500"
                    initial={{ width: "0%" }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
                <div className="flex justify-between items-center text-[10px] text-zinc-500 font-mono">
                  <span>Progress Log Matrix</span>
                  <span>{progress}% complete</span>
                </div>
              </div>

              {/* simulated logs terminal */}
              <div className="h-48 rounded-xl bg-black border border-white/5 p-4 text-left overflow-y-auto font-mono text-xs text-zinc-400 space-y-1.5 scrollbar-thin select-text">
                {logs.map((log, index) => (
                  <div key={index} className={log.includes("[System]") ? "text-violet-400" : "text-zinc-300"}>
                    <span className="text-zinc-600 mr-2">{">"}</span>
                    {log}
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {/* State 3: WORKSPACE SANDBOX */}
        {viewMode === "workspace" && generatedFiles && (
          <motion.div
            key="workspace-pane"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex-1 w-full h-screen relative"
          >
            <SandpackWorkspace initialFiles={generatedFiles} onReset={handleReset} />
          </motion.div>
        )}

      </AnimatePresence>
    </div>
  );
}
