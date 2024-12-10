from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.a import greet
from app.b import add_numbers

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        print(f"Ошибка: {e}")
        return HTMLResponse(content="Произошла ошибка", status_code=500)

@app.get("/greet/{name}")
async def read_greet(name: str):
    return {"message": greet(name)}

@app.get("/add/{a}/{b}")
async def read_add(a: float, b: float):
    result = add_numbers(a, b)
    return {"result": result}
