import json
import random
import design_templates

def assemble_portfolio_tsx(layout_data: dict) -> str:
    bg = layout_data.get("background", "ShapeGrid")
    hero_effect = layout_data.get("hero_effect", None)
    sections = layout_data.get("sections", [])

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

    imports = [
        "import React, { useState, useEffect } from 'react';",
        "import { Sun, Moon } from 'lucide-react';"
    ]
    for name in used_components:
        imports.append(f"import {name} from '../components/{name}';")

    jsx_elements = []

    # ── Theme Colors ──
    # Determine primary color based on hero_effect
    primary_color = "#a855f7" # default purple
    primary_light = "#d8b4fe"
    
    if hero_effect == "Lightning":
        hue = random.choice([230, 280, 190, 320])
        # Approximate hex colors for the hues
        if hue == 230: primary_color, primary_light = "#3b82f6", "#93c5fd" # Blue
        elif hue == 280: primary_color, primary_light = "#a855f7", "#d8b4fe" # Purple
        elif hue == 190: primary_color, primary_light = "#06b6d4", "#67e8f9" # Cyan
        elif hue == 320: primary_color, primary_light = "#ec4899", "#f9a8d4" # Pink
    elif hero_effect == "GradientBlinds":
        colors = ["['#FF9FFC', '#5227FF']", "['#3b82f6', '#8b5cf6', '#ec4899']", "['#10b981', '#3b82f6']"]
        gradientColors = random.choice(colors)
        if "'#10b981'" in gradientColors: primary_color, primary_light = "#10b981", "#6ee7b7" # Emerald
        elif "'#3b82f6'" in gradientColors: primary_color, primary_light = "#3b82f6", "#93c5fd" # Blue
        else: primary_color, primary_light = "#5227FF", "#93c5fd" # Violet/Blue
    elif hero_effect == "Silk":
        colors = ["#7B7481", "#a855f7", "#3b82f6", "#ec4899", "#10b981", "#f59e0b"]
        color = random.choice(colors)
        primary_color = color
        primary_light = color # simplify for now
    elif hero_effect == "ColorBends":
        palettes = ['["#ff5c7a", "#8a5cff", "#00ffd1"]', '["#3b82f6", "#8b5cf6", "#ec4899"]', '["#10b981", "#f59e0b", "#ef4444"]', '["#06b6d4", "#a855f7", "#f97316"]', '["#ec4899", "#8b5cf6", "#06b6d4"]']
        colors = random.choice(palettes)
        if "10b981" in colors: primary_color, primary_light = "#10b981", "#6ee7b7"
        elif "06b6d4" in colors: primary_color, primary_light = "#06b6d4", "#67e8f9"
        elif "ff5c7a" in colors: primary_color, primary_light = "#ff5c7a", "#fda4af"
        else: primary_color, primary_light = "#8b5cf6", "#c4b5fd"

    # Inject dynamic CSS variables
    jsx_elements.append(f"""
      <style>{{`
        :root {{
          --primary-color: {primary_color};
          --primary-light: {primary_light};
        }}
      `}}</style>
    """)

    # ── Full-screen background ──
    if bg == "ShapeGrid":
        speed = round(random.uniform(0.1, 0.8), 2)
        shape = random.choice(["square", "hexagon", "circle", "triangle"])
        jsx_elements.append(f"""
      <div className="fixed inset-0 z-0 opacity-10 dark:opacity-30 pointer-events-none">
        <ShapeGrid speed={{{speed}}} squareSize={{50}} direction="diagonal" borderColor="#00000010" hoverFillColor="var(--primary-color)" shape="{shape}" hoverTrailAmount={{5}} />
      </div>""")
    elif bg == "DotField":
        dotRadius = round(random.uniform(1.0, 2.0), 1)
        dotSpacing = random.choice([10, 12, 14, 16])
        sparkle = str(random.choice([True, False])).lower()
        waveAmplitude = random.choice([0, 10, 20])
        jsx_elements.append(f"""
      <div className="fixed inset-0 z-0 opacity-20 dark:opacity-50 pointer-events-none">
        <DotField dotRadius={{{dotRadius}}} dotSpacing={{{dotSpacing}}} bulgeStrength={{67}} glowRadius={{160}} sparkle={{{sparkle}}} waveAmplitude={{{waveAmplitude}}} />
      </div>""")

    # ── Hero section ──
    jsx_elements.append("""
      <div className="relative min-h-screen flex items-center justify-center overflow-hidden">""")

    jsx_elements.append('<header className="relative w-full min-h-screen flex flex-col items-center justify-center overflow-hidden">')

    if hero_effect == "RippleGrid":
        rippleIntensity = round(random.uniform(0.02, 0.08), 3)
        gridSize = random.choice([15, 20, 25])
        jsx_elements.append(f"""
        <div className="absolute inset-0 z-0 opacity-20 dark:opacity-40 mix-blend-multiply dark:mix-blend-screen">
          <RippleGrid enableRainbow={{false}} gridColor="var(--primary-color)" rippleIntensity={{{rippleIntensity}}} gridSize={{{gridSize}}} gridThickness={{2}} mouseInteraction={{true}} />
        </div>""")
    elif hero_effect == "Lightning":
        hue = random.choice([230, 280, 190, 320])
        speed = round(random.uniform(0.5, 2.0), 1)
        intensity = round(random.uniform(0.8, 1.5), 1)
        jsx_elements.append(f"""
        <div className="absolute inset-0 z-0 opacity-40 dark:opacity-80">
          <Lightning hue={{{hue}}} xOffset={{0}} speed={{{speed}}} intensity={{{intensity}}} size={{1}} />
        </div>""")
    elif hero_effect == "Beams":
        beamNumber = random.choice([8, 12, 16])
        noiseIntensity = round(random.uniform(1.0, 2.0), 2)
        rotation = random.choice([0, 45, -45])
        jsx_elements.append(f"""
        <div className="absolute inset-0 z-0 opacity-30 dark:opacity-80">
          <Beams beamWidth={{2}} beamHeight={{15}} beamNumber={{{beamNumber}}} lightColor="var(--primary-light)" speed={{2}} noiseIntensity={{{noiseIntensity}}} scale={{0.2}} rotation={{{rotation}}} />
        </div>""")
    elif hero_effect == "GradientBlinds":
        if 'gradientColors' not in locals(): gradientColors = "['#3b82f6', '#8b5cf6']"
        blindCount = random.choice([8, 12, 16, 20])
        noise = round(random.uniform(0.1, 0.5), 1)
        distortAmount = random.choice([0, 0.5, 1])
        jsx_elements.append(f"""
        <div className="absolute inset-0 z-0 opacity-40 dark:opacity-80">
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
        <div className="absolute inset-0 z-0 opacity-50 dark:opacity-100 mix-blend-difference dark:mix-blend-normal">
          <DarkVeil hueShift={{{hueShift}}} noiseIntensity={{{noiseIntensity}}} scanlineIntensity={{{scanlineIntensity}}} speed={{{speed}}} scanlineFrequency={{{scanlineFrequency}}} warpAmount={{{warpAmount}}} resolutionScale={{1}} />
        </div>""")
    elif hero_effect == "Silk":
        if 'color' not in locals(): color = "#a855f7"
        speed = random.choice([3, 5, 7, 10])
        scale = round(random.uniform(0.8, 1.5), 2)
        noiseIntensity = round(random.uniform(0.5, 2.0), 2)
        rotation = round(random.uniform(0, 3.14), 2)
        jsx_elements.append(f"""
        <div className="absolute inset-0 z-0 opacity-50 dark:opacity-100">
          <Silk speed={{{speed}}} scale={{{scale}}} color="{color}" noiseIntensity={{{noiseIntensity}}} rotation={{{rotation}}} />
        </div>""")
    elif hero_effect == "ColorBends":
        if 'colors' not in locals(): colors = '["#3b82f6", "#8b5cf6"]'
        rotation = random.choice([0, 45, 90, 135, 180, 270])
        speed = round(random.uniform(0.1, 0.4), 2)
        scale = round(random.uniform(0.8, 1.3), 2)
        frequency = round(random.uniform(0.5, 1.5), 2)
        warpStrength = round(random.uniform(0.5, 1.5), 2)
        intensity = round(random.uniform(1.0, 2.0), 2)
        bandWidth = random.choice([4, 6, 8])
        noise = round(random.uniform(0.05, 0.25), 3)
        jsx_elements.append(f"""
        <div className="absolute inset-0 z-0 opacity-40 dark:opacity-100">
          <ColorBends colors={{{colors}}} rotation={{{rotation}}} speed={{{speed}}} scale={{{scale}}} frequency={{{frequency}}} warpStrength={{{warpStrength}}} mouseInfluence={{1}} noise={{{noise}}} parallax={{0.5}} iterations={{1}} intensity={{{intensity}}} bandWidth={{{bandWidth}}} transparent />
        </div>""")
    elif hero_effect == "Prism":
        hueShift = round(random.uniform(0, 3.14), 2)
        colorFrequency = round(random.uniform(0.5, 2.0), 1)
        noise = round(random.uniform(0.1, 0.6), 1)
        jsx_elements.append(f"""
        <div className="absolute inset-0 z-0 opacity-40 dark:opacity-80">
          <Prism animationType="rotate" timeScale={{0.5}} height={{3.5}} baseWidth={{5.5}} scale={{3.6}} hueShift={{{hueShift}}} colorFrequency={{{colorFrequency}}} noise={{{noise}}} glow={{1}} />
        </div>""")

    jsx_elements.append('<div className="absolute bottom-0 left-0 w-full h-48 bg-gradient-to-t from-neutral-50 dark:from-neutral-950 to-transparent z-10 pointer-events-none"></div>')

    hero_props = {}
    for section in sections:
        if section.get("type") == "Hero":
            hero_props = section.get("props", {})
            break

    name = hero_props.get("name", "a Builder")
    title = hero_props.get("title", "Developer")
    subtitle = hero_props.get("subtitle", "")
    jsx_elements.append(f"""
        <nav className="absolute top-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-4 sm:gap-6 px-6 sm:px-8 py-3 rounded-full bg-white/50 dark:bg-white/5 border border-black/10 dark:border-white/10 backdrop-blur-md shadow-xl transition-all duration-300">
          <a href="#home" className="text-neutral-900 dark:text-white font-semibold text-sm bg-black/5 dark:bg-white/10 px-4 py-1.5 rounded-full">Home</a>
          <a href="#about" className="text-neutral-600 dark:text-gray-400 hover:text-primary transition-colors text-sm font-medium">About</a>
          <a href="#projects" className="text-neutral-600 dark:text-gray-400 hover:text-primary transition-colors text-sm font-medium">Projects</a>
          <a href="#blogs" className="text-neutral-600 dark:text-gray-400 hover:text-primary transition-colors text-sm font-medium">Blogs</a>
          <a href="#contact" className="text-neutral-600 dark:text-gray-400 hover:text-primary transition-colors text-sm font-medium">Contact</a>
          <button onClick={{toggleTheme}} className="ml-2 p-1.5 rounded-full bg-black/5 dark:bg-white/10 hover:bg-black/10 dark:hover:bg-white/20 transition-colors text-neutral-800 dark:text-white">
            {{isDark ? <Sun size={{16}} /> : <Moon size={{16}} />}}
          </button>
        </nav>

        <div id="home" className="relative z-10 flex flex-col items-center justify-center min-h-[90vh] text-center px-4 mt-20 pointer-events-none">
          <div className="pointer-events-auto w-24 h-24 rounded-full border border-neutral-300 dark:border-white/20 p-1 mb-6 bg-gradient-to-b from-neutral-200 dark:from-white/10 to-transparent shadow-xl">
            <div className="w-full h-full rounded-full bg-white/50 dark:bg-black/50 backdrop-blur flex items-center justify-center text-4xl overflow-hidden">
               🧑‍💻
            </div>
          </div>
          
          <div className="pointer-events-auto mb-6 flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/80 dark:bg-black/40 border border-neutral-200 dark:border-white/10 text-sm backdrop-blur-md shadow-lg">
            <div className="w-2 h-2 rounded-full bg-[var(--primary-color)] shadow-[0_0_10px_var(--primary-color)] animate-pulse"></div>
            <span className="text-neutral-800 dark:text-white font-medium text-xs tracking-wide">Available For New Projects</span>
          </div>
          
          <h1 className="pointer-events-auto text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight text-neutral-900 dark:text-white mb-6 max-w-4xl leading-[1.1] drop-shadow-2xl">
            <span className="font-serif italic text-neutral-600 dark:text-gray-200">Hi, I'm {name}</span> 👋 <br/>
            <span className="font-sans font-extrabold text-[var(--primary-color)]">{title}</span>
          </h1>
          
          <p className="pointer-events-auto text-lg md:text-xl text-neutral-600 dark:text-gray-400 mb-10 max-w-2xl font-light leading-relaxed">
            {subtitle}
          </p>
          
          <div className="pointer-events-auto flex flex-col sm:flex-row items-center gap-5">
            <button className="bg-neutral-100 dark:bg-black/40 text-neutral-900 dark:text-white border border-neutral-300 dark:border-white/20 px-8 py-3.5 rounded-xl font-bold hover:bg-neutral-200 dark:hover:bg-white/10 transition-all backdrop-blur-xl flex items-center gap-2 shadow-lg">
              Explore My Work ↓
            </button>
            <button className="bg-neutral-900 dark:bg-white text-white dark:text-black px-8 py-3.5 rounded-xl font-bold hover:bg-neutral-800 dark:hover:bg-gray-200 transition-all shadow-[0_0_20px_rgba(0,0,0,0.1)] dark:shadow-[0_0_20px_rgba(255,255,255,0.4)] flex items-center gap-2">
              🤝 Let's Connect
            </button>
          </div>
        </div>
        </header>""")

    jsx_elements.append("      </div>")

    # ── Content sections ──
    jsx_elements.append("""
      <div className="relative z-10 p-8 max-w-5xl mx-auto">""")

    for section in sections:
        t = section.get("type", "Section")
        if t == "Hero":
            continue
        props = section.get("props", {})

        if t in design_templates.get_component_names():
            wrapper_class = "mb-12 relative w-full overflow-hidden"
            if t == "ScrollStack":
                props["useWindowScroll"] = True

            jsx_elements.append(f"""
        <div id="{{ {json.dumps(t.lower())} }}" className="{wrapper_class}">
          <{t} {{...{json.dumps(props)}}} />
        </div>""")
        else:
            content_jsx = ""
            if isinstance(props, dict):
                for k, v in props.items():
                    if isinstance(v, str):
                        v_lines = str(v).replace("\\n", "\n").split("\n")
                        v_jsx = "<br/>".join([f"<span>{{ {json.dumps(line.strip())} }}</span>" for line in v_lines if line.strip()])
                        content_jsx += f'<p className="text-neutral-700 dark:text-gray-300 text-lg leading-relaxed mb-6 whitespace-pre-wrap">{v_jsx}</p>\n            '
                    elif isinstance(v, list):
                        if len(v) > 0 and isinstance(v[0], dict):
                            content_jsx += '<div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">\n'
                            for item in v:
                                if isinstance(item, dict):
                                    content_jsx += '  <div className="flex flex-col p-6 rounded-2xl bg-white dark:bg-[#0f0f11] border border-neutral-200 dark:border-white/10 shadow-xl hover:border-primary dark:hover:border-primary/50 transition-all">\n'
                                    for dk, dv in item.items():
                                        if isinstance(dv, str):
                                            dv_lines = str(dv).replace("\\n", "\n").split("\n")
                                            dv_jsx = "<br/>".join([f"<span>{{ {json.dumps(line.strip())} }}</span>" for line in dv_lines if line.strip()])
                                            if dk.lower() in ["title", "name", "role", "company"]:
                                                content_jsx += f'    <h3 className="text-xl font-bold text-neutral-900 dark:text-white mb-3">{dv_jsx}</h3>\n'
                                            else:
                                                content_jsx += f'    <p className="text-sm text-neutral-600 dark:text-gray-400 mb-2 leading-relaxed"><strong className="text-primary capitalize">{{ {json.dumps(dk)} }}:</strong> {dv_jsx}</p>\n'
                                        elif isinstance(dv, list):
                                            content_jsx += f'    <p className="text-sm text-neutral-600 dark:text-gray-400 mb-2 leading-relaxed"><strong className="text-primary capitalize">{{ {json.dumps(dk)} }}:</strong> {{ {json.dumps(", ".join([str(x) for x in dv]))} }}</p>\n'
                                    content_jsx += '  </div>\n'
                            content_jsx += '</div>\n'
                        else:
                            content_jsx += '<ul className="list-disc pl-5 mb-4 space-y-2 text-neutral-700 dark:text-gray-300">\n'
                            for item in v:
                                if isinstance(item, str):
                                    content_jsx += f'              <li>{{ {json.dumps(item)} }}</li>\n'
                            content_jsx += '            </ul>\n            '
            
            if not content_jsx:
                content_jsx = '<p className="text-neutral-500 dark:text-gray-400 italic">No content available.</p>'

            jsx_elements.append(f"""
        <div id="{{ {json.dumps(t.lower())} }}" className="mb-32 relative">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3/4 h-3/4 bg-primary/5 dark:bg-primary/10 blur-3xl rounded-full pointer-events-none"></div>
          <div className="mb-12 text-center relative z-10">
            <span className="px-4 py-1.5 rounded-full bg-neutral-200/50 dark:bg-white/5 border border-neutral-300 dark:border-white/10 text-primary font-bold tracking-[0.2em] text-xs uppercase shadow-sm backdrop-blur-md">{t}</span>
            <h2 className="text-4xl md:text-5xl font-extrabold mt-6 pb-2 text-transparent bg-clip-text bg-gradient-to-r from-neutral-800 to-neutral-500 dark:from-gray-100 dark:to-gray-500 tracking-tight">{t} Highlights</h2>
          </div>
          <div className="relative z-10 p-10 md:p-14 bg-white/60 dark:bg-[#0a0a0a]/60 backdrop-blur-xl rounded-[2.5rem] border border-neutral-200 dark:border-white/10 shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-[0_8px_30px_rgb(0,0,0,0.12)] hover:border-neutral-300 dark:hover:border-white/20 transition-all duration-500 max-w-5xl mx-auto">
            <div className="absolute inset-0 bg-gradient-to-br from-black/[0.02] dark:from-white/[0.02] to-transparent rounded-[2.5rem] pointer-events-none"></div>
            <div className="prose prose-neutral dark:prose-invert max-w-none relative z-20">
              {content_jsx}
            </div>
          </div>
        </div>""")

    jsx_elements.append("      </div>")

    # ── Custom Footer ──
    big_text = name.upper() if name and name != "a Builder" else "IHATEPDF"
    jsx_elements.append(f"""
      <footer className="w-full relative mt-32 border-t border-neutral-200 dark:border-white/10 overflow-hidden bg-neutral-100 dark:bg-black/80 transition-colors duration-300">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#0000000a_1px,transparent_1px)] dark:bg-[linear-gradient(to_right,#ffffff0a_1px,transparent_1px)] bg-[size:4px_100%] pointer-events-none mix-blend-overlay"></div>
        <div className="w-full overflow-hidden flex items-center justify-center py-24 relative z-10">
          <h1 className="text-[15vw] font-black tracking-tighter text-neutral-300/50 dark:text-white/5 whitespace-nowrap leading-none select-none">
            {{ {json.dumps(big_text)} }}
          </h1>
        </div>
        <div className="absolute bottom-4 w-full px-8 flex justify-between items-center text-neutral-500 dark:text-[#737373] text-xs font-mono z-20">
          <div>Made with <span className="text-red-500">hate</span> by <span className="text-neutral-900 dark:text-white font-bold">{{ {json.dumps(name)} }}</span> 😈</div>
          <div className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></div>All systems hostile</div>
        </div>
      </footer>
""")

    full_jsx = "\n".join(jsx_elements)

    code = "\n".join(imports) + "\n\n"
    code += "export default function Portfolio() {\n"
    code += "  const [isDark, setIsDark] = useState(true);\n"
    code += "  useEffect(() => {\n"
    code += "    if (isDark) document.documentElement.classList.add('dark');\n"
    code += "    else document.documentElement.classList.remove('dark');\n"
    code += "  }, [isDark]);\n"
    code += "  const toggleTheme = () => setIsDark(!isDark);\n\n"
    code += "  return (\n"
    code += "    <div className=\"min-h-screen bg-neutral-50 dark:bg-neutral-950 text-neutral-900 dark:text-white font-sans transition-colors duration-300\">\n"
    code += full_jsx + "\n"
    code += "    </div>\n"
    code += "  );\n"
    code += "}\n"

    return code
