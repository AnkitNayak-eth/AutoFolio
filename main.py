from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import sys

# Force stdout/stderr to use utf-8
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from dotenv import load_dotenv
load_dotenv()

from utils import fetch_github_data, extract_pdf_text
from agents import build_gen_graph, build_mod_graph

# ── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(title="AI Portfolio Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

gen_graph = build_gen_graph()
mod_graph = build_mod_graph()

# ── Routes ───────────────────────────────────────────────────────────────────
@app.post("/api/generate")
async def generate_portfolio(
    github_url: str = Form(""),
    linkedin_url: str = Form(""),
    cv_file: Optional[UploadFile] = File(None),
):
    cv_bytes = await cv_file.read() if cv_file else None

    async def event_generator():
        import asyncio
        
        yield f"data: {{ \"status\": \"Booting up Multi-Agent AI system...\", \"progress\": 5 }}\n\n"
        await asyncio.sleep(0.5)
        
        github_data = ""
        if github_url:
            yield f"data: {{ \"status\": \"Scraping GitHub repositories and profile...\", \"progress\": 10 }}\n\n"
            github_data = fetch_github_data(github_url)
            yield f"data: {{ \"status\": \"GitHub analysis complete! 🚀\", \"progress\": 15 }}\n\n"
            await asyncio.sleep(0.5)
            
        if linkedin_url:
            yield f"data: {{ \"status\": \"Processing LinkedIn URL...\", \"progress\": 20 }}\n\n"
            await asyncio.sleep(0.5)
            yield f"data: {{ \"status\": \"LinkedIn profile mapped. 👔\", \"progress\": 25 }}\n\n"
            await asyncio.sleep(0.5)
            
        cv_text = ""
        if cv_bytes:
            yield f"data: {{ \"status\": \"Extracting and parsing CV document...\", \"progress\": 30 }}\n\n"
            cv_text = extract_pdf_text(cv_bytes)
            yield f"data: {{ \"status\": \"CV data successfully ingested. 📄\", \"progress\": 35 }}\n\n"
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
        
        yield f"data: {{ \"status\": \"Delegating context to the Analyzer Agent...\", \"progress\": 40 }}\n\n"
        
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
                            yield f"data: {{ \"status\": \"Analyzer Agent finished: Skills and experience synthesized! 🧠\", \"progress\": 55 }}\n\n"
                            yield f"data: {{ \"status\": \"Passing data to Writer Agent...\", \"progress\": 60 }}\n\n"
                        elif node_name == "writer":
                            yield f"data: {{ \"status\": \"Writer Agent finished: Engaging copy drafted! ✍️\", \"progress\": 75 }}\n\n"
                            yield f"data: {{ \"status\": \"Thinking about a beautiful Next.js UI... (This takes a few seconds) 🎨\", \"progress\": 80 }}\n\n"
                        elif node_name == "generator":
                            yield f"data: {{ \"status\": \"Code Generator Agent finished: React code structured! 💻\", \"progress\": 95 }}\n\n"
                        
                        if state_update and isinstance(state_update, dict) and "portfolio_code" in state_update:
                            yield f"data: {json.dumps({'html': state_update['portfolio_code'], 'status': 'complete', 'progress': 100})}\n\n"
            except asyncio.TimeoutError:
                yield f"data: {{ \"status\": \"Agent is still writing complex Next.js code... ⏳\" }}\n\n"

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
        
        yield f"data: {{ \"status\": \"Modifier Agent is analyzing your request... 🔍\" }}\n\n"
        await asyncio.sleep(0.5)
        yield f"data: {{ \"status\": \"Rewriting Next.js components... ⚡\" }}\n\n"
        
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
                        yield f"data: {{ \"status\": \"Changes applied successfully! 🎉\" }}\n\n"
                        if state_update and isinstance(state_update, dict) and "portfolio_code" in state_update:
                            yield f"data: {json.dumps({'html': state_update['portfolio_code'], 'status': 'complete'})}\n\n"
            except asyncio.TimeoutError:
                yield f"data: {{ \"status\": \"Still modifying code... ⏳\" }}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/")
def root():
    return {"message": "AI Portfolio Generator API – see /docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
