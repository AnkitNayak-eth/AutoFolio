from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, TypedDict, Annotated
import operator, os, json, re, requests, sys, time

# Force stdout/stderr to use utf-8
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI
from langgraph.graph import StateGraph, END
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
import PyPDF2, io

load_dotenv()

# ── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(title="AI Portfolio Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── LLM (NVIDIA API – Gemma) ────────────────────────────────────────────────

def get_llm(max_tokens=2000, temperature=0.7, model_name="meta/llama-3.3-70b-instruct"):
    return ChatOpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=os.getenv("NVIDIA_API_KEY"),
        model=model_name,
        temperature=temperature,
        timeout=180.0,
        request_timeout=180.0,
        max_retries=2,
        extra_body={"max_tokens": max_tokens},
    )

class PortfolioState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    github_data: str
    linkedin_url: str
    cv_text: str
    profile_summary: str
    portfolio_content: str
    portfolio_code: str
    modification_request: str
    selected_components: str

# ── Helpers ──────────────────────────────────────────────────────────────────
def fetch_github_data(github_url: str) -> str:
    try:
        username = github_url.rstrip("/").split("/")[-1]
        user = requests.get(f"https://api.github.com/users/{username}", timeout=10).json()
        repos = requests.get(
            f"https://api.github.com/users/{username}/repos?sort=stars&per_page=10",
            timeout=10,
        ).json()
        return json.dumps({
            "name": user.get("name", username),
            "bio": user.get("bio", ""),
            "avatar": user.get("avatar_url", ""),
            "location": user.get("location", ""),
            "company": user.get("company", ""),
            "blog": user.get("blog", ""),
            "public_repos": user.get("public_repos", 0),
            "followers": user.get("followers", 0),
            "repos": [
                {"name": r["name"], "desc": r.get("description", ""), "lang": r.get("language", ""), "stars": r["stargazers_count"], "url": r["html_url"]}
                for r in repos if isinstance(r, dict)
            ],
        })
    except Exception:
        return "GitHub data unavailable"

def extract_pdf_text(raw: bytes) -> str:
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(raw))
        return "\n".join(p.extract_text() or "" for p in reader.pages)
    except Exception:
        return "Could not extract PDF text"

