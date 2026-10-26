#!/usr/bin/env python3
import asyncio, json, os, re, time
from copy import deepcopy
from pathlib import Path

WS_URL = os.environ.get('RPI5CC_HA_WS_URL','ws://supervisor/core/websocket')
TOKEN = os.environ.get('SUPERVISOR_TOKEN','')
CARD_JSON = Path('/dashboard_card.json')
UI_OVERRIDE_DIR = Path('/data/ui_updates')
CARD_JSON_OVERRIDE = UI_OVERRIDE_DIR / 'dashboard_card.json'
CARD_UI_VERSION_FILE = Path('/data/card_ui_version')
BACKUP_DIR = Path('/data/lovelace_backups')
RELEASE_JSON = Path('/release.json')

def _release_version():
    env = os.environ.get('SBC5CC_APP_VERSION', '').strip()
    if env:
        return env
    try:
        data = json.loads(RELEASE_JSON.read_text(encoding='utf-8'))
        version = str(data.get('version') or '').strip()
        if version:
            return version
    except Exception:
        pass
    return '2.8.32'

def _release_card_ui_version():
    try:
        data = json.loads(RELEASE_JSON.read_text(encoding='utf-8'))
        return str(data.get('card_ui_version') or data.get('version') or _release_version()).strip() or _release_version()
    except Exception:
        return _release_version()

def current_card_version():
    try:
        value = CARD_UI_VERSION_FILE.read_text(encoding='utf-8').strip()
        if value:
            return value
    except Exception:
        pass
    return _release_card_ui_version()

def current_card_path():
    return CARD_JSON_OVERRIDE if CARD_JSON_OVERRIDE.is_file() else CARD_JSON

class DashboardSyncError(RuntimeError):
    pass

async def _connect():
    try:
        import websockets
    except Exception as e:
        raise DashboardSyncError(f'Brak biblioteki websockets: {e}')
    if not TOKEN:
        raise DashboardSyncError('Brak SUPERVISOR_TOKEN')
    ws = await websockets.connect(WS_URL, open_timeout=8, close_timeout=3, ping_interval=None, max_size=8*1024*1024)
    first = json.loads(await asyncio.wait_for(ws.recv(), 8))
    if first.get('type') != 'auth_required':
        await ws.close(); raise DashboardSyncError('Nieoczekiwana odpowiedź WebSocket')
    await ws.send(json.dumps({'type':'auth','access_token':TOKEN}))
    auth = json.loads(await asyncio.wait_for(ws.recv(), 8))
    if auth.get('type') != 'auth_ok':
        await ws.close(); raise DashboardSyncError('Home Assistant odrzucił uwierzytelnienie aplikacji')
    return ws

class HAWS:
    def __init__(self, ws): self.ws=ws; self.seq=0
    async def cmd(self, typ, **kwargs):
        self.seq += 1
        payload={'id':self.seq,'type':typ}; payload.update(kwargs)
        await self.ws.send(json.dumps(payload, ensure_ascii=False))
        while True:
            raw = json.loads(await asyncio.wait_for(self.ws.recv(), 12))
            if raw.get('id') != self.seq: continue
            if not raw.get('success', False):
                err=raw.get('error') or {}
                raise DashboardSyncError(f"{typ}: {err.get('message') or err.get('code') or 'błąd'}")
            return raw.get('result')


def _serialized(obj):
    try: return json.dumps(obj, ensure_ascii=False, sort_keys=True)
    except Exception: return ''

def _is_project_card(card):
    if not isinstance(card, dict) or card.get('type') != 'vertical-stack': return False
    cards=card.get('cards') or []
    if not cards or not isinstance(cards[0], dict): return False
    first=cards[0]
    if first.get('primary') != 'Raspberry Pi 5': return False
    s=_serialized(card)
    required=('sensor.sbc5_cpu_temperature','sensor.sbc5_fan_calibration','sensor.sbc5_control_center_update')
    return all(x in s for x in required)

def _card_version(card):
    m=re.search(r'Card UI v(\d+\.\d+\.\d+)', _serialized(card))
    return m.group(1) if m else None

def _walk_cards(cards, prefix):
    found=[]
    if not isinstance(cards,list): return found
    for i,card in enumerate(cards):
        p=prefix+[i]
        if _is_project_card(card):
            found.append((p,card)); continue
        if isinstance(card,dict):
            if isinstance(card.get('cards'),list): found += _walk_cards(card['cards'], p+['cards'])
            if isinstance(card.get('card'),dict):
                c=card['card']
                if _is_project_card(c): found.append((p+['card'],c))
                elif isinstance(c.get('cards'),list): found += _walk_cards(c['cards'], p+['card','cards'])
    return found

