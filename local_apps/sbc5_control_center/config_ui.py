#!/usr/bin/env python3
import json, os, tempfile, time, copy, re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from dashboard_sync import dashboard_status, sync_dashboard_card, DashboardSyncError
CARD_JSON = Path('/dashboard_card.json')
UPDATE_CARD_JSON = Path('/update_status_card.json')
UI_OVERRIDE_DIR = Path('/data/ui_updates')
CARD_JSON_OVERRIDE = UI_OVERRIDE_DIR / 'dashboard_card.json'
UPDATE_CARD_JSON_OVERRIDE = UI_OVERRIDE_DIR / 'update_status_card.json'
CARD_UI_VERSION_FILE = Path('/data/card_ui_version')
LOVELACE_BACKUP_DIR = Path('/data/lovelace_backups')
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
    return '3.1.28'

APP_VERSION = _release_version()

def _release_card_ui_version():
    try:
        data = json.loads(RELEASE_JSON.read_text(encoding='utf-8'))
        return str(data.get('card_ui_version') or data.get('version') or APP_VERSION).strip() or APP_VERSION
    except Exception:
        return APP_VERSION

def current_card_ui_version():
    try:
        value = CARD_UI_VERSION_FILE.read_text(encoding='utf-8').strip()
        if value:
            return value
    except Exception:
        pass
    return _release_card_ui_version()

def current_card_json_path():
    return CARD_JSON_OVERRIDE if CARD_JSON_OVERRIDE.is_file() else CARD_JSON

def current_update_card_json_path():
    return UPDATE_CARD_JSON_OVERRIDE if UPDATE_CARD_JSON_OVERRIDE.is_file() else UPDATE_CARD_JSON

def _runtime_versioned_card(card):
    """Normalize embedded card markers to the release Card UI version.

    Browser-session Lovelace sync uses these template endpoints directly.  Returning
    raw packaged JSON previously allowed an old Update Card marker (2.8.34) to be
    written back even while the App and Card UI were already 3.1.28.
    """
    version = current_card_ui_version()
    def walk(value):
        if isinstance(value, str):
            value = re.sub(r'Card UI v\d+\.\d+\.\d+', f'Card UI v{version}', value)
            value = re.sub(r'Update Card v\d+\.\d+\.\d+', f'Update Card v{version}', value)
            value = re.sub(r'SBC5CC \d+\.\d+\.\d+', f'SBC5CC {version}', value)
            return value
        if isinstance(value, list):
            return [walk(v) for v in value]
        if isinstance(value, dict):
            return {k: walk(v) for k, v in value.items()}
        return value
    return walk(card)

OPTIONS = Path('/data/options.json')
RELOAD = Path('/data/config_ui_reload.request')
HTML = Path('/config_ui/index.html')
PORT = int(os.environ.get('RPI5CC_CONFIG_UI_PORT', '8099'))
CPU_STATE = Path('/data/cpu_profile_state.json')
CPU_STATE_SCHEMA = 2
GPU_STATE = Path('/data/gpu_profile_state.json')
GPU_STATE_SCHEMA = 1
ETHERNET_STATE = Path('/data/ethernet_settings.json')
ETHERNET_STATE_SCHEMA=1
ETHERNET_KEYS=('ethernet_eee_mode','ethernet_health_monitor_enabled','ethernet_flap_window_minutes','ethernet_flap_degraded_threshold')

