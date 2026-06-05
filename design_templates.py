import os

def read_template(filepath: str) -> str:
    """Helper to read template files from disk."""
    if not os.path.exists(filepath):
        return f"// Error: Template not found at {filepath}"
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

# ══════════════════════════════════════════════════════════════════════════════
# REGISTRY: Maps component name -> (file path in Sandpack, source code, usage hint for prompt)
# ══════════════════════════════════════════════════════════════════════════════

# Component registry points to the files on disk
DESIGN_COMPONENTS = {
    "ShapeGrid": {
        "file": "components/ShapeGrid.tsx",
        "source_path": "templates/backgrounds/ShapeGrid.tsx",
        "type": "background",
        "usage_hint": (
            "AVAILABLE PRE-BUILT COMPONENT — ShapeGrid (animated canvas background):\n"
            "  import ShapeGrid from '../components/ShapeGrid';\n"
            "  Usage: Wrap in a div with `absolute inset-0 z-0` behind Hero content.\n"
            "  <div className=\"absolute inset-0 z-0 opacity-40\">\n"
            "    <ShapeGrid speed={0.3} squareSize={50} direction=\"diagonal\" borderColor=\"#ffffff10\" hoverFillColor=\"#a855f7\" shape=\"square\" hoverTrailAmount={5} />\n"
            "  </div>\n"
            "  Props: speed (number), squareSize (number), direction ('diagonal'|'up'|'right'|'down'|'left'), borderColor (string), hoverFillColor (string), shape ('square'|'hexagon'|'circle'|'triangle'), hoverTrailAmount (number).\n"
        ),
    },
    "DotField": {
        "file": "components/DotField.tsx",
        "source_path": "templates/backgrounds/DotField.tsx",
        "type": "background",
        "usage_hint": (
            "AVAILABLE PRE-BUILT COMPONENT — DotField (interactive particle background):\n"
            "  import DotField from '../components/DotField';\n"
            "  Usage: Wrap in a div with `absolute inset-0 z-0` behind Hero content.\n"
            "  <div className=\"absolute inset-0 z-0\">\n"
            "    <DotField dotRadius={1.5} dotSpacing={14} bulgeStrength={67} glowRadius={160} sparkle={false} waveAmplitude={0} />\n"
            "  </div>\n"
            "  Props: dotRadius, dotSpacing, bulgeStrength, glowRadius, sparkle, waveAmplitude, gradientFrom, gradientTo.\n"
        ),
    },
    "RippleGrid": {
        "file": "components/RippleGrid.tsx",
        "source_path": "templates/hero/RippleGrid.tsx",
        "type": "hero",
        "usage_hint": (
            "AVAILABLE PRE-BUILT COMPONENT — RippleGrid (interactive grid ripple hero effect):\n"
            "  import RippleGrid from '../components/RippleGrid';\n"
            "  Usage: Renders inside the Hero section as a visual effect overlay.\n"
            "  <div className=\"absolute inset-0 z-0\">\n"
            "    <RippleGrid enableRainbow={false} gridColor=\"#ffffff\" rippleIntensity={0.05} gridSize={10} gridThickness={15} mouseInteraction={true} />\n"
            "  </div>\n"
            "  Props: enableRainbow, gridColor, rippleIntensity, gridSize, gridThickness, fadeDistance, vignetteStrength, glowIntensity, opacity, gridRotation, mouseInteraction, mouseInteractionRadius.\n"
        ),
    },
    "Lightning": {
        "file": "components/Lightning.tsx",
        "source_path": "templates/hero/Lightning.tsx",
        "type": "hero",
        "usage_hint": (
            "AVAILABLE PRE-BUILT COMPONENT — Lightning (interactive webgl lightning hero effect):\n"
            "  import Lightning from '../components/Lightning';\n"
            "  Usage: Renders inside the Hero section as a visual effect overlay.\n"
            "  <div className=\"absolute inset-0 z-0 opacity-80\">\n"
            "    <Lightning hue={230} xOffset={0} speed={1} intensity={1} size={1} />\n"
            "  </div>\n"
            "  Props: hue, xOffset, speed, intensity, size.\n"
        ),
    },
    "Beams": {
        "file": "components/Beams.tsx",
        "source_path": "templates/hero/Beams.tsx",
        "type": "hero",
        "usage_hint": (
            "AVAILABLE PRE-BUILT COMPONENT — Beams (3d fiber beams hero effect):\n"
            "  import Beams from '../components/Beams';\n"
            "  Usage: Renders inside the Hero section as a visual effect overlay.\n"
            "  <div className=\"absolute inset-0 z-0 opacity-80\">\n"
            "    <Beams beamWidth={2} beamHeight={15} beamNumber={12} lightColor=\"#ffffff\" speed={2} noiseIntensity={1.75} scale={0.2} rotation={0} />\n"
            "  </div>\n"
            "  Props: beamWidth, beamHeight, beamNumber, lightColor, speed, noiseIntensity, scale, rotation.\n"
        ),
    },
    "GradientBlinds": {
        "file": "components/GradientBlinds.tsx",
        "source_path": "templates/hero/GradientBlinds.tsx",
        "type": "hero",
        "usage_hint": (
            "AVAILABLE PRE-BUILT COMPONENT — GradientBlinds (interactive webgl blinds hero effect):\n"
            "  import GradientBlinds from '../components/GradientBlinds';\n"
            "  Usage: Renders inside the Hero section as a visual effect overlay.\n"
            "  <div className=\"absolute inset-0 z-0 opacity-80\">\n"
            "    <GradientBlinds gradientColors={['#FF9FFC', '#5227FF']} angle={0} noise={0.3} blindCount={12} blindMinWidth={50} spotlightRadius={0.5} spotlightSoftness={1} spotlightOpacity={1} mouseDampening={0.15} distortAmount={0} shineDirection=\"left\" mixBlendMode=\"lighten\" />\n"
            "  </div>\n"
            "  Props: gradientColors, angle, noise, blindCount, blindMinWidth, mouseDampening, spotlightRadius, spotlightSoftness, spotlightOpacity, distortAmount, shineDirection, mixBlendMode.\n"
        ),
    },
    "Prism": {
        "file": "components/Prism.tsx",
        "source_path": "templates/hero/Prism.tsx",
        "type": "hero",
        "usage_hint": (
            "AVAILABLE PRE-BUILT COMPONENT — Prism (interactive webgl prism background):\n"
            "  import Prism from '../components/Prism';\n"
            "  Usage: Wrap in a div with `absolute inset-0 z-0` behind Hero content.\n"
            "  <div className=\"absolute inset-0 z-0 opacity-80\">\n"
            "    <Prism animationType=\"rotate\" timeScale={0.5} height={3.5} baseWidth={5.5} scale={3.6} hueShift={0} colorFrequency={1} noise={0.5} glow={1} />\n"
            "  </div>\n"
            "  Props: height, baseWidth, animationType, glow, offset, noise, transparent, scale, hueShift, colorFrequency, hoverStrength, inertia, bloom, suspendWhenOffscreen, timeScale.\n"
        ),
    },
    "DarkVeil": {
        "file": "components/DarkVeil.tsx",
        "source_path": "templates/hero/DarkVeil.tsx",
        "type": "hero",
        "usage_hint": (
            "AVAILABLE PRE-BUILT COMPONENT — DarkVeil (webgl cppn neural network hero effect):\n"
            "  import DarkVeil from '../components/DarkVeil';\n"
            "  Usage: Renders inside the Hero section as a visual effect overlay.\n"
            "  <div className=\"absolute inset-0 z-0\">\n"
            "    <DarkVeil hueShift={0} noiseIntensity={0} scanlineIntensity={0} speed={0.5} scanlineFrequency={0} warpAmount={0} resolutionScale={1} />\n"
            "  </div>\n"
            "  Props: hueShift (number), noiseIntensity (number), scanlineIntensity (number), speed (number), scanlineFrequency (number), warpAmount (number), resolutionScale (number).\n"
        ),
    },
    "Silk": {
        "file": "components/Silk.tsx",
        "source_path": "templates/hero/Silk.tsx",
        "type": "hero",
        "usage_hint": (
            "AVAILABLE PRE-BUILT COMPONENT — Silk (webgl silk fabric hero effect):\n"
            "  import Silk from '../components/Silk';\n"
            "  Usage: Renders inside the Hero section as a visual effect overlay.\n"
            "  <div className=\"absolute inset-0 z-0\">\n"
            "    <Silk speed={5} scale={1} color=\"#7B7481\" noiseIntensity={1.5} rotation={0} />\n"
            "  </div>\n"
            "  Props: speed (number), scale (number), color (hex string), noiseIntensity (number), rotation (number radians).\n"
        ),
    },
    "ColorBends": {
        "file": "components/ColorBends.tsx",
        "source_path": "templates/hero/ColorBends.tsx",
        "type": "hero",
        "usage_hint": (
            "AVAILABLE PRE-BUILT COMPONENT — ColorBends (interactive fluid colors background):\n"
            "  import ColorBends from '../components/ColorBends';\n"
            "  Usage: Wrap in a div with `absolute inset-0 z-0` behind Hero content.\n"
            "  <div className=\"absolute inset-0 z-0\">\n"
            "    <ColorBends colors={[\"#ff5c7a\", \"#8a5cff\", \"#00ffd1\"]} rotation={90} speed={0.2} scale={1} frequency={1} warpStrength={1} mouseInfluence={1} noise={0.15} parallax={0.5} iterations={1} intensity={1.5} bandWidth={6} transparent />\n"
            "  </div>\n"
            "  Props: colors (string[]), rotation (number), speed (number), scale (number), frequency (number), warpStrength (number), mouseInfluence (number), noise (number), parallax (number), iterations (number), intensity (number), bandWidth (number), transparent (boolean).\n"
        ),
    },
    "MagicBento": {
        "file": "components/MagicBento.tsx",
        "source_path": "templates/components/MagicBento.tsx",
        "type": "component",
        "usage_hint": (
            "AVAILABLE PRE-BUILT COMPONENT — MagicBento (interactive bento grid layout):\n"
            "  import MagicBento from '../components/MagicBento';\n"
            "  Usage: Place this directly in the page to show an interactive bento grid of cards. Best used in an 'About' or 'Features' section.\n"
            "  <MagicBento items={[{ title: 'Project 1', description: 'Built with React', label: 'Feature' }]} textAutoHide={true} enableStars={false} enableSpotlight={true} enableBorderGlow={true} enableTilt enableMagnetism clickEffect={true} spotlightRadius={100} particleCount={12} glowColor=\"132, 0, 255\" />\n"
            "  Props: items (array of {title, description, label}), textAutoHide, enableStars, enableSpotlight, enableBorderGlow, disableAnimations, spotlightRadius, particleCount, enableTilt, glowColor, clickEffect, enableMagnetism.\n"
        ),
    },
    "LogoLoop": {
        "file": "components/LogoLoop.tsx",
        "source_path": "templates/components/LogoLoop.tsx",
        "type": "component",
        "usage_hint": (
            "AVAILABLE PRE-BUILT COMPONENT — LogoLoop (infinite scrolling logo carousel):\n"
            "  import LogoLoop from '../components/LogoLoop';\n"
            "  import { SiReact, SiNextdotjs, SiTypescript, SiTailwindcss } from 'react-icons/si';\n"
            "  Usage: Renders an infinite loop of technology logos. Ideal for 'Technologies' or 'Partners' sections.\n"
            "  <LogoLoop logos={[{node: <SiReact />, title: 'React'}, {node: <SiNextdotjs />, title: 'Next.js'}, {node: <SiTypescript />, title: 'TypeScript'}, {node: <SiTailwindcss />, title: 'Tailwind'}]} speed={120} direction=\"left\" logoHeight={48} gap={40} hoverSpeed={0} scaleOnHover fadeOut fadeOutColor=\"#120F17\" />\n"
            "  Props: logos, speed, direction, width, logoHeight, gap, pauseOnHover, hoverSpeed, fadeOut, fadeOutColor, scaleOnHover, renderItem, ariaLabel.\n"
        ),
    }
}