def strip_fences(text: str) -> str:
    match = re.search(r"```[a-zA-Z]*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text.strip())
    text = re.sub(r"\n?```$", "", text.strip())
    return text.strip()

def fix_jsx_wrapper(code: str) -> str:
    """Ensure the component's return statement wraps everything in a React fragment <>....</>.
    This fixes 'Adjacent JSX elements must be wrapped in an enclosing tag' errors
    caused by <style> and <div> being siblings."""
    # Strategy: find `return (` and check if the first JSX element after it is <style>
    # If so, wrap the entire return body in <> ... </>
    
    # Check if code already uses fragments
    if '<>' in code and '</>' in code:
        return code
    
    # Find the return statement and wrap its content in a fragment
    # Match: return ( ... <style> ... </div> ... )
    pattern = r'(return\s*\(\s*)\n(\s*)(<style>)'
    match = re.search(pattern, code)
    if match:
        indent = match.group(2)
        code = re.sub(
            pattern,
            f'{match.group(1)}\n{indent}<>\n{indent}{match.group(3)}',
            code,
            count=1
        )
        # Find the closing `)` of the return statement and insert </> before it
        # We need to find the last `);` or the closing `)` that ends the return
        # Find the pattern of closing div + closing paren
        code = re.sub(
            r'(\s*</div>\s*)\n(\s*)\)',
            r'\1\n' + indent + '</>\n\2)',
            code,
            count=1  # only the LAST occurrence
        )
        # Actually, the above might match intermediate </div>. Let's use a more robust approach.
        # Find the LAST `)` that closes the return and place </> before it.
    
    # Fallback: more robust approach - just wrap the entire return body
    # If we detect <style> followed by <div as direct children of return
    if '<>' not in code:
        # Simple regex: after return(, inject <> before <style, and </> before final )
        lines = code.split('\n')
        new_lines = []
        in_return = False
        return_depth = 0
        inserted_open = False
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            if re.match(r'return\s*\(', stripped):
                in_return = True
                return_depth = 1
                new_lines.append(line)
                # Get the indentation of the next line
                if i + 1 < len(lines):
                    next_indent = len(lines[i+1]) - len(lines[i+1].lstrip())
                    new_lines.append(' ' * next_indent + '<>')
                    inserted_open = True
                continue
            
            if in_return and inserted_open:
                # Count parens to find the end of return()
                for ch in stripped:
                    if ch == '(':
                        return_depth += 1
                    elif ch == ')':
                        return_depth -= 1
                
                if return_depth <= 0:
                    # This line contains the closing ) of return
                    indent_here = len(line) - len(line.lstrip())
                    new_lines.append(' ' * (indent_here + 2) + '</>')
                    new_lines.append(line)
                    in_return = False
                    continue
            
            new_lines.append(line)
        
        if inserted_open:
            code = '\n'.join(new_lines)
    
    return code



# ── Agent Nodes ──────────────────────────────────────────────────────────────
async def profile_analyzer(state: PortfolioState):
    print("[Agent 1 - Profile Analyzer] Starting...")
    t0 = time.time()
    llm = get_llm(temperature=0.1, model_name="meta/llama-3.1-8b-instruct") # Fast, deterministic
    
    prompt = (
        "Analyze the following data for a developer portfolio. Create a concise summary (max 300 words) of their core identity, main skills, and key projects.\n\n"
        f"GitHub:\n{state.get('github_data', '')}\n\n"
        f"LinkedIn/Other:\n{state.get('linkedin_url', '')}\n\n"
        f"CV/Resume:\n{state.get('cv_text', '')}"
    )
    resp = await llm.ainvoke([
        SystemMessage(content="You are an expert tech recruiter and portfolio strategist."),
        HumanMessage(content=prompt),
    ])
    print(f"[Agent 1 - Profile Analyzer] Done in {time.time()-t0:.1f}s")
    return {"profile_summary": resp.content}

async def content_writer(state: PortfolioState):
    print("[Agent 2 - Content Writer] Starting...")
    t0 = time.time()
    llm = get_llm(temperature=0.7, model_name="meta/llama-3.1-8b-instruct") # Fast, creative
    prompt = (
        "You are a portfolio copywriter. Write modern, impactful copy quickly. Do not add filler text.\n\n"
        "Using this profile JSON, write compelling portfolio copy:\n"
        "1) Hero headline + subtitle\n2) About Me (3-4 sentences)\n"
        "3) Skills with categories\n4) Project cards\n5) Experience timeline\n"
        "6) Contact CTA\n\n" + state.get("profile_summary", "")
    )
    resp = await llm.ainvoke([
        HumanMessage(content=prompt),
    ])
    print(f"[Agent 2 - Content Writer] Done in {time.time()-t0:.1f}s")
    return {"portfolio_content": resp.content}



BASE_FILES = {
    "pages/_app.tsx": """import '../styles/globals.css'
import type { AppProps } from 'next/app'
import React from 'react'

class ErrorBoundary extends React.Component<{children: React.ReactNode}, {hasError: boolean, error: string}> {
  constructor(props: any) {
    super(props)
    this.state = { hasError: false, error: '' }
  }
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error: error.message }
  }
  componentDidCatch(error: Error) {
    try {
      window.parent.postMessage({ type: 'sandpack-error', error: error.message }, '*')
    } catch(e) {}
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{background:'#0a0a0a',color:'#ef4444',minHeight:'100vh',display:'flex',alignItems:'center',justifyContent:'center',padding:'2rem',fontFamily:'monospace'}}>
          <div style={{maxWidth:'600px',textAlign:'center'}}>
            <h2 style={{fontSize:'1.5rem',marginBottom:'1rem'}}>Runtime Error Detected</h2>
            <p style={{color:'#fbbf24',fontSize:'0.875rem'}}>{this.state.error}</p>
            <p style={{color:'#737373',marginTop:'1rem',fontSize:'0.75rem'}}>Auto-Healer is fixing this...</p>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

export default function MyApp({ Component, pageProps }: AppProps) {
  return (
    <ErrorBoundary>
      <div className=\"bg-neutral-950 text-neutral-50 min-h-screen\">
        <Component {...pageProps} />
      </div>
    </ErrorBoundary>
  )
}""",
    "pages/index.js": """import Portfolio from './portfolio';
export default Portfolio;""",
    "styles/globals.css": """@tailwind base;
@tailwind components;
@tailwind utilities;""",
    "tailwind.config.js": """/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}""",
    "postcss.config.js": """module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}""",
    "tsconfig.json": """{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules"]
}""",
    "package.json": """{
  "name": "portfolio-sandbox",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "next": "13.4.19",
    "lucide-react": "^0.263.1",
    "framer-motion": "^10.16.4",
    "clsx": "^2.0.0",
    "tailwind-merge": "^1.14.0",
    "typescript": "^5.0.0",
    "@types/react": "^18.0.0",
    "@types/node": "^20.0.0",
    "tailwindcss": "^3.4.1",
    "postcss": "^8.4.35",
    "autoprefixer": "^10.4.17",
    "react-icons": "^4.11.0",
    "ogl": "^1.0.10",
    "three": "^0.160.0",
    "@react-three/fiber": "^8.15.12",
    "@react-three/drei": "^9.96.1",
    "gsap": "^3.12.5"
  }
}"""
}
SAFE_LUCIDE_ICONS = {
    "Mail", "Github", "Linkedin", "ExternalLink", "ChevronDown", "ChevronUp",
    "ChevronRight", "ChevronLeft", "ArrowRight", "ArrowLeft", "ArrowUpRight",
    "Code", "Code2", "Briefcase", "User", "Star", "Heart", "MapPin", "Phone",
    "Globe", "Terminal", "Layers", "Zap", "Send", "Menu", "X", "Check",
    "Calendar", "Clock", "Download", "Upload", "Eye", "Search", "Settings",
    "Home", "Award", "BookOpen", "Coffee", "Cpu", "Database", "FileText",
    "Folder", "GitBranch", "GitCommit", "GitPullRequest", "Hash", "Image",
    "Layout", "Link", "Lock", "Monitor", "Package", "Palette", "PenTool",
    "Server", "Shield", "Smartphone", "Sparkles", "Target", "Tv", "Wifi",
    "Activity", "AlertCircle", "Archive", "BarChart", "Bell", "Box",
    "Camera", "Cast", "Cloud", "Codepen", "Command", "Compass", "Copy",
    "Disc", "DollarSign", "Droplet", "Edit", "Film", "Filter", "Flag",
    "Headphones", "HelpCircle", "Hexagon", "Inbox", "Info", "Key",
    "LifeBuoy", "List", "Loader", "Map", "MessageCircle", "MessageSquare",
    "Mic", "Moon", "MoreHorizontal", "MoreVertical", "Move", "Music",
    "Navigation", "Octagon", "Paperclip", "Pause", "PieChart", "Play",
    "Plus", "Pocket", "Power", "Printer", "Radio", "RefreshCw", "Repeat",
    "RotateCw", "Rss", "Save", "Scissors", "Share", "ShoppingCart",
    "Sidebar", "SkipBack", "SkipForward", "Slash", "Sliders", "Speaker",
    "Square", "Sun", "Tablet", "Tag", "ThumbsUp", "ToggleLeft", "Tool",
    "Trash", "Trello", "TrendingUp", "Triangle", "Truck", "Twitter",
    "Umbrella", "Underline", "Unlock", "UserCheck", "UserPlus", "Users",
    "Video", "Volume", "Watch", "Wind", "ZoomIn", "ZoomOut",
    "Rocket", "GraduationCap", "Wrench", "Flame", "Bot", "Brain",
}

def sanitize_imports(code: str) -> str:
    """Remove import lines that reference unknown libraries or non-existent lucide icons."""
    lines = code.split("\n")
    clean_lines = []
    
    ALLOWED_MODULES = {"react", "framer-motion", "lucide-react", "ogl", "three", "@react-three/fiber", "@react-three/drei", "three/src/math/MathUtils.js", "gsap", "react-icons/si"}
    
    for line in lines:
        stripped = line.strip()
        
        # Check if it's an import line
        if stripped.startswith("import "):
            # Extract the module name from `from 'xxx'` or `from "xxx"`
            from_match = re.search(r"""from\s+['"]([^'"]+)['"]""", stripped)
            if from_match:
                module = from_match.group(1)
                # Allow relative imports and known modules
                if module.startswith(".") or module.startswith("/"):
                    clean_lines.append(line)
                    continue
                if module not in ALLOWED_MODULES:
                    print(f"[Sanitizer] Stripped bad import: {stripped}")
                    continue
                # If it's lucide-react, validate icon names
                if module == "lucide-react":
                    icons_match = re.search(r"import\s*{([^}]+)}", stripped)
                    if icons_match:
                        icons = [i.strip() for i in icons_match.group(1).split(",") if i.strip()]
                        valid_icons = [i for i in icons if i in SAFE_LUCIDE_ICONS]
                        if not valid_icons:
                            print(f"[Sanitizer] Stripped empty lucide import: {stripped}")
                            continue
                        if len(valid_icons) != len(icons):
                            bad = set(icons) - set(valid_icons)
                            print(f"[Sanitizer] Removed invalid lucide icons: {bad}")
                            clean_lines.append(f"import {{ {', '.join(valid_icons)} }} from 'lucide-react';")
                            continue
            clean_lines.append(line)
        else:
            clean_lines.append(line)
    
    return "\n".join(clean_lines)

def assemble_portfolio_tsx(layout_data: dict) -> str:
    import random
    import design_templates

    bg = layout_data.get("background", "ShapeGrid")
    hero_effect = layout_data.get("hero_effect", None)
    sections = layout_data.get("sections", [])

    # Track which components are actually used so we only import what's needed
    all_names = design_templates.get_background_names() + design_templates.get_hero_names() + design_templates.get_component_names()
    used_components = set()
    if bg in all_names:
        used_components.add(bg)
    if hero_effect in all_names:
        used_components.add(hero_effect)
    for section in sections:
        t = section.get("type", "")
        if t in all_names:
            used_components.add(t)

    imports = ["import React from 'react';"]
    for name in used_components:
        imports.append(f"import {name} from '../components/{name}';")

    jsx_elements = []

    # ── Full-screen background (fixed, behind everything) ──
    if bg == "ShapeGrid":
        speed = round(random.uniform(0.1, 0.8), 2)
        shape = random.choice(["square", "hexagon", "circle", "triangle"])
        jsx_elements.append(f"""
      <div className="fixed inset-0 z-0 opacity-30 pointer-events-none">
        <ShapeGrid speed={{{speed}}} squareSize={{50}} direction="diagonal" borderColor="#ffffff10" hoverFillColor="#a855f7" shape="{shape}" hoverTrailAmount={{5}} />
      </div>""")
    elif bg == "DotField":
        dotRadius = round(random.uniform(1.0, 2.0), 1)
        dotSpacing = random.choice([10, 12, 14, 16])
        sparkle = str(random.choice([True, False])).lower()
        waveAmplitude = random.choice([0, 10, 20])
        jsx_elements.append(f"""
      <div className="fixed inset-0 z-0 opacity-50 pointer-events-none">
        <DotField dotRadius={{{dotRadius}}} dotSpacing={{{dotSpacing}}} bulgeStrength={{67}} glowRadius={{160}} sparkle={{{sparkle}}} waveAmplitude={{{waveAmplitude}}} />
      </div>""")

    # ── Hero section (relative container with optional hero effect) ──
    jsx_elements.append("""
      <div className="relative min-h-screen flex items-center justify-center overflow-hidden">""")

    # Hero effect overlay (absolute, inside hero container)
    if hero_effect == "RippleGrid":
        rippleIntensity = round(random.uniform(0.02, 0.08), 3)
        gridSize = random.choice([15, 20, 25])
        jsx_elements.append(f"""
        <div className="absolute inset-0 z-0 opacity-40 mix-blend-screen">
          <RippleGrid enableRainbow={{false}} gridColor="#5227FF" rippleIntensity={{{rippleIntensity}}} gridSize={{{gridSize}}} gridThickness={{2}} mouseInteraction={{true}} />
        </div>""")
    elif hero_effect == "Lightning":
        hue = random.choice([230, 280, 190, 320])
        speed = round(random.uniform(0.5, 2.0), 1)
        intensity = round(random.uniform(0.8, 1.5), 1)
        jsx_elements.append(f"""
        <div className="absolute inset-0 z-0 opacity-80">
          <Lightning hue={{{hue}}} xOffset={{0}} speed={{{speed}}} intensity={{{intensity}}} size={{1}} />
        </div>""")
    elif hero_effect == "Beams":
        beamNumber = random.choice([8, 12, 16])
        noiseIntensity = round(random.uniform(1.0, 2.0), 2)
        rotation = random.choice([0, 45, -45])
        jsx_elements.append(f"""
        <div className="absolute inset-0 z-0 opacity-80">
          <Beams beamWidth={{2}} beamHeight={{15}} beamNumber={{{beamNumber}}} lightColor="#ffffff" speed={{2}} noiseIntensity={{{noiseIntensity}}} scale={{0.2}} rotation={{{rotation}}} />
        </div>""")
    elif hero_effect == "GradientBlinds":
        blindCount = random.choice([8, 12, 16, 20])
        noise = round(random.uniform(0.1, 0.5), 1)
        distortAmount = random.choice([0, 0.5, 1])
        colors = [
            "['#FF9FFC', '#5227FF']",
            "['#3b82f6', '#8b5cf6', '#ec4899']",
            "['#10b981', '#3b82f6']"
        ]
        gradientColors = random.choice(colors)
        jsx_elements.append(f"""
        <div className="absolute inset-0 z-0 opacity-80">
          <GradientBlinds gradientColors={{{gradientColors}}} angle={{0}} noise={{{noise}}} blindCount={{{blindCount}}} blindMinWidth={{50}} spotlightRadius={{0.5}} spotlightSoftness={{1}} spotlightOpacity={{1}} mouseDampening={{0.15}} distortAmount={{{distortAmount}}} shineDirection="left" mixBlendMode="lighten" />
        </div>""")
    elif hero_effect == "DarkVeil":
        hueShift = random.choice([0, 30, 60, 120, 180, 240, 300])
        noiseIntensity = round(random.uniform(0, 0.08), 3)
        scanlineIntensity = round(random.uniform(0, 0.15), 3)
        speed = round(random.uniform(0.3, 0.8), 2)
        scanlineFrequency = random.choice([0, 50, 100, 200])
        warpAmount = round(random.uniform(0, 0.5), 2)
        jsx_elements.append(f"""
        <div className="absolute inset-0 z-0">
          <DarkVeil hueShift={{{hueShift}}} noiseIntensity={{{noiseIntensity}}} scanlineIntensity={{{scanlineIntensity}}} speed={{{speed}}} scanlineFrequency={{{scanlineFrequency}}} warpAmount={{{warpAmount}}} resolutionScale={{1}} />
        </div>""")
    elif hero_effect == "Silk":
        speed = random.choice([3, 5, 7, 10])
        scale = round(random.uniform(0.8, 1.5), 2)
        colors = ["#7B7481", "#a855f7", "#3b82f6", "#ec4899", "#10b981", "#f59e0b"]
        color = random.choice(colors)
        noiseIntensity = round(random.uniform(0.5, 2.0), 2)
        rotation = round(random.uniform(0, 3.14), 2)
        jsx_elements.append(f"""
        <div className="absolute inset-0 z-0">
          <Silk speed={{{speed}}} scale={{{scale}}} color="{color}" noiseIntensity={{{noiseIntensity}}} rotation={{{rotation}}} />
        </div>""")
    elif hero_effect == "ColorBends":
        palettes = [
            '["#ff5c7a", "#8a5cff", "#00ffd1"]',
            '["#3b82f6", "#8b5cf6", "#ec4899"]',
            '["#10b981", "#f59e0b", "#ef4444"]',
            '["#06b6d4", "#a855f7", "#f97316"]',
            '["#ec4899", "#8b5cf6", "#06b6d4"]'
        ]
        colors = random.choice(palettes)
        rotation = random.choice([0, 45, 90, 135, 180, 270])
        speed = round(random.uniform(0.1, 0.4), 2)
        scale = round(random.uniform(0.8, 1.3), 2)
        frequency = round(random.uniform(0.5, 1.5), 2)
        warpStrength = round(random.uniform(0.5, 1.5), 2)
        intensity = round(random.uniform(1.0, 2.0), 2)
        bandWidth = random.choice([4, 6, 8])
        noise = round(random.uniform(0.05, 0.25), 3)
        jsx_elements.append(f"""
        <div className="absolute inset-0 z-0">
          <ColorBends colors={{{colors}}} rotation={{{rotation}}} speed={{{speed}}} scale={{{scale}}} frequency={{{frequency}}} warpStrength={{{warpStrength}}} mouseInfluence={{1}} noise={{{noise}}} parallax={{0.5}} iterations={{1}} intensity={{{intensity}}} bandWidth={{{bandWidth}}} transparent />
        </div>""")
    elif hero_effect == "Prism":
        hueShift = round(random.uniform(0, 3.14), 2)
        colorFrequency = round(random.uniform(0.5, 2.0), 1)
        noise = round(random.uniform(0.1, 0.6), 1)
        jsx_elements.append(f"""
        <div className="absolute inset-0 z-0 opacity-80">
          <Prism animationType="rotate" timeScale={{0.5}} height={{3.5}} baseWidth={{5.5}} scale={{3.6}} hueShift={{{hueShift}}} colorFrequency={{{colorFrequency}}} noise={{{noise}}} glow={{1}} />
        </div>""")

    # Hero text content
    hero_props = {}
    for section in sections:
        if section.get("type") == "Hero":
            hero_props = section.get("props", {})
            break

    title = hero_props.get("title", "Developer")
    subtitle = hero_props.get("subtitle", "")
    jsx_elements.append(f"""
        <nav className="absolute top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4 mx-auto max-w-7xl">
          <div className="flex items-center gap-3 text-white font-semibold text-lg">
            <div className="w-8 h-8 rounded-full bg-white text-black flex items-center justify-center font-bold tracking-tighter">A</div>
            <span className="tracking-tight">Portfolio</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-gray-400">
            <a href="#work" className="hover:text-white transition-colors">Work</a>
            <a href="#about" className="hover:text-white transition-colors">About</a>
          </div>
          <div>
            <button className="bg-white text-black px-4 py-2 rounded-lg text-sm font-bold hover:bg-gray-200 transition-colors">Contact me</button>
          </div>
        </nav>

        <div className="relative z-10 flex flex-col items-center justify-center min-h-[80vh] text-center px-4 mt-16 pointer-events-none">
          <div className="pointer-events-auto mb-8 flex items-center gap-3 px-4 py-2 rounded-full bg-white/5 border border-white/10 text-sm backdrop-blur-md shadow-2xl">
            <span className="bg-white text-black px-2.5 py-0.5 rounded-full text-xs font-bold tracking-wide">HELLO</span>
            <span className="text-gray-300 font-medium tracking-wide">Welcome to my digital space</span>
          </div>
          
          <h1 className="pointer-events-auto text-5xl md:text-7xl lg:text-[5.5rem] font-extrabold tracking-tight text-white mb-6 max-w-5xl leading-tight drop-shadow-2xl">
            {title}
          </h1>
          
          <p className="pointer-events-auto text-xl md:text-2xl text-gray-400 mb-10 max-w-3xl font-light leading-relaxed">
            {subtitle}
          </p>
          
          <div className="pointer-events-auto flex flex-col sm:flex-row items-center gap-4">
            <button className="bg-white text-black px-8 py-3.5 rounded-xl font-bold hover:bg-gray-200 transition-all hover:scale-105 active:scale-95 shadow-[0_0_30px_rgba(255,255,255,0.2)]">
              Get started
            </button>
            <button className="bg-black/40 text-white border border-white/10 px-8 py-3.5 rounded-xl font-bold hover:bg-white/10 transition-all backdrop-blur-xl">
              Learn more
            </button>
          </div>
        </div>""")

    jsx_elements.append("      </div>")

    # ── Content sections (below hero) ──
    jsx_elements.append("""
      <div className="relative z-10 p-8 max-w-5xl mx-auto">""")

    for section in sections:
        t = section.get("type", "Section")
        if t == "Hero":
            continue  # already rendered above
        props = section.get("props", {})

        if t in design_templates.get_component_names():
            # Render the actual UI component!
            jsx_elements.append(f"""
        <div className="mb-12 relative w-full overflow-hidden">
          <{t} {{...{json.dumps(props)}}} />
        </div>""")
        else:
            # Generic fallback for unknown sections
            colors = ["text-blue-400", "text-purple-400", "text-green-400", "text-pink-400"]
            color = random.choice(colors)
            jsx_elements.append(f"""
        <div className="mb-12 p-6 bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 shadow-xl hover:bg-white/10 transition-all">
          <h2 className="text-4xl font-bold mb-4 {color}">{t}</h2>
          <pre className="whitespace-pre-wrap text-sm text-gray-300">{{JSON.stringify({json.dumps(props)}, null, 2)}}</pre>
        </div>""")

    jsx_elements.append("      </div>")

    full_jsx = "\n".join(jsx_elements)

    code = "\n".join(imports) + "\n\n"
    code += "export default function Portfolio() {\n"
    code += "  return (\n"
    code += "    <div className=\"min-h-screen bg-neutral-950 text-white font-sans\">\n"
    code += full_jsx + "\n"
    code += "    </div>\n"
    code += "  );\n"
    code += "}\n"

    return code

async def code_generator(state: PortfolioState):
    print("[Agent 3 - Code Generator] Starting...")
    t0 = time.time()
    
    content = state.get("portfolio_content", "")
    
    prompt = (
        "You are an AI layout generator for a portfolio website. Based on the following portfolio content, generate a JSON object representing the page layout.\n\n"
        "PORTFOLIO CONTENT:\n" + content + "\n\n"
        "You MUST output valid JSON ONLY, no markdown, no explanation.\n"
        "The JSON should have the following structure:\n"
        "{\n"
        "  \"background\": \"DotField\", // Full-screen background — choose ONE of: 'ShapeGrid', 'DotField'\n"
        "  \"hero_effect\": \"RippleGrid\", // Hero section visual effect — choose ONE of: 'RippleGrid', 'Lightning', 'Beams', 'GradientBlinds', 'DarkVeil', 'Silk', 'ColorBends', 'Prism', or null for no effect\n"
        "  \"sections\": [\n"
        "    {\n"
        "      \"type\": \"Hero\",\n"
        "      \"props\": {\"title\": \"John Doe\", \"subtitle\": \"Frontend Engineer\"}\n"
        "    },\n"
        "    {\n"
        "      \"type\": \"MagicBento\",\n"
        "      \"props\": {\"textAutoHide\": true, \"enableSpotlight\": true}\n"
        "    },\n"
        "    {\n"
        "      \"type\": \"LogoLoop\",\n"
        "      \"props\": {\"logos\": [{\"src\": \"https://upload.wikimedia.org/wikipedia/commons/a/a7/React-icon.svg\", \"alt\": \"React\"}], \"speed\": 120}\n"
        "    },\n"
        "    {\n"
        "      \"type\": \"About\",\n"
        "      \"props\": {\"text\": \"Generic fallback section text...\"}\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "IMPORTANT: You MUST use 'MagicBento' and 'LogoLoop' component types in your sections to make the UI look good. Use generic text sections minimally.\n"
        "Keep the JSON minimal but ensure it captures the essence of the content."
    )
    
    client = AsyncOpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=os.getenv("NVIDIA_API_KEY"),
        max_retries=3,
        timeout=180.0
    )

    print("[Llama 3.3 70B] Generating JSON layout...")
    completion = await client.chat.completions.create(
        model="meta/llama-3.3-70b-instruct",
        messages=[{"role":"user","content":prompt}],
        temperature=0.3,
        max_tokens=1500,
        response_format={"type": "json_object"}
    )
    
    raw_content = completion.choices[0].message.content
    elapsed = time.time() - t0
    print(f"[Agent 3 - Code Generator] LLM responded in {elapsed:.1f}s ({len(raw_content)} chars)")
    
    # Try to parse the JSON
    try:
        layout_data = json.loads(strip_fences(raw_content))
    except Exception as e:
        print(f"Error parsing JSON: {e}. Falling back to default layout.")
        layout_data = {"background": "ShapeGrid", "hero_effect": "RippleGrid", "sections": [{"type": "Hero", "props": {"title": "Error generating layout", "subtitle": ""}}]}
        
    code = assemble_portfolio_tsx(layout_data)
    
    # Merge base files with the newly generated page
    files = BASE_FILES.copy()
    
    # Get design templates
    import design_templates
    design_files = design_templates.get_all_component_files()
    files.update(design_files)
    
    files["pages/portfolio.tsx"] = code
        
    print(f"[Agent 3 - Code Generator] Total time: {time.time()-t0:.1f}s")
    return {"portfolio_code": json.dumps(files)}