DEFAULTS = {
  'custom_curve_1_name':'Zbalansowana','custom_target_temp_c':50.0,
  'cooling_control_mode':'automatic','cooling_auto_style':'balanced',
  'hybrid_correction_limit_percent':10,'custom_min_pwm_percent':29,
  'custom_target_pwm_percent':55,'custom_max_pwm_percent':100,
  'manual_hysteresis_c':1.0,'custom_hysteresis_dense_c':0.75,
  'custom_hysteresis_outer_c':1.0,'apply_custom_on_start':False,
  'adaptive_pwm_enabled':True,'adaptive_pwm_deadband_c':0.75,
  'adaptive_pwm_interval_seconds':10,'adaptive_pwm_down_confirm_cycles':2,
  'restart_policy':'ask','pre_restart_config_check':True,'restart_notice_on_start':True,
  'post_update_restart_prompt':True,'native_restart_repair':True,
  'ethernet_eee_mode':'auto','ethernet_health_monitor_enabled':True,'ethernet_flap_window_minutes':60,'ethernet_flap_degraded_threshold':3,
  'actionable_mobile_notifications':True,'mobile_notify_service':'auto',
  'update_check_enabled':True,'update_check_interval_hours':6,'update_notify':True,
  'app_update_manifest_url':'https://raw.githubusercontent.com/krlmdfk/sbc5-control-center/main/local_apps/sbc5_control_center/release.json','local_package_updates_enabled':True,
  'local_package_scan_interval_minutes':2,'local_package_keep_processed':True,'local_package_cleanup_enabled':True,'local_package_processed_retention':2,'local_package_failed_retention':2,
  'multicore_telemetry_enabled':True,'multicore_workers':'auto',
  'config_txt_manager':{'enabled':False,'sync_interval_seconds':30,'advanced_mode':False},
  'config_cpu_profile':'factory',
  'config_cpu':{'arm_freq':'auto','arm_freq_min':'auto','over_voltage':'auto','over_voltage_min':'auto','over_voltage_delta':'auto','force_turbo':'auto','initial_turbo':'auto','temp_limit':'auto'},
  'config_gpu_profile':'factory',
  'config_gpu':{'core_freq':'auto','core_freq_min':'auto','isp_freq':'auto','isp_freq_min':'auto','v3d_freq':'auto','v3d_freq_min':'auto','gpu_freq_min':'auto'},
  'config_power_usb':{'usb_max_current_enable':'auto','power_force_3v3_pwm':'auto'},
  'config_pcie_rp1':{'pciex4_reset':'auto'},
  'config_boot_kernel':{'auto_initramfs':'auto','arm_64bit':'auto','boot_ramdisk':'auto','sha256':'auto','set_reboot_arg1':'auto','kernel':'auto','cmdline':'auto','os_prefix':'auto'},
  'config_hardware':{'camera_auto_detect':'auto','display_auto_detect':'auto'},
  'config_uart_debug':{'enable_uart':'auto','enable_rp1_uart':'auto','uart_2ndstage':'auto'},
  'config_video':{'enable_tvout':'auto','disable_overscan':'auto','disable_fw_kms_setup':'auto','max_framebuffers':'auto','hdmi_enable_4kp60':'auto'},
  'config_device_tree':{'device_tree':'auto','overlay_prefix':'auto'},
  'config_compatibility':{'arm_boost':'auto','audio_pwm_mode':'auto'},
  'config_custom_parameters':[],
  'section_ai_cooling_enabled':False,'ai_cooling_mode':'learning','ai_cooling_assist_limit_percent':5,'ai_cooling_min_samples':30,
  'section_adaptive_advanced_enabled':False,'section_notifications_enabled':True,
  'section_updates_enabled':True,'section_telemetry_enabled':True,
  'section_cpu_enabled':False,'section_gpu_enabled':False,'section_power_usb_enabled':False,
  'section_pcie_rp1_enabled':False,'section_boot_kernel_enabled':False,'section_hardware_enabled':False,
  'section_uart_debug_enabled':False,'section_video_enabled':False,'section_device_tree_enabled':False,
  'section_compatibility_enabled':False,'section_custom_parameters_enabled':False
}

SECTION_KEYS = {
 'profile':['custom_curve_1_name','custom_target_temp_c','cooling_control_mode'],
 'safety':['restart_policy','pre_restart_config_check','restart_notice_on_start','post_update_restart_prompt','native_restart_repair'],
 'ethernet':['ethernet_eee_mode','ethernet_health_monitor_enabled','ethernet_flap_window_minutes','ethernet_flap_degraded_threshold'],
 'automatic':['cooling_auto_style'],
 'hybrid':['hybrid_correction_limit_percent','custom_min_pwm_percent','custom_target_pwm_percent','custom_max_pwm_percent','custom_hysteresis_dense_c','custom_hysteresis_outer_c'],
 'manual':['manual_hysteresis_c','custom_min_pwm_percent','custom_target_pwm_percent','custom_max_pwm_percent'],
 'ai_cooling':['ai_cooling_mode','ai_cooling_assist_limit_percent','ai_cooling_min_samples'],
 'adaptive':['adaptive_pwm_deadband_c','adaptive_pwm_interval_seconds','adaptive_pwm_down_confirm_cycles'],
 'notifications':['actionable_mobile_notifications','mobile_notify_service'],
 'updates':['update_check_enabled','update_check_interval_hours','update_notify','app_update_manifest_url','local_package_updates_enabled','local_package_scan_interval_minutes','local_package_keep_processed','local_package_cleanup_enabled','local_package_processed_retention','local_package_failed_retention'],
 'telemetry':['multicore_telemetry_enabled','multicore_workers'],
 'config_manager':['config_txt_manager'],
 'cpu':['config_cpu_profile','config_cpu'],'gpu':['config_gpu_profile','config_gpu'],'power_usb':['config_power_usb'],'pcie_rp1':['config_pcie_rp1'],
 'boot_kernel':['config_boot_kernel'],'hardware':['config_hardware'],'uart_debug':['config_uart_debug'],
 'video':['config_video'],'device_tree':['config_device_tree'],'compatibility':['config_compatibility'],
 'custom_parameters':['config_custom_parameters']
}
SECTION_TOGGLE = {
 'ai_cooling':'section_ai_cooling_enabled',
 'adaptive':'section_adaptive_advanced_enabled','adaptive_advanced':'section_adaptive_advanced_enabled',
 'notifications':'section_notifications_enabled','updates':'section_updates_enabled','telemetry':'section_telemetry_enabled',
 'cpu':'section_cpu_enabled','gpu':'section_gpu_enabled','power_usb':'section_power_usb_enabled','pcie_rp1':'section_pcie_rp1_enabled',
 'boot_kernel':'section_boot_kernel_enabled','hardware':'section_hardware_enabled','uart_debug':'section_uart_debug_enabled',
 'video':'section_video_enabled','device_tree':'section_device_tree_enabled','compatibility':'section_compatibility_enabled',
 'custom_parameters':'section_custom_parameters_enabled'
}
LEGACY_SECTION_TOGGLE = {
 'ai_cooling':'section_ai_cooling_enabled','adaptive_advanced':'section_adaptive_advanced_enabled','notifications':'section_notifications_enabled','updates':'section_updates_enabled',
 'telemetry':'section_telemetry_enabled','cpu':'section_cpu_enabled','gpu':'section_gpu_enabled','power_usb':'section_power_usb_enabled',
 'pcie_rp1':'section_pcie_rp1_enabled','boot_kernel':'section_boot_kernel_enabled','hardware':'section_hardware_enabled',
 'uart_debug':'section_uart_debug_enabled','video':'section_video_enabled','device_tree':'section_device_tree_enabled',
 'compatibility':'section_compatibility_enabled','custom_parameters':'section_custom_parameters_enabled'
}



