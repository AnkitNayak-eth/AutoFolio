def get_profile_analyzer_prompt(github_data: str, linkedin_url: str, cv_text: str) -> str:
    return (
        "Analyze the following data for a developer portfolio. Create a concise summary (max 300 words) of their core identity, main skills, and key projects.\n\n"
        f"GitHub:\n{github_data}\n\n"
        f"LinkedIn/Other:\n{linkedin_url}\n\n"
        f"CV/Resume:\n{cv_text}"
    )

def get_content_writer_prompt(profile_summary: str) -> str:
    return (
        "You are a portfolio copywriter. Write modern, impactful copy quickly. Do not add filler text.\n\n"
        "Using this profile JSON, write compelling portfolio copy:\n"
        "1) Hero headline + subtitle\n2) About Me (3-4 sentences)\n"
        "3) Skills with categories\n4) Project cards\n5) Experience timeline\n"
        "6) Contact CTA\n\n" + profile_summary
    )

def get_code_generator_prompt(content: str, backgrounds_str: str, hero_effects_str: str) -> str:
    return (
        "You are an AI layout generator for a portfolio website. Based on the following portfolio content, generate a JSON object representing the page layout.\n\n"
        "PORTFOLIO CONTENT:\n" + content + "\n\n"
        "You MUST output valid JSON ONLY, no markdown, no explanation.\n"
        "The JSON should have the following structure:\n"
        "{\n"
        f"  \"background\": \"<CHOOSE_ONE_OF: {backgrounds_str}>\", // Full-screen background\n"
        f"  \"hero_effect\": \"<CHOOSE_ONE_OF: {hero_effects_str}>\", // Hero section visual effect\n"
        "  \"sections\": [\n"
        "    {\n"
        "      \"type\": \"Hero\",\n"
        "      \"props\": {\"name\": \"<EXTRACT_REAL_NAME_FROM_CONTENT_OR_USE_USERNAME>\", \"title\": \"<JOB_TITLE_OR_SPECIALTY>\", \"subtitle\": \"<EXTRACT_DETAILED_BIO_FROM_PORTFOLIO_CONTENT>\"}\n"
        "    },\n"
        "    {\n"
        "      \"type\": \"LogoLoop\",\n"
        "      \"props\": {\"logos\": [{\"src\": \"https://upload.wikimedia.org/wikipedia/commons/a/a7/React-icon.svg\", \"alt\": \"React\"}], \"speed\": 120}\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "IMPORTANT: You MUST use the 'ScrollStack' component specifically for the 'Projects' section. Extract exactly the top 4 projects based on stars and pass them as `items` to ScrollStack.\n"
        "Each ScrollStack item MUST have these fields: {\"title\": \"Project Name\", \"description\": \"2-3 sentence description of what it does\", \"category\": \"e.g. Full-Stack App, Web3, AI/ML\", \"year\": \"2024\", \"techStack\": [\"React\", \"Node.js\", \"...max 5 techs\"], \"highlights\": [\"Key feature 1\", \"Key feature 2\", \"Key feature 3\"], \"link\": \"github_url\", \"homepage\": \"live_demo_url_if_available\"}\n"
        "CRITICAL: When using ScrollStack, you MUST pass an `items` array populated with the user's REAL data from the PORTFOLIO CONTENT.\n"
        "CRITICAL: When generating standard/generic sections (like Experience, Contact), you MUST provide the data as an array of objects in the props (e.g., `\"items\": [{\"name\": \"...\", \"description\": \"...\"}]`) so they can be rendered as cards.\n"
        "CRITICAL: For the Contact section, extract REAL contact info (email, blog/website, twitter, linkedin, social accounts) from the portfolio data. DO NOT use placeholder text like '[Your Email]'.\n"
        "CRITICAL: The Hero subtitle MUST be a detailed, meaningful description extracted directly from the user's bio content. DO NOT output placeholder text.\n"
        "Keep the JSON minimal but ensure it captures the essence of the content."
    )

def get_modifier_prompt(existing_code: str, modification_request: str) -> str:
    return (
        "You are an expert Next.js developer debugging or modifying code.\n"
        "Here is the current code for `pages/portfolio.tsx`:\n\n"
        + existing_code
        + "\n\nUser request or Sandbox Error Log: " + modification_request
        + "\n\nIf the user provided an error, diagnose and fix it completely. If they provided a feature request, implement it beautifully using Tailwind and Framer Motion.\n"
        "Rules:\n"
        "- You may import from: 'framer-motion', 'lucide-react', 'react', 'gsap', 'react-icons/si', and relative paths like '../components/ShapeGrid', '../components/DotField', '../components/RippleGrid', '../components/Lightning', '../components/Beams', '../components/GradientBlinds', '../components/Prism', '../components/DarkVeil', '../components/Silk', '../components/ColorBends', '../components/LogoLoop'.\n"
        "- Do NOT import from any other modules.\n"
        "- CRITICAL: Ensure there is ONLY ONE declaration of the `Portfolio` function. Export as `export default function Portfolio()`.\n"
        "- Return ONLY the modified code for `pages/portfolio.tsx`. NO EXPLANATIONS. NO MARKDOWN TEXT. JUST THE RAW CODE!\n"
    )