# ── Graphs ───────────────────────────────────────────────────────────────────
def build_gen_graph():
    g = StateGraph(PortfolioState)
    g.add_node("analyzer", profile_analyzer)
    g.add_node("writer", content_writer)
    g.add_node("generator", code_generator)
    g.set_entry_point("analyzer")
    g.add_edge("analyzer", "writer")
    g.add_edge("writer", "generator")
    g.add_edge("generator", END)
    return g.compile()

def build_mod_graph():
    async def modifier(state: PortfolioState):
        print("[Agent - Modifier]")
        llm = get_llm(max_tokens=3000, temperature=0.3, model_name="meta/llama-3.3-70b-instruct")
        
        existing = {}
        try:
            existing = json.loads(state.get("portfolio_code", "{}"))
        except:
            pass
        existing_code = existing.get("pages/portfolio.tsx", "")

        prompt = (
            "You are an expert Next.js developer debugging or modifying code.\n"
            "Here is the current code for `pages/portfolio.tsx`:\n\n"
            + existing_code
            + "\n\nUser request or Sandbox Error Log: " + state.get("modification_request", "")
            + "\n\nIf the user provided an error, diagnose and fix it completely. If they provided a feature request, implement it beautifully using Tailwind and Framer Motion.\n"
            "Rules:\n"
            "- You may import from: 'framer-motion', 'lucide-react', 'react', 'gsap', 'react-icons/si', and relative paths like '../components/ShapeGrid', '../components/DotField', '../components/RippleGrid', '../components/Lightning', '../components/Beams', '../components/GradientBlinds', '../components/Prism', '../components/DarkVeil', '../components/Silk', '../components/ColorBends', '../components/MagicBento', '../components/LogoLoop'.\n"
            "- Do NOT import from any other modules.\n"
            "- CRITICAL: Ensure there is ONLY ONE declaration of the `Portfolio` function. Export as `export default function Portfolio()`.\n"
            "- Return ONLY the modified code for `pages/portfolio.tsx`. NO EXPLANATIONS. NO MARKDOWN TEXT. JUST THE RAW CODE!\n"
        )
        resp = await llm.ainvoke([HumanMessage(content=prompt)])
        
        code = strip_fences(resp.content)
        code = fix_jsx_wrapper(code)
        code = sanitize_imports(code)
        
        # Merge with existing
        existing = {}
        try:
            existing = json.loads(state.get("portfolio_code", "{}"))
        except:
            pass
        existing["pages/portfolio.tsx"] = code
        
        return {"portfolio_code": json.dumps(existing)}

    g = StateGraph(PortfolioState)
    g.add_node("modifier", modifier)
    g.set_entry_point("modifier")
    g.add_edge("modifier", END)
    return g.compile()