def normalize_section_flags(obj):
    out = copy.deepcopy(obj) if isinstance(obj,dict) else {}
    legacy = out.pop('sections', {})
    if isinstance(legacy,dict):
        for old,new in LEGACY_SECTION_TOGGLE.items():
            if new not in out and old in legacy:
                out[new] = bool(legacy[old])
    return out

def deep_merge(a,b):
    out = copy.deepcopy(a) if isinstance(a,dict) else {}
    for k,v in (b or {}).items():
        if isinstance(v,dict) and isinstance(out.get(k),dict): out[k]=deep_merge(out[k],v)
        else: out[k]=copy.deepcopy(v)
    return out

CPU_PROFILES = {
  'factory': {'arm_freq':'auto','arm_freq_min':'auto','over_voltage':'auto','over_voltage_min':'auto','over_voltage_delta':'auto','force_turbo':'auto','initial_turbo':'auto','temp_limit':'auto'},
  'mild': {'arm_freq':'2500','arm_freq_min':'auto','over_voltage':'auto','over_voltage_min':'auto','over_voltage_delta':'auto','force_turbo':'auto','initial_turbo':'auto','temp_limit':'auto'},
  'balanced': {'arm_freq':'2600','arm_freq_min':'auto','over_voltage':'auto','over_voltage_min':'auto','over_voltage_delta':'auto','force_turbo':'auto','initial_turbo':'auto','temp_limit':'auto'},
  'performance': {'arm_freq':'2800','arm_freq_min':'auto','over_voltage':'auto','over_voltage_min':'auto','over_voltage_delta':'auto','force_turbo':'auto','initial_turbo':'auto','temp_limit':'auto'},
  'experimental': {'arm_freq':'3000','arm_freq_min':'auto','over_voltage':'auto','over_voltage_min':'auto','over_voltage_delta':'auto','force_turbo':'auto','initial_turbo':'auto','temp_limit':'auto'},
}
CPU_PROFILE_NAMES = set(CPU_PROFILES) | {'advanced'}


GPU_PROFILES = {
  # factory removes all SBC5-owned GPU clock entries and lets firmware choose.
  'factory': {'core_freq':'auto','core_freq_min':'auto','isp_freq':'auto','isp_freq_min':'auto','v3d_freq':'auto','v3d_freq_min':'auto','gpu_freq_min':'auto'},
  # Conservative underclock for headless/light GPU workloads. Minimum clocks stay at Pi 5 defaults.
  'eco': {'core_freq':'850','core_freq_min':'500','isp_freq':'850','isp_freq_min':'500','v3d_freq':'900','v3d_freq_min':'500','gpu_freq_min':'auto'},
  # Mild daily profile: small uplift over the Pi 5 reference 910/910/960 MHz clocks.
  'balanced': {'core_freq':'950','core_freq_min':'500','isp_freq':'950','isp_freq_min':'500','v3d_freq':'1000','v3d_freq_min':'500','gpu_freq_min':'auto'},
  'performance': {'core_freq':'1000','core_freq_min':'500','isp_freq':'1000','isp_freq_min':'500','v3d_freq':'1100','v3d_freq_min':'500','gpu_freq_min':'auto'},
  # Upper protective preset. Stability is silicon/firmware/cooling dependent and not guaranteed.
  'experimental': {'core_freq':'1100','core_freq_min':'500','isp_freq':'1100','isp_freq_min':'500','v3d_freq':'1200','v3d_freq_min':'500','gpu_freq_min':'auto'},
}
GPU_PROFILE_NAMES = set(GPU_PROFILES) | {'advanced'}

def _norm_cpu_value(v):
    if v is None: return 'auto'
    s=str(v).strip().lower()
    return 'auto' if s in ('','none','null','auto') else s

