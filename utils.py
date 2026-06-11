import operator, os, json, re, requests, sys, time, random
import io
import PyPDF2

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
      <Component {...pageProps} />
    </ErrorBoundary>
  )
}""",
    "pages/index.js": """import Portfolio from './portfolio';
export default Portfolio;""",
    "styles/globals.css": """@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --primary-color: #a855f7;
    --primary-light: #d8b4fe;
  }
  body {
    @apply bg-neutral-50 text-neutral-900 transition-colors duration-300;
  }
  html.dark body {
    @apply bg-neutral-950 text-neutral-50;
  }
}""",
    "tailwind.config.js": """/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: 'var(--primary-color)',
        'primary-light': 'var(--primary-light)',
      }
    },
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
    "gsap": "^3.12.5",
    "lenis": "latest"
  }
}"""
}

def fetch_github_data(github_url: str) -> str:
    try:
        username = github_url.rstrip("/").split("/")[-1]
        user = requests.get(f"https://api.github.com/users/{username}", timeout=10).json()
        repos = requests.get(
            f"https://api.github.com/users/{username}/repos?sort=stars&per_page=10",
            timeout=10,
        ).json()
        profile_readme = ""
        try:
            readme_res = requests.get(f"https://raw.githubusercontent.com/{username}/{username}/main/README.md", timeout=5)
            if readme_res.status_code == 200:
                profile_readme = readme_res.text
            else:
                readme_res = requests.get(f"https://raw.githubusercontent.com/{username}/{username}/master/README.md", timeout=5)
                if readme_res.status_code == 200:
                    profile_readme = readme_res.text
        except Exception:
            pass

        social_accounts = []
        try:
            social_res = requests.get(
                f"https://api.github.com/users/{username}/social_accounts",
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=5
            )
            if social_res.status_code == 200:
                social_accounts = social_res.json()
        except Exception:
            pass

        return json.dumps({
            "name": user.get("name", username),
            "bio": user.get("bio", ""),
            "avatar": user.get("avatar_url", ""),
            "location": user.get("location", ""),
            "company": user.get("company", ""),
            "blog": user.get("blog", ""),
            "email": user.get("email", ""),
            "twitter_username": user.get("twitter_username", ""),
            "social_accounts": [{"provider": s.get("provider", ""), "url": s.get("url", "")} for s in social_accounts if isinstance(s, dict)],
            "public_repos": user.get("public_repos", 0),
            "followers": user.get("followers", 0),
            "profile_readme": profile_readme[:2000] if profile_readme else "", # Limit length to save tokens
            "repos": [
                {
                    "name": r["name"],
                    "desc": r.get("description", ""),
                    "lang": r.get("language", ""),
                    "stars": r["stargazers_count"],
                    "forks": r.get("forks_count", 0),
                    "url": r["html_url"],
                    "homepage": r.get("homepage", ""),
                    "topics": r.get("topics", []),
                    "created_at": r.get("created_at", ""),
                }
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
    """Ensure the component's return statement wraps everything in a React fragment <>....</>."""
    if '<>' in code and '</>' in code:
        return code
    
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
        code = re.sub(
            r'(\s*</div>\s*)\n(\s*)\)',
            r'\1\n' + indent + '</>\n\2)',
            code,
            count=1
        )
    
    if '<>' not in code:
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
                if i + 1 < len(lines):
                    next_indent = len(lines[i+1]) - len(lines[i+1].lstrip())
                    new_lines.append(' ' * next_indent + '<>')
                    inserted_open = True
                continue
            
            if in_return and inserted_open:
                for ch in stripped:
                    if ch == '(':
                        return_depth += 1
                    elif ch == ')':
                        return_depth -= 1
                
                if return_depth <= 0:
                    indent_here = len(line) - len(line.lstrip())
                    new_lines.append(' ' * (indent_here + 2) + '</>')
                    new_lines.append(line)
                    in_return = False
                    continue
            
            new_lines.append(line)
        
        if inserted_open:
            code = '\n'.join(new_lines)
    
    return code

def sanitize_imports(code: str) -> str:
    """Remove import lines that reference unknown libraries or non-existent lucide icons."""
    lines = code.split("\n")
    clean_lines = []
    
    ALLOWED_MODULES = {"react", "framer-motion", "lucide-react", "ogl", "three", "@react-three/fiber", "@react-three/drei", "three/src/math/MathUtils.js", "gsap", "react-icons/si", "lenis"}
    
    for line in lines:
        stripped = line.strip()
        
        if stripped.startswith("import "):
            from_match = re.search(r'''from\s+['"]([^'"]+)['"]''', stripped)
            if from_match:
                module = from_match.group(1)
                if module.startswith(".") or module.startswith("/"):
                    clean_lines.append(line)
                    continue
                if module not in ALLOWED_MODULES:
                    print(f"[Sanitizer] Stripped bad import: {stripped}")
                    continue
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