def _find_candidates(config, url_path, title):
    out=[]
    views=config.get('views') if isinstance(config,dict) else None
    if not isinstance(views,list): return out
    for vi,view in enumerate(views):
        if not isinstance(view,dict): continue
        for path,card in _walk_cards(view.get('cards') or [], ['views',vi,'cards']):
            out.append({
                'url_path':url_path,
                'dashboard_title':title or ('Domyślny' if url_path in (None,'lovelace') else str(url_path)),
                'view_index':vi,
                'view_title':view.get('title') or view.get('path') or f'Widok {vi+1}',
                'path':path,
                'card_version':_card_version(card),
                'up_to_date':_card_version(card)==current_card_version(),
            })
    return out

def _get_at(root,path):
    cur=root
    for x in path: cur=cur[x]
    return cur

def _set_at(root,path,value):
    cur=root
    for x in path[:-1]: cur=cur[x]
    cur[path[-1]]=value

async def _scan(client):
    try: dashboards=await client.cmd('lovelace/dashboards/list')
    except Exception: dashboards=[]
    dashboards=dashboards if isinstance(dashboards,list) else []
    entries=[]
    seen=set()
    if any(isinstance(d,dict) and d.get('url_path')=='lovelace' for d in dashboards):
        pass
    else:
        entries.append((None,'Domyślny'))
    for d in dashboards:
        if not isinstance(d,dict): continue
        u=d.get('url_path')
        if u in seen: continue
        seen.add(u); entries.append((u,d.get('title') or u))
    candidates=[]; scanned=[]
    for url,title in entries:
        kw={} if url is None else {'url_path':url}
        try:
            cfg=await client.cmd('lovelace/config', force=True, **kw)
            scanned.append({'url_path':url,'title':title,'ok':True})
            candidates += _find_candidates(cfg,url,title)
        except Exception as e:
            scanned.append({'url_path':url,'title':title,'ok':False,'error':str(e)})
    return candidates, scanned

async def _status_async():
    ws=await _connect(); c=HAWS(ws)
    try:
        candidates,scanned=await _scan(c)
        return {'ok':True,'packaged_version':current_card_version(),'candidates':candidates,'scanned':scanned,'count':len(candidates)}
    finally: await ws.close()

def dashboard_status():
    return asyncio.run(_status_async())

async def _sync_async(confirm=False):
    if not confirm: raise DashboardSyncError('Wymagane potwierdzenie')
    card_path=current_card_path()
    if not card_path.exists(): raise DashboardSyncError('Brak wzorcowej karty w obrazie aplikacji ani w trwałym UI override')
    card=json.loads(card_path.read_text(encoding='utf-8'))
    ws=await _connect(); c=HAWS(ws)
    try:
        candidates,_=await _scan(c)
        if len(candidates)==0: raise DashboardSyncError('Nie znaleziono karty SBC5 Control Center w dashboardach storage')
        if len(candidates)>1: raise DashboardSyncError(f'Znaleziono {len(candidates)} kart projektu. Dla bezpieczeństwa automatyczna podmiana została zatrzymana.')
        cand=candidates[0]; url=cand['url_path']; kw={} if url is None else {'url_path':url}
        cfg=await c.cmd('lovelace/config', force=True, **kw)
        # verify target still exists and matches signature
        current=_get_at(cfg,cand['path'])
        if not _is_project_card(current): raise DashboardSyncError('Karta zmieniła się podczas synchronizacji — anulowano zapis')
        if _card_version(current) == current_card_version() and _serialized(current) == _serialized(card):
            return {'ok':True,'already_current':True,'packaged_version':current_card_version(),'target':cand}
        BACKUP_DIR.mkdir(parents=True,exist_ok=True)
        stamp=time.strftime('%Y%m%d-%H%M%S')
        safe=str(url or 'default').replace('/','_')
        backup=BACKUP_DIR/f'{stamp}_{safe}.json'
        backup.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
        new_cfg=deepcopy(cfg); _set_at(new_cfg,cand['path'],card)
        try:
            await c.cmd('lovelace/config/save', config=new_cfg, **kw)
            verify=await c.cmd('lovelace/config', force=True, **kw)
            saved_card=_get_at(verify,cand['path'])
            v=_card_version(saved_card)
            if v != current_card_version():
                raise DashboardSyncError(f'Weryfikacja nie powiodła się (Card UI={v or "brak"})')
            if _serialized(saved_card) != _serialized(card):
                raise DashboardSyncError('Weryfikacja integralności karty nie powiodła się — zapis różni się od wzorca')
        except Exception:
            try: await c.cmd('lovelace/config/save', config=cfg, **kw)
            except Exception: pass
            raise
        return {'ok':True,'packaged_version':current_card_version(),'backup':str(backup),'target':cand}
    finally: await ws.close()

def sync_dashboard_card(confirm=False):
    return asyncio.run(_sync_async(confirm=confirm))

if __name__=='__main__':
    import sys
    try:
        if len(sys.argv)>1 and sys.argv[1]=='sync': print(json.dumps(sync_dashboard_card(confirm='--confirm' in sys.argv),ensure_ascii=False,indent=2))
        else: print(json.dumps(dashboard_status(),ensure_ascii=False,indent=2))
    except Exception as e:
        print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False,indent=2)); raise