gen_graph = build_gen_graph()
mod_graph = build_mod_graph()

# ── Routes ───────────────────────────────────────────────────────────────────
@app.post("/api/generate")
async def generate_portfolio(
    github_url: str = Form(""),
    linkedin_url: str = Form(""),
    cv_file: Optional[UploadFile] = File(None),
):
    # Read file content outside generator to avoid connection scope issues
    cv_bytes = await cv_file.read() if cv_file else None

    async def event_generator():
        import asyncio
        
        yield f"data: {json.dumps({'status': 'Booting up Multi-Agent AI system...', 'progress': 5})}\n\n"
        await asyncio.sleep(0.5)
        
        github_data = ""
        if github_url:
            yield f"data: {json.dumps({'status': 'Scraping GitHub repositories and profile...', 'progress': 10})}\n\n"
            github_data = fetch_github_data(github_url)
            yield f"data: {json.dumps({'status': 'GitHub analysis complete! 🚀', 'progress': 15})}\n\n"
            await asyncio.sleep(0.5)
            
        if linkedin_url:
            yield f"data: {json.dumps({'status': 'Processing LinkedIn URL...', 'progress': 20})}\n\n"
            await asyncio.sleep(0.5)
            yield f"data: {json.dumps({'status': 'LinkedIn profile mapped. 👔', 'progress': 25})}\n\n"
            await asyncio.sleep(0.5)
            
        cv_text = ""
        if cv_bytes:
            yield f"data: {json.dumps({'status': 'Extracting and parsing CV document...', 'progress': 30})}\n\n"
            cv_text = extract_pdf_text(cv_bytes)
            yield f"data: {json.dumps({'status': 'CV data successfully ingested. 📄', 'progress': 35})}\n\n"
            await asyncio.sleep(0.5)

        initial_state = {
            "messages": [],
            "github_data": github_data,
            "linkedin_url": linkedin_url,
            "cv_text": cv_text,
            "profile_summary": "",
            "portfolio_content": "",
            "portfolio_code": "",
            "modification_request": "",
        }
        
        yield f"data: {json.dumps({'status': 'Delegating context to the Analyzer Agent...', 'progress': 40})}\n\n"
        
        queue = asyncio.Queue()

        async def run_graph():
            try:
                async for output in gen_graph.astream(initial_state):
                    await queue.put({"type": "node", "data": output})
                await queue.put({"type": "done"})
            except Exception as e:
                print(f"❌ GRAPH ERROR: {e}")
                await queue.put({"type": "error", "error": str(e)})

        task = asyncio.create_task(run_graph())

        while True:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=15.0)
                if msg["type"] == "done":
                    break
                elif msg["type"] == "error":
                    err_text = str(msg.get("error", "Unknown error"))
                    yield f"data: {json.dumps({'status': f'Error: {err_text}', 'progress': 100})}\n\n"
                    break
                elif msg["type"] == "node":
                    output = msg["data"]
                    for node_name, state_update in output.items():
                        if node_name == "analyzer":
                            yield f"data: {json.dumps({'status': 'Analyzer Agent finished: Skills and experience synthesized! 🧠', 'progress': 55})}\n\n"
                            yield f"data: {json.dumps({'status': 'Passing data to Writer Agent...', 'progress': 60})}\n\n"
                        elif node_name == "writer":
                            yield f"data: {json.dumps({'status': 'Writer Agent finished: Engaging copy drafted! ✍️', 'progress': 75})}\n\n"
                            yield f"data: {json.dumps({'status': 'Thinking about a beautiful Next.js UI... (This takes a few seconds) 🎨', 'progress': 80})}\n\n"
                        elif node_name == "generator":
                            yield f"data: {json.dumps({'status': 'Code Generator Agent finished: React code structured! 💻', 'progress': 95})}\n\n"
                        
                        if state_update and isinstance(state_update, dict) and "portfolio_code" in state_update:
                            yield f"data: {json.dumps({'html': state_update['portfolio_code'], 'status': 'complete', 'progress': 100})}\n\n"
            except asyncio.TimeoutError:
                # Keep-alive ping every 15 seconds to prevent browser reset!
                yield f"data: {json.dumps({'status': 'Agent is still writing complex Next.js code... ⏳'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

