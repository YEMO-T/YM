from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.api import chat, coursewares, auth, knowledge, templates, exports, templates_v2, voice
import traceback

app = FastAPI(title="豆沙包教师助手 API", version="1.0.0")

# 允许前端跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 这里的 * 在开发环境下是方便的，生产环境应改为具体的域名
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ========== 健康检查接口 ==========
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Backend service is running"}
# =================================

# ========== 新增：全局异常捕获（自动打印所有错误） ==========
@app.exception_handler(Exception)
async def catch_all_exceptions(request: Request, exc: Exception):
    # 把详细错误打印到后端终端
    traceback.print_exc()
    # 返回错误信息给前端
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器错误：{str(exc)}"}
    )
# ==========================================================

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(coursewares.router, prefix="/api", tags=["Coursewares"])
app.include_router(knowledge.router, prefix="/api", tags=["Knowledge"])
app.include_router(templates.router, prefix="/api", tags=["Templates"])
app.include_router(templates_v2.router)  # 新模板API，包含前缀
app.include_router(exports.router, prefix="/api", tags=["Exports"])
app.include_router(voice.router, prefix="/api/voice", tags=["Voice"])

@app.get("/")
def read_root():
    return {"message": "Welcome to 豆沙包教师助手 API"}