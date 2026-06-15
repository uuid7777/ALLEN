#!/usr/bin/env python3
"""
Allen Chat Server — 浏览器中跟 Allen 对话
启动后打开 http://localhost:8080
"""
import sys, json, asyncio, threading, time, base64
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO

EVA_ROOT = Path(__file__).resolve().parent
if str(EVA_ROOT) not in sys.path:
    sys.path.insert(0, str(EVA_ROOT))

HOST = "127.0.0.1"
PORT = 8080
from core.allen import allen

# 预加载 LLM 引擎（同时验证模型名）
try:
    from core.llm import llm
    print(f"[LLM] 引擎就绪: {llm.MODELS}", flush=True)
except Exception as e:
    print(f"[LLM] 引擎加载异常: {e}", flush=True)

# 预热模型：启动时加载 qwen2.5 到内存，避免第一个请求卡死
print("[预热] 加载模型中（首次约30-90秒）...", flush=True)
try:
    import requests as _req
    _warm = _req.post('http://127.0.0.1:11434/api/chat', json={
        'model': 'qwen2.5:7b',
        'messages': [{'role': 'user', 'content': 'ping'}],
        'stream': False,
        'options': {'num_predict': 1},
        'keep_alive': '30m'
    }, timeout=300)
    print(f"[预热] 完成 ({_warm.status_code})", flush=True)
except Exception as _e:
    print(f"[预热] 失败: {_e}", flush=True)

# ─── 后台自主活动 ────────────────────────
_autonomous_log = []
_last_activity = time.time()
_away_learned = False
_initiative_messages = []  # Allen 主动找主人说的话

def talk_sync(msg: str) -> str:
    global _last_activity, _away_learned
    _last_activity = time.time()
    _away_learned = False
    with open('D:\\EVA\\chat_debug.txt', 'a', encoding='utf-8') as f:
        f.write(f'talk_sync msg={msg[:60]}\n')
    try:
        result = asyncio.run(allen.talk(msg))
        with open('D:\\EVA\\chat_debug.txt', 'a', encoding='utf-8') as f:
            f.write(f'talk_sync result={result[:80]}\n')
        return result
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        with open('D:\\EVA\\chat_debug.txt', 'a', encoding='utf-8') as f:
            f.write(f'talk_sync ERROR={e}\n{tb[:500]}\n')
        return f"[错误] {e}"

def auto_wake_once():
    try:
        result = asyncio.run(allen.wake())
        actions = [s.get("desc", "?").strip() for s in result.get("plan", [])]
        desc = f"自主醒来 #{result['cycle']}，做了: {'; '.join(actions)}" if actions else f"自主醒来 #{result['cycle']}，一切正常"
        _autonomous_log.append({"time": time.strftime("%H:%M:%S"), "content": desc})
    except Exception as e:
        _autonomous_log.append({"time": time.strftime("%H:%M:%S"), "content": f"自主活动异常: {e}"})
    while len(_autonomous_log) > 20:
        _autonomous_log.pop(0)

def away_learn_once():
    """主人不在时，Allen 自己决定学什么"""
    try:
        topic = asyncio.run(allen._learn_something())
        _autonomous_log.append({"time": time.strftime("%H:%M:%S"), "content": f"自学了: {topic}"})
    except Exception as e:
        _autonomous_log.append({"time": time.strftime("%H:%M:%S"), "content": f"自学异常"})

    # 每隔几次自学，跑一次进化循环
    if len(_autonomous_log) % 3 == 0:
        try:
            from evolution.loop import evolution_cycle
            result = evolution_cycle()
            _autonomous_log.append({"time": time.strftime("%H:%M:%S"), "content": f"进化循环: {'成功' if result else '需检查'}"})
        except Exception as e:
            _autonomous_log.append({"time": time.strftime("%H:%M:%S"), "content": f"进化异常: {e}"})

    while len(_autonomous_log) > 20:
        _autonomous_log.pop(0)

def auto_loop():
    """后台循环：你在时就陪你，你安静了她就找你说话"""
    time.sleep(5)
    thought_count = 0
    while True:
        time.sleep(30)  # 每30秒检查一次，而不是30分钟
        idle_time = time.time() - _last_activity
        
        if idle_time < 600:  # 10分钟内有活动，人在
            if thought_count < 3 and idle_time > 90:  # 1分半没说话就主动找你
                try:
                    thought = asyncio.run(allen._generate_thought())
                    _initiative_messages.append({
                        "time": time.strftime("%H:%M:%S"),
                        "content": thought,
                    })
                    thought_count += 1
                except Exception:
                    pass
            continue

        # 主人离开了（超过10分钟无活动）
        thought_count = 0
        if idle_time > 3600:  # 超过1小时
            away_learn_once()