class ModifyRequest(BaseModel):
    current_html: str
    modification: str

@app.post("/api/modify")
async def modify_portfolio(req: ModifyRequest):
    async def event_generator():
        import asyncio
        initial_state = {
            "messages": [],
            "github_data": "", "linkedin_url": "", "cv_text": "",
            "profile_summary": "", "portfolio_content": "",
            "portfolio_code": req.current_html,
            "modification_request": req.modification,
        }
        
        yield f"data: {json.dumps({'status': 'Modifier Agent is analyzing your request... 🔍'})}\n\n"
        await asyncio.sleep(0.5)
        yield f"data: {json.dumps({'status': 'Rewriting Next.js components... ⚡'})}\n\n"
        
        queue = asyncio.Queue()

        async def run_graph():
            try:
                async for output in mod_graph.astream(initial_state):
                    await queue.put({"type": "node", "data": output})
                await queue.put({"type": "done"})
            except Exception as e:
                print(f"❌ GRAPH ERROR: {e}")
                await queue.put({"type": "error", "error": str(e)})

        task = asyncio.create_task(run_graph())

        while True:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=15.0)
                if msg["type"] == "done":
                    break
                elif msg["type"] == "error":
                    err_text = str(msg.get("error", "Unknown error"))
                    yield f"data: {json.dumps({'status': f'Error: {err_text}'})}\n\n"
                    break
                elif msg["type"] == "node":
                    output = msg["data"]
                    for node_name, state_update in output.items():
                        yield f"data: {json.dumps({'status': 'Changes applied successfully! 🎉'})}\n\n"
                        if state_update and isinstance(state_update, dict) and "portfolio_code" in state_update:
                            yield f"data: {json.dumps({'html': state_update['portfolio_code'], 'status': 'complete'})}\n\n"
            except asyncio.TimeoutError:
                # Keep-alive ping every 15 seconds to prevent browser reset!
                yield f"data: {json.dumps({'status': 'Still modifying code... ⏳'})}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/")
def root():
    return {"message": "AI Portfolio Generator API – see /docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