# ══════════════════════════════════════════════════════════════════════════════
# TEXT ANIMATIONS & HERO SECTIONS (add your templates here later)
# ══════════════════════════════════════════════════════════════════════════════
# e.g., "Hero1": {"file": "components/Hero1.tsx", "source_path": "templates/hero/Hero1.tsx", "type": "hero", ...}


def get_background_names() -> list:
    """Return list of component names with type='background'."""
    return [name for name, comp in DESIGN_COMPONENTS.items() if comp.get("type") == "background"]


def get_hero_names() -> list:
    """Return list of component names with type='hero'."""
    return [name for name, comp in DESIGN_COMPONENTS.items() if comp.get("type") == "hero"]


def get_component_names() -> list:
    """Return list of component names with type='component'."""
    return [name for name, comp in DESIGN_COMPONENTS.items() if comp.get("type") == "component"]


def get_all_component_files() -> dict:
    """Returns a dict of {filepath: source_code} for all design components,
    ready to be merged into BASE_FILES."""
    files = {}
    for comp in DESIGN_COMPONENTS.values():
        if "source_path" in comp:
            files[comp["file"]] = read_template(comp["source_path"])
        else:
            files[comp["file"]] = comp.get("source", "")
    return files


def get_all_usage_hints() -> str:
    """Returns a combined string of all usage hints for injecting into the LLM prompt."""
    hints = []
    for comp in DESIGN_COMPONENTS.values():
        hints.append(comp["usage_hint"])
    return "\n".join(hints)