def infer_cpu_profile(cfg):
    cfg=cfg if isinstance(cfg,dict) else {}
    normalized={k:_norm_cpu_value(cfg.get(k,'auto')) for k in DEFAULTS['config_cpu']}
    for name,profile in CPU_PROFILES.items():
        if all(normalized.get(k,'auto') == _norm_cpu_value(v) for k,v in profile.items()):
            return name
    return 'advanced'


def infer_gpu_profile(cfg):
    cfg=cfg if isinstance(cfg,dict) else {}
    normalized={k:_norm_cpu_value(cfg.get(k,'auto')) for k in DEFAULTS['config_gpu']}
    for name,profile in GPU_PROFILES.items():
        if all(normalized.get(k,'auto') == _norm_cpu_value(v) for k,v in profile.items()):
            return name
    return 'advanced'

def _atomic_json_write(path, data):
    path=Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=str(path.parent))
    try:
        with os.fdopen(fd,'w') as f:
            json.dump(data,f,ensure_ascii=False,indent=2); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        try: os.unlink(tmp)
        except FileNotFoundError: pass

def read_cpu_state():
    try:
        st=json.loads(CPU_STATE.read_text()) if CPU_STATE.exists() else {}
        if not isinstance(st,dict) or int(st.get('schema',0)) != CPU_STATE_SCHEMA: return {}
        if st.get('requested_profile') not in CPU_PROFILE_NAMES: return {}
        if not isinstance(st.get('requested_config',{}),dict): return {}
        return st
    except Exception:
        return {}