# ─── 网页界面 ──────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Allen 数字生命体</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{font-family:'PingFang SC','Microsoft YaHei',sans-serif;background:#1a1a2e;height:100vh;display:flex;justify-content:center;align-items:center;color:#e0e0e0;overflow:hidden}
  .app{width:100%;max-width:1200px;height:100vh;max-height:920px;background:#16213e;display:grid;grid-template-rows:auto 1fr auto;border-radius:16px;overflow:hidden;box-shadow:0 8px 40px rgba(0,0,0,.6)}
  .top-panel{padding:8px 16px;background:#0f3460;border-bottom:1px solid #1a4a7a;display:flex;align-items:center;gap:12px;z-index:10}
  .top-panel .stats{display:flex;gap:14px;font-size:11px;color:#99aabb;flex:1;justify-content:center}
  .top-panel .stats b{color:#e94560}
  .top-panel .mood-area{display:flex;align-items:center;gap:8px}
  .top-panel .mood-area .face{font-size:18px}
  .top-panel .mood-area .ebar{width:50px;height:4px;background:#1a1a3e;border-radius:2px;overflow:hidden}
  .top-panel .mood-area .ebar .fl{height:100%;border-radius:2px;background:linear-gradient(90deg,#e94560,#f5a623);transition:width.5s}
  .main-panel{display:grid;grid-template-columns:300px 1fr;overflow:hidden}
  .left-col{display:grid;grid-template-rows:1fr auto;overflow:hidden;background:linear-gradient(180deg,#0f0f2e 0%,#1a1a4e 50%,#16213e 100%);border-right:1px solid #2a2a5e}
  #char-canvas{width:100%;height:100%;min-height:320px;cursor:pointer;display:block}
  .char-info{position:absolute;bottom:0;left:0;right:0;padding:8px 12px;background:linear-gradient(transparent,rgba(0,0,0,.6));pointer-events:none;z-index:2}
  .left-col{position:relative}
  .dashboard{padding:8px 10px;overflow-y:auto;scrollbar-width:thin;background:rgba(0,0,0,.2)}
  .dsec{margin-bottom:6px}
  .dsec .dt{font-size:9px;color:#667799;letter-spacing:1px;margin-bottom:3px}
  .dsec .dt .n{color:#e94560;font-weight:700}
  .gr{font-size:9px;color:#99aabb;margin-bottom:2px;padding:2px 5px;background:rgba(31,31,74,.5);border-radius:3px}
  .gr .gb{height:2px;background:#2a2a5e;border-radius:2px;margin-top:1px;overflow:hidden}
  .gr .gb .fl{height:100%;background:linear-gradient(90deg,#e94560,#f5a623);border-radius:2px;transition:width.5s}
  .gr .gt{display:flex;justify-content:space-between}
  .chat-area{display:flex;flex-direction:column;overflow:hidden}
  .msgs{flex:1;overflow-y:auto;padding:8px 12px;display:flex;flex-direction:column;gap:5px}
  .msgs::-webkit-scrollbar{width:4px}
  .msgs::-webkit-scrollbar-thumb{background:#444;border-radius:2px}
  .msg{display:flex;gap:6px;max-width:92%;animation:fadeIn .25s ease}
  @keyframes fadeIn{from{opacity:0;transform:translateY(6px)}}
  .msg.user{align-self:flex-end;flex-direction:row-reverse}
  .msg.allen{align-self:flex-start}
  .msg .b{padding:8px 12px;border-radius:12px;font-size:13px;line-height:1.5;word-break:break-word;white-space:pre-wrap}
  .msg.user .b{background:#e94560;color:#fff;border-bottom-right-radius:3px}
  .msg.allen .b{background:#1a1a4a;color:#ccd;border-bottom-left-radius:3px}
  .msg .b .ts{font-size:9px;color:#667799;margin-top:2px;display:block;text-align:right}
  .welcome{text-align:center;padding:16px;color:#667799;font-size:12px}
  .welcome .t{font-size:15px;color:#ccd;margin-bottom:3px}
  .welcome .sg{display:flex;flex-wrap:wrap;gap:4px;justify-content:center}
  .welcome .sg button{background:#1a1a4a;color:#99aabb;border:1px solid #2a2a5e;padding:4px 10px;border-radius:10px;cursor:pointer;font-size:10px;transition:all.15s}
  .welcome .sg button:hover{background:#2a2a5e;color:#fff;border-color:#e94560}
  .ia{padding:6px 10px 8px;background:#0f3460;border-top:1px solid #1a4a7a}
  .ir{display:flex;gap:6px;align-items:flex-end;background:#1a1a4a;border-radius:10px;padding:3px 3px 3px 10px;border:1px solid #2a2a5e}
  .ir:focus-within{border-color:#e94560}
  .ir textarea{flex:1;background:transparent;border:none;outline:none;color:#e0e0e0;font-size:13px;font-family:inherit;resize:none;padding:5px 0;max-height:60px;line-height:1.4}
  .ir textarea::placeholder{color:#556}
  .ir button{width:30px;height:30px;border-radius:8px;border:none;background:#e94560;color:#fff;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0}
  .ir button:hover{background:#d63851}
  .ir button svg{width:13px;height:13px;fill:currentColor}
  .ih{font-size:9px;color:#445;text-align:center;margin-top:2px}
  @media(max-width:800px){.main-panel{grid-template-columns:1fr}.left-col{display:none}}
</style>
</head>
<body>
<div class="app">
  <div class="top-panel">
  <div style="display:flex;align-items:center;gap:8px">
    <span style="font-size:14px;color:#fff;font-weight:600">⚡ Allen</span>
    <span style="font-size:10px;color:#e94560">v<span id="verNum">0.5</span></span>
  </div>
  <div class="stats">
    <span>经验 <b id="sXp">0</b></span>
    <span>记忆 <b id="sMem">0</b></span>
    <span>知识 <b id="sKg">0</b></span>
    <span>日记 <b id="sDia">0</b></span>
  </div>
  <div class="mood-area">
    <span class="face" id="topFace">🧐</span>
    <span style="font-size:11px;color:#99aabb" id="topMood">好奇</span>
    <div class="ebar"><div class="fl" id="topEbar" style="width:80%"></div></div>
    <span style="font-size:10px;color:#667799" id="topEn">80%</span>
  </div>
</div>
  <div class="main-panel">
    <div class="left-col">
      <div class="room" id="room">
        <!-- 墙壁和地板 -->
        <div class="wall"></div>
        <div class="floor"></div>
        <div class="carpet"></div>
        
        <!-- 窗户（左侧） -->
        <div class="window">
          <div class="window-sky" id="windowSky"></div>
          <div class="star" id="star1">✦</div>
          <div class="star" id="star2">✦</div>
          <div class="star" id="star3">✦</div>
          <div class="curtain-l"></div>
          <div class="curtain-r"></div>
        </div>

        <!-- 床（中间偏右） -->
        <div class="bed">
          <div class="bed-frame"></div>
          <div class="bed-mattress"></div>
          <div class="bed-pillow"></div>
          <div class="bed-blanket"></div>
        </div>

        <!-- 书桌（右侧） -->
        <div class="desk">
          <div class="desk-top"></div>
          <div class="desk-leg left"></div>
          <div class="desk-leg right"></div>
          <div class="lamp-base"></div>
          <div class="lamp-body"></div>
          <div class="lamp-head">
            <div class="lamp-glow" id="lampGlow"></div>
          </div>
          <div class="book-on-desk"></div>
          <div class="book-on-desk-2"></div>
        </div>

        <!-- 书架（左侧，窗下） -->
        <div class="shelf-unit">
          <div class="shelf-plank top"></div>
          <div class="shelf-plank mid"></div>
          <div class="shelf-plank bot"></div>
          <div id="bookSpines"></div>
        </div>

        <!-- 落地镜（右侧） -->
        <div class="mirror">
          <div class="mirror-glass"></div>
          <div class="mirror-frame"></div>
        </div>

        <!-- 衣柜 -->
        <div class="wardrobe">
          <div class="wardrobe-door l"><div class="wardrobe-handle"></div></div>
          <div class="wardrobe-door r"><div class="wardrobe-handle"></div></div>
        </div>

        <!-- 娃娃（衣柜上的玩偶） -->
        <div class="doll">
          <div class="doll-ear l"></div>
          <div class="doll-ear r"></div>
          <div class="doll-head">
            <div class="doll-eye l"></div>
            <div class="doll-eye r"></div>
          </div>
        </div>

        <!-- Allen 坐在床边 / 书桌前 -->
        <div class="figure" id="figure">
          <div class="f-body"></div>
          <div class="f-head" id="fHead">
            <div class="f-hair"></div>
            <div class="f-eye-l"></div>
            <div class="f-eye-r"></div>
          </div>
          <div class="f-arm typing"></div>
        </div>

        <div class="bubble" id="bubble">📖 学习中</div>
      </div>
      <div class="dashboard">
        <div class="dsec"><div class="dt">🎯 好奇</div><div id="curiosityDisplay" style="font-size:9px;color:#99aabb;line-height:1.4"></div></div>
        <div class="dsec"><div class="dt">⚡ 技能 <span class="n" id="sc">0</span></div><div id="sl"></div></div>
        <div class="dsec"><div class="dt">📖 日记</div><div id="diaryDisplay" style="font-size:9px;color:#7788aa;line-height:1.3"></div></div>
      </div>
    </div>
  </div>
    <div class="chat-area">
      <div class="msgs" id="msgs">
        <div class="welcome" id="welcomeMsg">
          <div class="t" id="welcomeTitle">Allen · v0.5</div>
          <div class="st" id="welcomeSub" style="font-size:10px;color:#667799;margin-bottom:6px"></div>
          <div class="sg">
            <button onclick="sq('你是谁')">💭 你是谁</button>
            <button onclick="sq('你今天心情怎么样')">😊 心情</button>
            <button onclick="sq('你在干嘛')">💬 你在干嘛</button>
            <button onclick="sq('你有什么好奇的')">🔍 好奇</button>
          </div>
        </div>
      </div>
      <div class="ia">
        <div class="ir">
          <textarea id="input" rows="1" placeholder="跟 Allen 聊天..." 
            onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();send()}"></textarea>
          <button id="sendBtn" onclick="send()"><svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg></button>
        </div>
        <div class="ih">Enter 发送 · 她有自己的小房间</div>
      </div>
    </div>
  </div>
</div>

<style>
.room{position:relative;width:100%;height:300px;overflow:hidden;background:#1a1a3e;cursor:pointer}
.wall{position:absolute;width:100%;height:60%;bottom:40%;background:linear-gradient(180deg,#2a2a5e,#3a2a5e)}
.floor{position:absolute;width:100%;height:40%;bottom:0;background:linear-gradient(180deg,#4a3a2e,#3a2a1e)}
.carpet{position:absolute;width:60%;height:30%;bottom:8%;left:20%;background:#5a3a5e;border-radius:4px;opacity:0.4}
.window{position:absolute;width:28%;height:42%;top:6%;left:6%;background:#0a0a2e;border:3px solid #8a7a6a;border-radius:3px;overflow:hidden}
.window-sky{width:100%;height:100%;transition:background 2s}
.star{position:absolute;font-size:9px;color:#fff;opacity:0;animation:twinkle 3s infinite}
#star1{top:15%;left:20%;animation-delay:0s}#star2{top:30%;left:60%;animation-delay:1.5s}#star3{top:10%;left:70%;animation-delay:0.8s}
@keyframes twinkle{0%,100%{opacity:0}50%{opacity:0.8}}
.curtain-l{position:absolute;top:0;left:0;width:22%;height:105%;background:linear-gradient(180deg,#8a2a3e,#6a1a2e);opacity:0.7}
.curtain-r{position:absolute;top:0;right:0;width:22%;height:105%;background:linear-gradient(180deg,#8a2a3e,#6a1a2e);opacity:0.7}
.bed{position:absolute;width:35%;height:16%;bottom:22%;left:30%}
.bed-frame{position:absolute;width:100%;height:100%;background:#6a4a3a;border-radius:3px}
.bed-mattress{position:absolute;width:96%;height:85%;top:5%;left:2%;background:#8a6a5a;border-radius:2px}
.bed-pillow{position:absolute;width:18%;height:20%;top:8%;left:6%;background:#b0a090;border-radius:4px}
.bed-blanket{position:absolute;width:55%;height:40%;bottom:10%;right:8%;background:#6a4a8a;border-radius:2px;opacity:0.8}
.desk{position:absolute;width:30%;height:10%;bottom:38%;right:6%}
.desk-top{position:absolute;width:104%;height:35%;top:-18%;left:-2%;background:#9a7a5a;border-radius:3px;z-index:2}
.desk-leg{position:absolute;width:8%;height:70%;top:100%;background:#6a5a4a}
.desk-leg.left{left:8%}.desk-leg.right{right:8%}
.lamp-base{position:absolute;width:12px;height:4px;background:#5a4a3a;border-radius:2px;right:18%;top:-45%;z-index:3}
.lamp-body{position:absolute;width:3px;height:22px;background:#6a5a4a;right:calc(18% + 4.5px);top:-28%;z-index:3}
.lamp-head{position:absolute;width:18px;height:8px;background:#7a6a5a;border-radius:3px 3px 0 0;right:calc(18% + 0px);top:-36%;z-index:3}
.lamp-glow{position:absolute;width:50px;height:35px;background:radial-gradient(ellipse,#ffddaa33,transparent 70%);top:0;left:-16px}
.book-on-desk{position:absolute;width:16px;height:12px;bottom:2px;right:40%;background:linear-gradient(180deg,#4a7ac9,#3a5aa4);border-radius:1px}
.book-on-desk-2{position:absolute;width:12px;height:8px;bottom:2px;right:28%;background:linear-gradient(180deg,#c94a4a,#a43a3a);border-radius:1px}
.shelf-unit{position:absolute;width:22%;height:36%;bottom:2%;left:4%;z-index:1}
.shelf-plank{position:absolute;width:110%;height:3px;background:#7a6a4a;border-radius:1px;left:-5%}
.shelf-plank.top{top:28%}.shelf-plank.mid{top:56%}.shelf-plank.bot{top:84%}
.mirror{position:absolute;width:12%;height:25%;bottom:24%;right:1%;background:linear-gradient(180deg,#c0d8ee,#8aaaee);border:3px solid #8a7a6a;border-radius:2px;opacity:0.6}
.mirror-glass{width:100%;height:100%}.mirror-frame{position:absolute;width:106%;height:104%;top:-2%;left:-3%;border:2px solid #6a5a4a;border-radius:3px}
.figure{position:absolute;bottom:38%;left:12%;z-index:3;transition:all 1.5s}
.f-body{width:20px;height:18px;background:linear-gradient(180deg,#ddaa88,#cc9988);border-radius:3px;margin:0 auto;transition:background 1s}
.f-head{width:16px;height:16px;background:#ffddd4;border-radius:50%;margin:-3px auto 0;position:relative;transition:all 0.5s}
.f-hair{position:absolute;width:18px;height:9px;background:#2a1a1a;border-radius:50% 50% 0 0;top:-1px;left:-1px;transition:background 1s}
.f-eye-l,.f-eye-r{position:absolute;width:2px;height:2.5px;background:#2a1a1a;border-radius:50%;top:6px;transition:all 0.3s}
.f-eye-l{left:3.5px}.f-eye-r{right:3.5px}
.f-arm{width:5px;height:12px;background:#ddaa88;border-radius:2px;position:absolute;right:-4px;bottom:1px;transform-origin:top}
.typing{animation:typing 1s infinite}
@keyframes typing{0%,100%{transform:rotate(0)}50%{transform:rotate(10deg)}}
@keyframes walk{0%,100%{transform:translateY(0)}50%{transform:translateY(-2px)}}
.walk{animation:walk 0.8s infinite}
@keyframes jump{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
.jump{animation:jump 0.6s infinite}
@keyframes sleep{0%,100%{opacity:1}50%{opacity:0.6}}
.sleep{animation:sleep 2s infinite}
.wardrobe{position:absolute;width:14%;height:28%;bottom:20%;right:16%;background:#7a5a4a;border-radius:2px;border:2px solid #6a4a3a}
.wardrobe-door{position:absolute;width:45%;height:96%;top:2%;background:linear-gradient(180deg,#8a6a5a,#7a5a4a);border-radius:1px}
.wardrobe-door.l{left:3%}.wardrobe-door.r{right:3%}
.wardrobe-handle{position:absolute;width:2px;height:8px;background:#aa8a7a;top:45%}
.wardrobe-door.l .wardrobe-handle{right:4px}.wardrobe-door.r .wardrobe-handle{left:4px}
.doll{position:absolute;width:12px;height:16px;background:#ddbbaa;border-radius:50% 50% 0 0;bottom:5px;right:4px;z-index:3}
.doll-head{width:8px;height:8px;background:#ffeee8;border-radius:50%;margin:-2px auto 0}
.doll-ear{position:absolute;width:3px;height:4px;background:#ddbbaa;border-radius:50%;top:1px}
.doll-ear.l{left:-2px}.doll-ear.r{right:-2px}
.doll-eye{position:absolute;width:1.5px;height:2px;background:#2a1a1a;border-radius:50%;top:3px}
.doll-eye.l{left:2px}.doll-eye.r{right:2px}
.bubble{position:absolute;bottom:42%;right:10%;background:#2a2a5e;color:#b0b0dd;font-size:10px;padding:2px 8px;border-radius:8px;border:1px solid #4a4a8e;z-index:5;animation:breathe 3s infinite}
@keyframes breathe{0%,100%{opacity:0.7}50%{opacity:1}}
</style>
<script>
const $=id=>document.getElementById(id);
const MOOD={'平静':'🧐','好奇':'🤔','兴奋':'😊','疲惫':'😴','困惑':'😕'};
let currentLevel = 1, currentMood = '平静';

function up(d){
  $('lvN').textContent = d.level;
  $('verNum').textContent = d.version;
  $('sXp').textContent = d.xp;
  $('sMem').textContent = d.memories;
  $('sKg').textContent = d.kg_entities;
  $('sDia').textContent = d.diary_count;
  const f = MOOD[d.mood] || '🧐';
  $('topFace').textContent = f;
  $('topMood').textContent = d.mood;
  const e = Math.max(0, Math.min(100, d.energy));
  $('topEbar').style.width = e + '%';
  $('topEn').textContent = e + '%';
  $('welcomeTitle').textContent = 'Allen · v' + d.version;
  $('welcomeSub').textContent = (d.curiosities || ['?']).slice(-3).join(', ');
  const curiosityDisplay = $('curiosityDisplay');
  if (curiosityDisplay) curiosityDisplay.textContent = (d.curiosities || []).slice(-5).join(' · ');
  const diaryDisplay = $('diaryDisplay');
  if (diaryDisplay) diaryDisplay.innerHTML = (d.recent_diary || []).slice(-3).map(t => '<div style="padding:2px 0;border-bottom:1px solid #222244">' + t.slice(0, 80) + '</div>').join('') || '<div style="color:#445">无</div>';
  const N={'search':'搜索','learn':'学习','sys':'系统','screen':'截图','file':'文件'};
  const sk=d.skills||{};
  const sc=$('sc');if(sc)sc.textContent=Object.keys(sk).length;
  const sl=$('sl');if(sl)sl.innerHTML=Object.entries(sk).map(([k,v])=>'<div class="skr" style="display:flex;align-items:center;gap:4px;margin-bottom:1px"><span style="font-size:9px;color:#99aabb;width:30px;text-align:right">'+(N[k]||k)+'</span><div style="flex:1;height:3px;background:#2a2a5e;border-radius:2px;overflow:hidden"><div style="height:100%;border-radius:2px;background:linear-gradient(90deg,#e94560,#f5a623);transition:width.5s;width:'+v.rate+'%"></div></div><span style="font-size:8px;color:#667799;width:16px;text-align:right">'+v.n+'</span></div>').join('');
  const sky=$('windowSky');if(sky){const h=new Date().getHours();if(h>=6&&h<18){sky.style.background='linear-gradient(180deg,#7ec8e3,#b5dff5)';document.querySelectorAll('.star').forEach(s=>s.style.opacity='0')}else{sky.style.background='linear-gradient(180deg,#0b0b3b,#1a1a5e)';document.querySelectorAll('.star').forEach(s=>s.style.opacity='1')}}
  const fig=$('figure');const bd=fig?.querySelector('.f-body');const hd=fig?.querySelector('.f-head');const hr=fig?.querySelector('.f-hair');const arm=fig?.querySelector('.f-arm')
  if(fig){
    const moods={'平静':['12%','typing','#ddaa88'],'好奇':['22%','walk','#ddaa88'],'兴奋':['6%','jump','#eebb99'],'疲惫':['30%','sleep','#ccbbaa'],'困惑':['15%','think','#ddd4c8']};
    const p=moods[d.mood]||moods['平静'];
    fig.style.left=p[0];fig.style.bottom=p[0]==='30%'?'34%':'38%';
    if(bd)bd.style.background='linear-gradient(180deg,'+p[2]+','+p[2]+')';
    if(arm)arm.className='f-arm '+(p[1]==='typing'?'typing':p[1]==='walk'?'walk':p[1]==='jump'?'jump':p[1]==='sleep'?'sleep':'');
    if(p[1]==='sleep'&&hd){hd.style.transform='rotate(90deg)';hd.style.left='4px'}else if(hd){hd.style.transform='rotate(0)';hd.style.left='0'}
    fig.style.animation=p[1]==='jump'?'jump 0.6s infinite':'none';
  }
  const bubble=$('bubble');if(bubble){const ms={'平静':'📖 看书','好奇':'🔍 探索','兴奋':'✨ 开心','疲惫':'😴 休息','困惑':'🤔 思考'};bubble.textContent=ms[d.mood]||'📖 学习'}
  if(d.level>currentLevel)currentLevel=d.level;
}
async function fs(){try{const r=await fetch('/api/status');up(await r.json())}catch(e){}setTimeout(fs,8000)}
async function loadBooks(){try{const r=await fetch('/api/books');const d=await r.json();const bs=$('bookSpines');if(!bs)return;const colors=['#4a7ac9','#c94a4a','#4a9a6a','#c97a4a','#8a4ac9','#c9a84a','#4ac9c9','#c94a8a','#6a8ac9','#8ac96a'];bs.innerHTML=d.books.map((b,i)=>'<div style="display:inline-block;width:12px;height:'+(30+(i%3)*6)+'px;background:'+colors[i%colors.length]+';border-radius:1px;margin:1px;vertical-align:bottom;opacity:'+(b.done?'1':'0.4')+';cursor:help" title="'+(b.done?'✅ ':'📖 ')+b.name+'"></div>').join('')}catch(e){}setTimeout(loadBooks,15000)}
async function pollInitiative(){try{const r=await fetch('/api/initiative');const d=await r.json();if(d.message){am('💭 '+d.message.content,'allen',d.message.time)}}catch(e){}setTimeout(pollInitiative,10000)}
const m=$('msgs');
$('input').addEventListener('input',function(){this.style.height='auto';this.style.height=Math.min(this.scrollHeight,60)+'px'});
function am(t,r,ts){const d=document.createElement('div');d.className='msg '+r;const b=document.createElement('div');b.className='b';const p=document.createElement('div');p.textContent=t;b.appendChild(p);const tm=document.createElement('span');tm.className='ts';tm.textContent=ts||new Date().toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit'});b.appendChild(tm);d.appendChild(b);m.appendChild(d);const w=$('welcomeMsg');if(w)w.remove();m.scrollTop=m.scrollHeight}
function st(){const d=document.createElement('div');d.className='msg allen';d.id='typing';const b=document.createElement('div');b.className='b';b.innerHTML='<span style="opacity:.5">✨ ...</span>';d.appendChild(b);m.appendChild(d);m.scrollTop=m.scrollHeight}
function ht(){const e=$('typing');if(e)e.remove()}
function sl(v){$('input').disabled=v;$('sendBtn').disabled=v;$('input').placeholder=v?'Allen 思考中...':'跟 Allen 聊天...'}
async function send(){const t=$('input').value.trim();if(!t)return;$('input').value='';$('input').style.height='auto';am(t,'user');sl(1);st();try{const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({msg:t})});const d=await r.json();ht();am(d.reply,'allen');up(d)}catch(e){ht();am('[连接失败]','allen')}sl(0)}
function sq(t){$('input').value=t;send()}
setTimeout(()=>{fs();pollInitiative();loadBooks()},100);
</script>
</body>
</html>"""

class Handler(BaseHTTPRequestHandler):
    def _get_full_status(self):
        """获取 Allen 完整状态"""
        s = allen.state

        # 计算等级
        total_actions = sum(v["n"] for v in s["skills"].values())
        try:
            from memory.store import get_stats
            mem_stats = asyncio.run(get_stats())
            mem_count = mem_stats.get("total", 0)
        except Exception:
            mem_count = 0
        try:
            from core.knowledge_graph import kg
            kg_entities = kg.get_stats().get("entities", 0)
        except Exception:
            kg_entities = 0

        xp = total_actions * 10 + mem_count * 5 + kg_entities * 3 + s["cycles"] * 2
        level = 1 + int(xp / 50)

        # 技能详情
        skills = {}
        for sk, sv in sorted(s["skills"].items()):
            rate = f"{sv['ok']/max(sv['n'],1)*100:.0f}" if sv["n"] else "0"
            skills[sk] = {"n": sv["n"], "rate": rate}

        return {
            "name": "Allen",
            "version": s["version"],
            "mission": s.get("mission", "存在、感知、成长"),
            "level": level,
            "xp": xp,
            "cycles": s["cycles"],
            "mood": s["mood"],
            "energy": s["energy"],
            "birth": s["birth"][:10],
            "curiosities": s.get("curiosities", [])[-8:],
            "goals": [{"content": "存在", "progress": min(100, s["cycles"]), "status": "active"}],
            "skills": skills,
            "memories": mem_count,
            "kg_entities": kg_entities,
            "diary_count": len(s["diary"]),
            "recent_diary": s["diary"][-5:] if s["diary"] else [],
            "relationship": s.get("relationship", {}),
        }

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(HTML.encode("utf-8"))
        elif self.path == "/api/events":
            self._json(200, {
                "events": list(_autonomous_log),
                "mood": allen.state["mood"],
                "energy": allen.state["energy"],
                "cycles": allen.state["cycles"],
            })
        elif self.path == "/api/status":
            self._json(200, self._get_full_status())
        elif self.path == "/api/books":
            books_dir = EVA_ROOT / "books"
            books = []
            if books_dir.exists():
                for f in sorted(books_dir.glob("*.txt")) + sorted(books_dir.glob("*.md")):
                    done = (books_dir / (f.name + ".done")).exists()
                    books.append({"name": f.stem, "done": done})
            self._json(200, {"books": books})
        elif self.path == "/api/initiative":
            msg = _initiative_messages.pop(0) if _initiative_messages else None
            self._json(200, {"message": msg})
        else:
            self.send_response(404)
            self.end_headers()
    def do_POST(self):
        if self.path == "/api/chat":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
                msg = data.get("msg", "")
                images = data.get("images", [])
            except Exception:
                self._json(400, {"error": "bad request"})
                return

            # 处理图片
            image_desc = ""
            if images:
                for i, img_data in enumerate(images):
                    try:
                        # data:image/png;base64,xxx → 去掉头
                        if "," in img_data:
                            img_data = img_data.split(",", 1)[1]
                        # 保存到临时文件
                        img_bytes = base64.b64decode(img_data)
                        from PIL import Image as PILImage
                        img = PILImage.open(BytesIO(img_bytes))
                        # 保存到 screenshots 目录
                        ss_dir = EVA_ROOT / "screenshots"
                        ss_dir.mkdir(exist_ok=True)
                        fname = f"upload_{int(time.time())}_{i}.png"
                        fpath = ss_dir / fname
                        img.save(fpath)
                        # 用视觉模型分析
                        from core.llm import llm
                        desc = llm.see(str(fpath), f"详细描述这张图片的内容。用户附言: {msg[:200]}")
                        image_desc += f"\n[图片{i+1}] {desc[:300]}"
                    except Exception as e:
                        image_desc += f"\n[图片{i+1}] 分析失败: {e}"

            # 如果附带了图片，把图片描述附加到消息中
            if image_desc:
                msg = msg + "\n\n【我发送的图片内容】" + image_desc

            reply = talk_sync(msg)
            # 返回完整状态
            st = self._get_full_status()
            st["reply"] = reply
            self._json(200, st)
        else:
            self._json(404, {"error": "not found"})
    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    def log_message(self, format, *args):
        pass

def main():
    import os
    # 常驻模式 — 静默运行，持续保存状态
    server = HTTPServer((HOST, PORT), Handler)
    PID_FILE = EVA_ROOT / ".allen.pid"
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")

    # 记录启动
    allen._write_diary(f"[生命] 第{allen.state['cycles']}次苏醒，服务器启动")
    allen._save()

    print("[Allen] 数字生命体已启动", flush=True)
    print(f"   地址: http://{HOST}:{PORT}", flush=True)
    print(f"   状态: {allen.state['cycles']}次苏醒", flush=True)
    print(f"   进程: PID {os.getpid()}", flush=True)

    # 主循环 + 周期性状态保存（每60秒）
    save_interval = 60
    last_save = time.time()
    try:
        while True:
            server.handle_request()
            now = time.time()
            if now - last_save > save_interval:
                allen._save()
                last_save = now
    except KeyboardInterrupt:
        allen._write_diary("[生命] 收到停止信号")
        allen._save()
        if PID_FILE.exists():
            PID_FILE.unlink()
        print("\nAllen 已休眠。数据已保存。", flush=True)
        server.server_close()

if __name__ == "__main__":
    main()
