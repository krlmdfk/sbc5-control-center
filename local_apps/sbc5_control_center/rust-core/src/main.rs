use std::env;
use std::error::Error;
use std::fs::{self, File};
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::process;
use std::thread;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

const VERSION: &str = env!("CARGO_PKG_VERSION");
const SCHEMA: u32 = 1;

#[derive(Clone, Debug)]
struct CpuTimes {
    name: String,
    total: u64,
    idle: u64,
}

fn main() {
    if let Err(err) = run() {
        eprintln!("sbc5-core: {err}");
        process::exit(1);
    }
}

fn run() -> Result<(), Box<dyn Error>> {
    let args: Vec<String> = env::args().collect();
    let command = args.get(1).map(String::as_str).unwrap_or("probe");
    match command {
        "version" | "--version" | "-V" => {
            println!("sbc5-core {VERSION}");
            Ok(())
        }
        "self-test" => self_test(),
        "probe" => {
            let status = option_value(&args, "--status").map(PathBuf::from);
            let mirror = option_value(&args, "--mirror").map(PathBuf::from);
            let payload = collect_status(None)?;
            if let Some(path) = status.as_deref() {
                atomic_write(path, &payload)?;
            }
            if let Some(path) = mirror.as_deref() {
                atomic_write(path, &payload)?;
            }
            println!("{payload}");
            Ok(())
        }
        "daemon" => daemon(&args),
        "help" | "--help" | "-h" => {
            print_help();
            Ok(())
        }
        other => Err(format!("unknown command: {other}").into()),
    }
}

fn print_help() {
    println!(
        "SBC5 Control Center Rust Core {VERSION}\n\
         Usage:\n\
           sbc5-core version\n\
           sbc5-core self-test\n\
           sbc5-core probe [--status PATH] [--mirror PATH]\n\
           sbc5-core daemon --status PATH [--mirror PATH] [--interval SECONDS]"
    );
}

fn option_value(args: &[String], name: &str) -> Option<String> {
    args.windows(2)
        .find(|pair| pair[0] == name)
        .map(|pair| pair[1].clone())
}

fn self_test() -> Result<(), Box<dyn Error>> {
    let payload = collect_status(None)?;
    if !Path::new("/proc").exists() || !Path::new("/sys").exists() {
        return Err("required Linux /proc or /sys filesystem is unavailable".into());
    }
    println!(
        "{{\"ok\":true,\"engine\":\"rust\",\"version\":\"{}\",\"probe\":{}}}",
        VERSION, payload
    );
    Ok(())
}

fn daemon(args: &[String]) -> Result<(), Box<dyn Error>> {
    let status = option_value(args, "--status")
        .map(PathBuf::from)
        .ok_or("daemon requires --status PATH")?;
    let mirror = option_value(args, "--mirror").map(PathBuf::from);
    let interval = option_value(args, "--interval")
        .and_then(|v| v.parse::<u64>().ok())
        .unwrap_or(2)
        .clamp(1, 60);
    let parent_pid = parent_pid().unwrap_or(0);
    let mut previous = read_cpu_times().unwrap_or_default();

    eprintln!(
        "SBC5 Rust Core {} started: status={} interval={}s parent_pid={}",
        VERSION,
        status.display(),
        interval,
        parent_pid
    );

    loop {
        thread::sleep(Duration::from_secs(interval));
        if parent_pid > 1 && !Path::new(&format!("/proc/{parent_pid}")).exists() {
            eprintln!("SBC5 Rust Core: parent process exited; stopping native runtime.");
            return Ok(());
        }

        let current = read_cpu_times().unwrap_or_default();
        let usage = cpu_usage(&previous, &current);
        previous = current;
        match collect_status(Some(&usage)) {
            Ok(payload) => {
                if let Err(err) = atomic_write(&status, &payload) {
                    eprintln!("SBC5 Rust Core: status write failed: {err}");
                }
                if let Some(path) = mirror.as_deref() {
                    if let Err(err) = atomic_write(path, &payload) {
                        eprintln!("SBC5 Rust Core: mirror write failed: {err}");
                    }
                }
            }
            Err(err) => eprintln!("SBC5 Rust Core: telemetry probe failed: {err}"),
        }
    }
}

fn parent_pid() -> Option<u32> {
    let raw = fs::read_to_string("/proc/self/stat").ok()?;
    raw.split_whitespace().nth(3)?.parse().ok()
}