def persist_cpu_state(options, source='config_ui', explicit=True):
    profile=str(options.get('config_cpu_profile','factory')).strip().lower()
    if profile not in CPU_PROFILE_NAMES: raise ValueError('Nieprawidłowy profil CPU / OC')
    cfg=copy.deepcopy(options.get('config_cpu') if isinstance(options.get('config_cpu'),dict) else {})
    if profile in CPU_PROFILES: cfg=copy.deepcopy(CPU_PROFILES[profile])
    state={
        'schema':CPU_STATE_SCHEMA,
        'enabled':bool(options.get('section_cpu_enabled',False)),
        'requested_profile':profile,
        'requested_config':cfg,
        'source':source,
        'explicit':bool(explicit),
        'updated':time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    _atomic_json_write(CPU_STATE,state)
    return state

def read_gpu_state():
    try:
        st=json.loads(GPU_STATE.read_text()) if GPU_STATE.exists() else {}
        if not isinstance(st,dict) or int(st.get('schema',0)) != GPU_STATE_SCHEMA: return {}
        if st.get('requested_profile') not in GPU_PROFILE_NAMES: return {}
        if not isinstance(st.get('requested_config',{}),dict): return {}
        return st
    except Exception:
        return {}

def persist_gpu_state(options, source='config_ui', explicit=True):
    profile=str(options.get('config_gpu_profile','factory')).strip().lower()
    if profile not in GPU_PROFILE_NAMES: raise ValueError('Nieprawidłowy profil GPU / V3D / ISP')
    cfg=copy.deepcopy(options.get('config_gpu') if isinstance(options.get('config_gpu'),dict) else {})
    if profile in GPU_PROFILES: cfg=copy.deepcopy(GPU_PROFILES[profile])
    state={
        'schema':GPU_STATE_SCHEMA,
        'enabled':bool(options.get('section_gpu_enabled',False)),
        'requested_profile':profile,
        'requested_config':cfg,
        'source':source,
        'explicit':bool(explicit),
        'updated':time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    _atomic_json_write(GPU_STATE,state)
    return state

def read_ethernet_state():
    try:
        st=json.loads(ETHERNET_STATE.read_text()) if ETHERNET_STATE.exists() else {}
        if not isinstance(st,dict) or int(st.get('schema',0)) != ETHERNET_STATE_SCHEMA: return {}
        if str(st.get('ethernet_eee_mode','')).lower() not in ('auto','off'): return {}
        return st
    except Exception:
        return {}

def persist_ethernet_state(options, source='config_ui', explicit=True):
    mode=str(options.get('ethernet_eee_mode','auto')).strip().lower()
    if mode not in ('auto','off'): mode='auto'
    try: window=max(1,min(1440,int(options.get('ethernet_flap_window_minutes',60))))
    except Exception: window=60
    try: threshold=max(1,min(50,int(options.get('ethernet_flap_degraded_threshold',3))))
    except Exception: threshold=3
    state={
        'schema':ETHERNET_STATE_SCHEMA,
        'ethernet_eee_mode':mode,
        'ethernet_health_monitor_enabled':bool(options.get('ethernet_health_monitor_enabled',True)),
        'ethernet_flap_window_minutes':window,
        'ethernet_flap_degraded_threshold':threshold,
        'source':source,
        'explicit':bool(explicit),
        'updated':time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    _atomic_json_write(ETHERNET_STATE,state)
    return state

def read_options():
    try: cur=json.loads(OPTIONS.read_text()) if OPTIONS.exists() else {}
    except Exception: cur={}
    cur=normalize_section_flags(cur)
    if 'config_cpu_profile' not in cur:
        cur['config_cpu_profile']=infer_cpu_profile(cur.get('config_cpu',{}))
    if 'config_gpu_profile' not in cur:
        cur['config_gpu_profile']=infer_gpu_profile(cur.get('config_gpu',{}))
    out=deep_merge(DEFAULTS, cur)
    if out.get('config_gpu_profile') in GPU_PROFILES:
        out['config_gpu']=copy.deepcopy(GPU_PROFILES[out['config_gpu_profile']])
    # v2.7.2 single source of truth: the persistent CPU state wins over a
    # transient/default Supervisor options snapshot during startup.
    st=read_cpu_state()
    if st:
        out['section_cpu_enabled']=bool(st.get('enabled',out.get('section_cpu_enabled',False)))
        out['config_cpu_profile']=st['requested_profile']
        out['config_cpu']=copy.deepcopy(st.get('requested_config') or out.get('config_cpu') or {})
        if out['config_cpu_profile'] in CPU_PROFILES:
            out['config_cpu']=copy.deepcopy(CPU_PROFILES[out['config_cpu_profile']])
    # v2.8.15: persistent GPU state wins over transient/default Supervisor options.
    gst=read_gpu_state()
    if gst:
        out['section_gpu_enabled']=bool(gst.get('enabled',out.get('section_gpu_enabled',False)))
        out['config_gpu_profile']=gst['requested_profile']
        out['config_gpu']=copy.deepcopy(gst.get('requested_config') or out.get('config_gpu') or {})
        if out['config_gpu_profile'] in GPU_PROFILES:
            out['config_gpu']=copy.deepcopy(GPU_PROFILES[out['config_gpu_profile']])
        if out['section_gpu_enabled']:
            out.setdefault('config_txt_manager',{})['enabled']=True
    # v3.1.28: persistent Ethernet/EEE state wins over a Supervisor-restored default snapshot.
    est=read_ethernet_state()
    if est:
        for key in ETHERNET_KEYS:
            if key in est: out[key]=copy.deepcopy(est[key])
    return out

def atomic_write(data, notify=True):
    _atomic_json_write(OPTIONS,data)
    if notify: RELOAD.write_text(str(int(time.time())))

def _read_json(path):
    try:
        data=json.loads(Path(path).read_text())
        return data if isinstance(data,dict) else {}
    except Exception:
        return {}

def runtime_summary():
    # telemetry.json is the same normalized snapshot exported to Home Assistant.
    telemetry=_read_json('/homeassistant/sbc5_control_center/telemetry.json')

    calibration=_read_json('/data/fan_calibration.json')
    if not calibration and isinstance(telemetry.get('fan_calibration'),dict):
        calibration=copy.deepcopy(telemetry['fan_calibration'])
    if calibration:
        rpm_map=calibration.get('rpm_map')
        if isinstance(rpm_map,list):
            calibration['map_points']=len(rpm_map)
        else:
            calibration['map_points']=int(calibration.get('map_points') or 0)

    ai=_read_json('/data/ai_cooling_status.json')
    if not ai and isinstance(telemetry.get('ai_cooling'),dict):
        ai=copy.deepcopy(telemetry['ai_cooling'])

    platform=_read_json('/data/platform_compatibility.json')
    if not platform and isinstance(telemetry.get('platform_compatibility'),dict):
        platform=copy.deepcopy(telemetry['platform_compatibility'])

    return {'telemetry':telemetry,'calibration':calibration,'ai':ai,'platform':platform,'cpu_profile_state':read_cpu_state(),'gpu_profile_state':read_gpu_state(),'requested_cpu_profile':(read_cpu_state().get('requested_profile') if read_cpu_state() else None),'requested_gpu_profile':(read_gpu_state().get('requested_profile') if read_gpu_state() else None)}

def clamp_num(v,lo,hi,float_ok=True):
    try: x=float(v)
    except Exception: raise ValueError('Nieprawidłowa liczba')
    if x<lo or x>hi: raise ValueError(f'Zakres {lo}–{hi}')
    return x if float_ok else int(x)

def _cpu_int_or_auto(cfg,key,lo,hi,label=None):
    raw=_norm_cpu_value(cfg.get(key,'auto'))
    if raw=='auto': return 'auto'
    try: n=int(raw)
    except Exception: raise ValueError(f'{label or key}: wpisz auto albo liczbę całkowitą')
    if n<lo or n>hi: raise ValueError(f'{label or key}: bezpieczny zakres aplikacji {lo}–{hi}')
    return str(n)

def validate_cpu_config(o):
    profile=str(o.get('config_cpu_profile','factory')).strip().lower()
    if profile not in CPU_PROFILE_NAMES: raise ValueError('Nieprawidłowy profil CPU / OC')
    o['config_cpu_profile']=profile
    if profile in CPU_PROFILES:
        o['config_cpu']=copy.deepcopy(CPU_PROFILES[profile])
        return

    cfg=copy.deepcopy(o.get('config_cpu') if isinstance(o.get('config_cpu'),dict) else {})
    # Advanced remains manual, but Control Center still enforces hard safety rails.
    cfg['arm_freq']=_cpu_int_or_auto(cfg,'arm_freq',600,3000,'arm_freq')
    cfg['arm_freq_min']=_cpu_int_or_auto(cfg,'arm_freq_min',600,2400,'arm_freq_min')
    cfg['over_voltage']=_cpu_int_or_auto(cfg,'over_voltage',-16,8,'over_voltage (Legacy)')
    cfg['over_voltage_min']=_cpu_int_or_auto(cfg,'over_voltage_min',-16,8,'over_voltage_min (Legacy)')
    cfg['over_voltage_delta']=_cpu_int_or_auto(cfg,'over_voltage_delta',0,50000,'over_voltage_delta [µV]')
    ft=_norm_cpu_value(cfg.get('force_turbo','auto'))
    if ft not in ('auto','0','1'): raise ValueError('force_turbo: dozwolone auto, 0 albo 1')
    cfg['force_turbo']=ft
    cfg['initial_turbo']=_cpu_int_or_auto(cfg,'initial_turbo',0,60,'initial_turbo [s]')
    cfg['temp_limit']=_cpu_int_or_auto(cfg,'temp_limit',70,85,'temp_limit [°C]')
    if cfg['arm_freq']!='auto' and cfg['arm_freq_min']!='auto' and int(cfg['arm_freq_min'])>int(cfg['arm_freq']):
        raise ValueError('arm_freq_min nie może być większe niż arm_freq')
    o['config_cpu']=cfg


def _gpu_int_or_auto(cfg,key,lo,hi,label=None):
    raw=_norm_cpu_value(cfg.get(key,'auto'))
    if raw=='auto': return 'auto'
    try: n=int(raw)
    except Exception: raise ValueError(f'{label or key}: wpisz auto albo liczbę całkowitą')
    if n<lo or n>hi: raise ValueError(f'{label or key}: zakres ochronny aplikacji {lo}–{hi} MHz')
    return str(n)

def validate_gpu_config(o):
    profile=str(o.get('config_gpu_profile','factory')).strip().lower()
    if profile not in GPU_PROFILE_NAMES: raise ValueError('Nieprawidłowy profil GPU / V3D / ISP')
    o['config_gpu_profile']=profile
    if profile in GPU_PROFILES:
        o['config_gpu']=copy.deepcopy(GPU_PROFILES[profile])
        return
    cfg=copy.deepcopy(o.get('config_gpu') if isinstance(o.get('config_gpu'),dict) else {})
    for key in ('core_freq','isp_freq','v3d_freq'):
        cfg[key]=_gpu_int_or_auto(cfg,key,500,1200,key)
    for key in ('core_freq_min','isp_freq_min','v3d_freq_min','gpu_freq_min'):
        cfg[key]=_gpu_int_or_auto(cfg,key,200,960,key)
    for maximum,minimum in (('core_freq','core_freq_min'),('isp_freq','isp_freq_min'),('v3d_freq','v3d_freq_min')):
        if cfg[maximum]!='auto' and cfg[minimum]!='auto' and int(cfg[minimum])>int(cfg[maximum]):
            raise ValueError(f'{minimum} nie może być większe niż {maximum}')
    if cfg['gpu_freq_min']!='auto':
        gmin=int(cfg['gpu_freq_min'])
        for maximum in ('core_freq','isp_freq','v3d_freq'):
            if cfg[maximum]!='auto' and gmin>int(cfg[maximum]):
                raise ValueError(f'gpu_freq_min nie może być większe niż {maximum}')
    o['config_gpu']=cfg

def validate(data):
    o=read_options(); o=deep_merge(o,normalize_section_flags(data))
    o['custom_curve_1_name']=str(o.get('custom_curve_1_name','Zbalansowana')).strip()[:32] or 'Zbalansowana'
    o['custom_target_temp_c']=clamp_num(o.get('custom_target_temp_c',50),46,65)
    if o.get('cooling_control_mode') not in ('automatic','hybrid','manual'): raise ValueError('Nieprawidłowy tryb sterowania')
    if o.get('cooling_auto_style') not in ('quiet','balanced','performance'): raise ValueError('Nieprawidłowy charakter automatyczny')
    o['hybrid_correction_limit_percent']=clamp_num(o.get('hybrid_correction_limit_percent',10),0,25,False)
    o['custom_min_pwm_percent']=clamp_num(o.get('custom_min_pwm_percent',29),9,70,False)
    o['custom_target_pwm_percent']=clamp_num(o.get('custom_target_pwm_percent',55),15,90,False)
    o['custom_max_pwm_percent']=clamp_num(o.get('custom_max_pwm_percent',100),50,100,False)
    if not (o['custom_min_pwm_percent'] < o['custom_target_pwm_percent'] < o['custom_max_pwm_percent']): raise ValueError('PWM musi spełniać min < cel < max')
    o['manual_hysteresis_c']=clamp_num(o.get('manual_hysteresis_c',1),0.25,5)
    if o.get('ai_cooling_mode') not in ('learning','assist'): raise ValueError('Nieprawidłowy tryb AI Cooling')
    o['ai_cooling_assist_limit_percent']=clamp_num(o.get('ai_cooling_assist_limit_percent',5),1,10,False)
    o['ai_cooling_min_samples']=clamp_num(o.get('ai_cooling_min_samples',30),10,300,False)
    o['custom_hysteresis_dense_c']=clamp_num(o.get('custom_hysteresis_dense_c',0.75),0.25,3)
    o['custom_hysteresis_outer_c']=clamp_num(o.get('custom_hysteresis_outer_c',1),0.25,5)
    o['adaptive_pwm_deadband_c']=clamp_num(o.get('adaptive_pwm_deadband_c',0.75),0.1,1.5)
    o['adaptive_pwm_interval_seconds']=clamp_num(o.get('adaptive_pwm_interval_seconds',10),5,60,False)
    o['adaptive_pwm_down_confirm_cycles']=clamp_num(o.get('adaptive_pwm_down_confirm_cycles',2),1,6,False)
    o['update_check_interval_hours']=clamp_num(o.get('update_check_interval_hours',6),1,24,False)
    o['local_package_scan_interval_minutes']=clamp_num(o.get('local_package_scan_interval_minutes',2),1,60,False)
    o['local_package_keep_processed']=bool(o.get('local_package_keep_processed',True))
    o['local_package_cleanup_enabled']=bool(o.get('local_package_cleanup_enabled',True))
    o['local_package_processed_retention']=clamp_num(o.get('local_package_processed_retention',2),0,20,False)
    o['local_package_failed_retention']=clamp_num(o.get('local_package_failed_retention',2),0,20,False)
    validate_cpu_config(o)
    validate_gpu_config(o)
    for field in set(SECTION_TOGGLE.values()): o[field]=bool(o.get(field,DEFAULTS[field]))
    o.pop('sections',None)
    return o


UPDATE_PACKAGE_DIR = Path('/homeassistant/sbc5_control_center_updates')
LEGACY_UPDATE_PACKAGE_DIRS = (
    Path('/homeassistant/rpi5_control_center_updates'),
    Path('/homeassistant/rpi5_fan_manager_updates'),
)

def _zip_archive_info(path):
    path=Path(path)
    files=[]
    if path.is_dir():
        for item in path.glob('*.zip'):
            try:
                st=item.stat(); files.append((item,st.st_mtime,st.st_size))
            except OSError: pass
    files.sort(key=lambda x:x[1], reverse=True)
    return files

def _update_archive_dirs(name):
    # Canonical plus two historical aliases. Keep paths unique so the same ZIP
    # is never counted twice and retention cannot try to delete it twice.
    dirs=[UPDATE_PACKAGE_DIR/name]
    dirs.extend(path/name for path in LEGACY_UPDATE_PACKAGE_DIRS)
    unique=[]; seen=set()
    for path in dirs:
        key=str(path)
        if key not in seen:
            seen.add(key); unique.append(path)
    return unique

def _zip_archive_info_all(name):
    files=[]
    for path in _update_archive_dirs(name): files.extend(_zip_archive_info(path))
    files.sort(key=lambda x:x[1], reverse=True)
    return files

def update_package_cleanup_status():
    o=read_options()
    processed=_zip_archive_info_all('processed')
    failed=_zip_archive_info_all('failed')
    keep_p=int(o.get('local_package_processed_retention',2)) if o.get('local_package_keep_processed',True) else 0
    keep_f=int(o.get('local_package_failed_retention',2))
    return {'ok':True,'enabled':bool(o.get('local_package_cleanup_enabled',True)),
            'processed':{'count':len(processed),'bytes':sum(x[2] for x in processed),'retention':keep_p},
            'failed':{'count':len(failed),'bytes':sum(x[2] for x in failed),'retention':keep_f}}

def cleanup_update_packages():
    o=read_options(); deleted=[]; freed=0
    policies=[('processed', int(o.get('local_package_processed_retention',2)) if o.get('local_package_keep_processed',True) else 0),
              ('failed', int(o.get('local_package_failed_retention',2)))]
    for name,keep in policies:
        keep=max(0,min(20,keep)); files=_zip_archive_info_all(name)
        for item,_mtime,size in files[keep:]:
            try:
                item.unlink(); deleted.append(str(item)); freed+=size
            except FileNotFoundError: pass
    out=update_package_cleanup_status(); out.update({'deleted':len(deleted),'freed_bytes':freed,'deleted_files':deleted})
    return out

class H(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def send_json(self,obj,status=200):
        body=json.dumps(obj,ensure_ascii=False).encode(); self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        p=self.path.split('?',1)[0]
        if p in ('/','/index.html'):
            body=HTML.read_bytes(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body); return
        if p=='/api/state': self.send_json({'version':APP_VERSION,'card_ui_version':current_card_ui_version(),'options':read_options(),'defaults':DEFAULTS,'runtime':runtime_summary()}); return
        if p=='/api/update_packages/status': self.send_json(update_package_cleanup_status()); return
        if p=='/api/dashboard_card/status':
            try: self.send_json(dashboard_status()); return
            except Exception as e: self.send_json({'ok':False,'error':str(e)},500); return
        if p=='/api/dashboard_card/template':
            try:
                card=_runtime_versioned_card(json.loads(current_card_json_path().read_text(encoding='utf-8')))
                self.send_json({'ok':True,'packaged_version':current_card_ui_version(),'card':card}); return
            except Exception as e: self.send_json({'ok':False,'error':f'Nie można odczytać wzorca karty: {e}'},500); return
        if p=='/api/update_card/template':
            try:
                card=_runtime_versioned_card(json.loads(current_update_card_json_path().read_text(encoding='utf-8')))
                self.send_json({'ok':True,'packaged_version':current_card_ui_version(),'card':card}); return
            except Exception as e: self.send_json({'ok':False,'error':f'Nie można odczytać wzorca karty update: {e}'},500); return
        self.send_error(404)
    def do_POST(self):
        try:
            n=int(self.headers.get('Content-Length','0')); payload=json.loads(self.rfile.read(n) or b'{}')
            if self.path=='/api/save':
                o=validate(payload.get('options',{}))
                atomic_write(o,notify=False)
                persist_cpu_state(o,source='config_ui',explicit=True)
                persist_gpu_state(o,source='config_ui',explicit=True)
                persist_ethernet_state(o,source='config_ui',explicit=True)
                RELOAD.write_text(str(int(time.time())))
                self.send_json({'ok':True,'options':o,'cpu_profile_state':read_cpu_state(),'gpu_profile_state':read_gpu_state()}); return
            if self.path=='/api/reset_section':
                sec=str(payload.get('section','')); confirm=bool(payload.get('confirm',False))
                if not confirm: self.send_json({'ok':False,'error':'Wymagane potwierdzenie'},400); return
                if sec not in SECTION_KEYS: self.send_json({'ok':False,'error':'Nieznana sekcja'},400); return
                o=read_options()
                for k in SECTION_KEYS[sec]: o[k]=json.loads(json.dumps(DEFAULTS[k]))
                if sec in SECTION_TOGGLE: o[SECTION_TOGGLE[sec]]=DEFAULTS[SECTION_TOGGLE[sec]]
                if sec=='config_manager': o['config_txt_manager']['enabled']=False
                o=validate(o)
                atomic_write(o,notify=False)
                if sec=='cpu': persist_cpu_state(o,source='config_ui_reset',explicit=True)
                if sec=='gpu': persist_gpu_state(o,source='config_ui_reset',explicit=True)
                if sec=='ethernet': persist_ethernet_state(o,source='config_ui_reset',explicit=True)
                RELOAD.write_text(str(int(time.time())))
                self.send_json({'ok':True,'options':o,'cpu_profile_state':read_cpu_state(),'gpu_profile_state':read_gpu_state()}); return
            if self.path=='/api/update_packages/cleanup':
                if not bool(payload.get('confirm',False)): self.send_json({'ok':False,'error':'Wymagane potwierdzenie'},400); return
                self.send_json(cleanup_update_packages()); return
            if self.path=='/api/reset_ai_model':
                if not bool(payload.get('confirm',False)): self.send_json({'ok':False,'error':'Wymagane potwierdzenie'},400); return
                for path in ('/data/ai_cooling_model.json','/data/ai_cooling_status.json','/homeassistant/sbc5_control_center/ai_cooling.json'):
                    try: Path(path).unlink()
                    except FileNotFoundError: pass
                self.send_json({'ok':True}); return
            if self.path=='/api/dashboard_card/backup':
                if not bool(payload.get('confirm',False)): self.send_json({'ok':False,'error':'Wymagane potwierdzenie'},400); return
                cfg=payload.get('config')
                if not isinstance(cfg,dict) or not isinstance(cfg.get('views'),list): self.send_json({'ok':False,'error':'Nieprawidłowa konfiguracja dashboardu'},400); return
                LOVELACE_BACKUP_DIR.mkdir(parents=True,exist_ok=True)
                stamp=time.strftime('%Y%m%d-%H%M%S')
                url=str(payload.get('url_path') or 'default').replace('/','_').replace('\\','_')[:80]
                path=LOVELACE_BACKUP_DIR/f'{stamp}_{url}_browser.json'
                path.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
                self.send_json({'ok':True,'backup':str(path)}); return
            if self.path=='/api/dashboard_card/sync':
                if not bool(payload.get('confirm',False)): self.send_json({'ok':False,'error':'Wymagane potwierdzenie'},400); return
                try: self.send_json(sync_dashboard_card(confirm=True)); return
                except DashboardSyncError as e: self.send_json({'ok':False,'error':str(e)},409); return
                except Exception as e: self.send_json({'ok':False,'error':str(e)},500); return
            self.send_json({'ok':False,'error':'Nieznana akcja'},404)
        except ValueError as e: self.send_json({'ok':False,'error':str(e)},400)
        except Exception as e: self.send_json({'ok':False,'error':'Błąd zapisu konfiguracji'},500)

if __name__=='__main__':
    ThreadingHTTPServer(('0.0.0.0',PORT),H).serve_forever()
