import os
import time
import json
import operator
import random
from typing import List, TypedDict, Annotated

from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI
from langgraph.graph import StateGraph, END

import prompts
from utils import strip_fences, fix_jsx_wrapper, sanitize_imports, BASE_FILES
from renderer import assemble_portfolio_tsx

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

async def profile_analyzer(state: PortfolioState):
    print("[Agent 1 - Profile Analyzer] Starting...")
    t0 = time.time()
    llm = get_llm(temperature=0.1, model_name="meta/llama-3.1-8b-instruct") # Fast, deterministic
    
    prompt = prompts.get_profile_analyzer_prompt(
        state.get('github_data', ''),
        state.get('linkedin_url', ''),
        state.get('cv_text', '')
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
    prompt = prompts.get_content_writer_prompt(state.get("profile_summary", ""))
    
    resp = await llm.ainvoke([
        HumanMessage(content=prompt),
    ])
    print(f"[Agent 2 - Content Writer] Done in {time.time()-t0:.1f}s")
    return {"portfolio_content": resp.content}

async def code_generator(state: PortfolioState):
    print("[Agent 3 - Code Generator] Starting...")
    t0 = time.time()
    
    content = state.get("portfolio_content", "")
    
    hero_effects = ["RippleGrid", "Lightning", "Beams", "GradientBlinds", "DarkVeil", "Silk", "ColorBends", "Prism"]
    random.shuffle(hero_effects)
    hero_effects_str = ", ".join(hero_effects)

    backgrounds = ["ShapeGrid", "DotField"]
    random.shuffle(backgrounds)
    backgrounds_str = ", ".join(backgrounds)

    prompt = prompts.get_code_generator_prompt(content, backgrounds_str, hero_effects_str)
    
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
        max_tokens=4096,
        response_format={"type": "json_object"}
    )
    
    raw_content = completion.choices[0].message.content
    elapsed = time.time() - t0
    print(f"[Agent 3 - Code Generator] LLM responded in {elapsed:.1f}s ({len(raw_content)} chars)")
    
    try:
        layout_data = json.loads(strip_fences(raw_content))
    except Exception as e:
        print(f"Error parsing JSON: {e}. Falling back to default layout.")
        layout_data = {"background": "ShapeGrid", "hero_effect": "RippleGrid", "sections": [{"type": "Hero", "props": {"title": "Error generating layout", "subtitle": ""}}]}
        
    code = assemble_portfolio_tsx(layout_data)
    
    files = BASE_FILES.copy()
    
    import design_templates
    design_files = design_templates.get_all_component_files()
    files.update(design_files)
    
    files["pages/portfolio.tsx"] = code
        
    print(f"[Agent 3 - Code Generator] Total time: {time.time()-t0:.1f}s")
    return {"portfolio_code": json.dumps(files)}

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

        prompt = prompts.get_modifier_prompt(existing_code, state.get("modification_request", ""))
        resp = await llm.ainvoke([HumanMessage(content=prompt)])
        
        code = strip_fences(resp.content)
        code = fix_jsx_wrapper(code)
        code = sanitize_imports(code)
        
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