fn collect_status(cpu_usage: Option<&[f64]>) -> Result<String, Box<dyn Error>> {
    let pid = process::id();
    let epoch = SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs();
    let temp_c = read_cpu_temp().unwrap_or(0.0);
    let load = read_loadavg().unwrap_or([0.0, 0.0, 0.0]);
    let freqs = read_cpu_freqs();
    let usages = cpu_usage.unwrap_or(&[]);
    let mem = read_meminfo();
    let uptime = read_uptime().unwrap_or(0.0);
    let rpm = read_fan_rpm().unwrap_or(0);

    let mut cores = String::new();
    let count = freqs.len().max(usages.len());
    for idx in 0..count {
        if idx > 0 {
            cores.push(',');
        }
        let freq = freqs.get(idx).copied().unwrap_or(0);
        let usage = usages.get(idx).copied().unwrap_or(0.0);
        cores.push_str(&format!("{{\"cpu\":{},\"freq_mhz\":{},\"usage_percent\":{:.1}}}", idx, freq, usage));
    }

    Ok(format!(
        "{{\"schema\":{},\"engine\":\"rust\",\"version\":\"{}\",\"pid\":{},\"epoch\":{},\"temperature_c\":{:.2},\"load1\":{:.2},\"load5\":{:.2},\"load15\":{:.2},\"cores\":[{}],\"memory_total_kb\":{},\"memory_available_kb\":{},\"uptime_seconds\":{:.1},\"fan_rpm\":{}}}",
        SCHEMA,
        VERSION,
        pid,
        epoch,
        temp_c,
        load[0],
        load[1],
        load[2],
        cores,
        mem.0,
        mem.1,
        uptime,
        rpm
    ))
}

fn read_cpu_temp() -> Option<f64> {
    let raw = fs::read_to_string("/sys/class/thermal/thermal_zone0/temp").ok()?;
    raw.trim().parse::<f64>().ok().map(|v| v / 1000.0)
}

fn read_loadavg() -> Option<[f64; 3]> {
    let raw = fs::read_to_string("/proc/loadavg").ok()?;
    let mut it = raw.split_whitespace().filter_map(|v| v.parse::<f64>().ok());
    Some([it.next()?, it.next()?, it.next()?])
}

fn read_cpu_freqs() -> Vec<u64> {
    let mut out = Vec::new();
    for cpu in 0..64 {
        let path = format!("/sys/devices/system/cpu/cpu{cpu}/cpufreq/scaling_cur_freq");
        match fs::read_to_string(path) {
            Ok(raw) => out.push(raw.trim().parse::<u64>().unwrap_or(0) / 1000),
            Err(_) if cpu == 0 => continue,
            Err(_) => break,
        }
    }
    out
}

fn read_cpu_times() -> Result<Vec<CpuTimes>, Box<dyn Error>> {
    let raw = fs::read_to_string("/proc/stat")?;
    let mut out = Vec::new();
    for line in raw.lines() {
        let mut parts = line.split_whitespace();
        let Some(name) = parts.next() else { continue };
        if !name.starts_with("cpu") || name == "cpu" {
            continue;
        }
        let values: Vec<u64> = parts.filter_map(|v| v.parse::<u64>().ok()).collect();
        if values.len() < 4 {
            continue;
        }
        let total: u64 = values.iter().sum();
        let idle = values[3] + values.get(4).copied().unwrap_or(0);
        out.push(CpuTimes {
            name: name.to_string(),
            total,
            idle,
        });
    }
    Ok(out)
}

fn cpu_usage(previous: &[CpuTimes], current: &[CpuTimes]) -> Vec<f64> {
    current
        .iter()
        .map(|cur| {
            let Some(prev) = previous.iter().find(|p| p.name == cur.name) else {
                return 0.0;
            };
            let total = cur.total.saturating_sub(prev.total);
            let idle = cur.idle.saturating_sub(prev.idle);
            if total == 0 {
                0.0
            } else {
                ((total.saturating_sub(idle)) as f64 * 100.0 / total as f64).clamp(0.0, 100.0)
            }
        })
        .collect()
}

fn read_meminfo() -> (u64, u64) {
    let raw = fs::read_to_string("/proc/meminfo").unwrap_or_default();
    let mut total = 0;
    let mut avail = 0;
    for line in raw.lines() {
        if let Some(v) = line.strip_prefix("MemTotal:") {
            total = v.split_whitespace().next().and_then(|x| x.parse().ok()).unwrap_or(0);
        } else if let Some(v) = line.strip_prefix("MemAvailable:") {
            avail = v.split_whitespace().next().and_then(|x| x.parse().ok()).unwrap_or(0);
        }
    }
    (total, avail)
}

fn read_uptime() -> Option<f64> {
    fs::read_to_string("/proc/uptime")
        .ok()?
        .split_whitespace()
        .next()?
        .parse()
        .ok()
}

fn read_fan_rpm() -> Option<u64> {
    let candidates = [
        "/sys/class/hwmon/hwmon0/fan1_input",
        "/sys/class/hwmon/hwmon1/fan1_input",
        "/sys/class/hwmon/hwmon2/fan1_input",
        "/sys/class/hwmon/hwmon3/fan1_input",
    ];
    for path in candidates {
        if let Ok(raw) = fs::read_to_string(path) {
            if let Ok(value) = raw.trim().parse::<u64>() {
                return Some(value);
            }
        }
    }
    None
}

fn atomic_write(path: &Path, payload: &str) -> Result<(), Box<dyn Error>> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    let tmp = path.with_extension(format!("tmp.{}", process::id()));
    {
        let mut file = File::create(&tmp)?;
        file.write_all(payload.as_bytes())?;
        file.write_all(b"\n")?;
        file.sync_all()?;
    }
    fs::rename(tmp, path)?;
    Ok(())
}
