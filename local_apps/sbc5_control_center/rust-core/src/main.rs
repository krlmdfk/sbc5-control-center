use std::env;
use std::error::Error;
use std::fs::{self, File};
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::process;
use std::thread;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

const VERSION: &str = "3.0.0";
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
            Err(err) => eprintln!("SBC5 Rust Core: telemetry collection failed: {err}"),
        }
    }
}

fn collect_status(cpu_usage: Option<&[f64]>) -> Result<String, Box<dyn Error>> {
    let now = SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs();
    let temperature = cpu_temperature_c();
    let frequencies = cpu_frequencies_mhz();
    let average_frequency = if frequencies.is_empty() {
        None
    } else {
        Some(frequencies.iter().sum::<f64>() / frequencies.len() as f64)
    };
    let load = load_1m();
    let uptime = uptime_seconds();
    let (mem_total, mem_available) = memory_kib();
    let fan = fan_rpm();
    let parent = parent_pid().unwrap_or(0);
    let usage = cpu_usage.unwrap_or(&[]);

    Ok(format!(
        concat!(
            "{{",
            "\"schema\":{},",
            "\"engine\":\"rust\",",
            "\"version\":\"{}\",",
            "\"pid\":{},",
            "\"parent_pid\":{},",
            "\"updated_epoch\":{},",
            "\"cpu_temperature_c\":{},",
            "\"load_1m\":{},",
            "\"cpu_frequency_mhz\":{},",
            "\"cpu_core_frequency_mhz\":{},",
            "\"cpu_core_usage_percent\":{},",
            "\"memory_total_kib\":{},",
            "\"memory_available_kib\":{},",
            "\"uptime_seconds\":{},",
            "\"fan_rpm\":{}",
            "}}"
        ),
        SCHEMA,
        VERSION,
        process::id(),
        parent,
        now,
        json_opt_f64(temperature, 2),
        json_opt_f64(load, 2),
        json_opt_f64(average_frequency, 1),
        json_array_f64(&frequencies, 1),
        json_array_f64(usage, 1),
        json_opt_u64(mem_total),
        json_opt_u64(mem_available),
        json_opt_f64(uptime, 1),
        json_opt_u64(fan),
    ))
}

fn atomic_write(path: &Path, payload: &str) -> Result<(), Box<dyn Error>> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    let file_name = path
        .file_name()
        .and_then(|v| v.to_str())
        .unwrap_or("sbc5-core.json");
    let temp = path.with_file_name(format!(".{file_name}.tmp.{}", process::id()));
    {
        let mut file = File::create(&temp)?;
        file.write_all(payload.as_bytes())?;
        file.write_all(b"\n")?;
        file.sync_data()?;
    }
    fs::rename(&temp, path)?;
    Ok(())
}

fn read_text(path: &str) -> Option<String> {
    let mut content = String::new();
    File::open(path).ok()?.read_to_string(&mut content).ok()?;
    Some(content)
}

fn read_number(path: &str) -> Option<f64> {
    read_text(path)?.trim().parse::<f64>().ok()
}

fn cpu_temperature_c() -> Option<f64> {
    let candidates = [
        "/sys/class/thermal/thermal_zone0/temp",
        "/sys/devices/virtual/thermal/thermal_zone0/temp",
    ];
    for path in candidates {
        if let Some(raw) = read_number(path) {
            let value = if raw > 500.0 { raw / 1000.0 } else { raw };
            if (-40.0..=150.0).contains(&value) {
                return Some(value);
            }
        }
    }
    None
}

fn cpu_frequencies_mhz() -> Vec<f64> {
    let mut result = Vec::new();
    for cpu in 0..32 {
        let base = format!("/sys/devices/system/cpu/cpu{cpu}/cpufreq");
        let scaling = format!("{base}/scaling_cur_freq");
        let cpuinfo = format!("{base}/cpuinfo_cur_freq");
        let raw = read_number(&scaling).or_else(|| read_number(&cpuinfo));
        match raw {
            Some(value) => result.push(if value > 10_000.0 { value / 1000.0 } else { value }),
            None if cpu < 4 => result.push(0.0),
            None => break,
        }
    }
    while result.last().is_some_and(|v| *v <= 0.0) {
        result.pop();
    }
    result
}

fn load_1m() -> Option<f64> {
    read_text("/proc/loadavg")?
        .split_whitespace()
        .next()?
        .parse::<f64>()
        .ok()
}

fn uptime_seconds() -> Option<f64> {
    read_text("/proc/uptime")?
        .split_whitespace()
        .next()?
        .parse::<f64>()
        .ok()
}

fn memory_kib() -> (Option<u64>, Option<u64>) {
    let Some(text) = read_text("/proc/meminfo") else {
        return (None, None);
    };
    let mut total = None;
    let mut available = None;
    for line in text.lines() {
        let mut parts = line.split_whitespace();
        match parts.next() {
            Some("MemTotal:") => total = parts.next().and_then(|v| v.parse::<u64>().ok()),
            Some("MemAvailable:") => available = parts.next().and_then(|v| v.parse::<u64>().ok()),
            _ => {}
        }
    }
    (total, available)
}

fn fan_rpm() -> Option<u64> {
    let root = Path::new("/sys/class/hwmon");
    let entries = fs::read_dir(root).ok()?;
    for entry in entries.flatten() {
        let path = entry.path();
        let Ok(files) = fs::read_dir(path) else { continue };
        for file in files.flatten() {
            let name = file.file_name();
            let name = name.to_string_lossy();
            if name.starts_with("fan") && name.ends_with("_input") {
                if let Ok(value) = fs::read_to_string(file.path()) {
                    if let Ok(rpm) = value.trim().parse::<u64>() {
                        if rpm > 0 {
                            return Some(rpm);
                        }
                    }
                }
            }
        }
    }
    None
}

fn read_cpu_times() -> Option<Vec<CpuTimes>> {
    let text = read_text("/proc/stat")?;
    let mut result = Vec::new();
    for line in text.lines() {
        let mut parts = line.split_whitespace();
        let Some(name) = parts.next() else { continue };
        if !name.starts_with("cpu") || name == "cpu" {
            continue;
        }
        let values: Vec<u64> = parts.filter_map(|v| v.parse::<u64>().ok()).collect();
        if values.len() < 4 {
            continue;
        }
        let total = values.iter().sum::<u64>();
        let idle = values.get(3).copied().unwrap_or(0) + values.get(4).copied().unwrap_or(0);
        result.push(CpuTimes {
            name: name.to_string(),
            total,
            idle,
        });
    }
    Some(result)
}

fn cpu_usage(previous: &[CpuTimes], current: &[CpuTimes]) -> Vec<f64> {
    let mut result = Vec::new();
    for now in current {
        let Some(before) = previous.iter().find(|item| item.name == now.name) else {
            result.push(0.0);
            continue;
        };
        let total = now.total.saturating_sub(before.total);
        let idle = now.idle.saturating_sub(before.idle);
        if total == 0 {
            result.push(0.0);
        } else {
            let busy = total.saturating_sub(idle);
            result.push((busy as f64 / total as f64 * 100.0).clamp(0.0, 100.0));
        }
    }
    result
}

fn parent_pid() -> Option<u32> {
    let stat = read_text("/proc/self/stat")?;
    let end = stat.rfind(')')?;
    let tail = stat.get(end + 1..)?.trim();
    let mut fields = tail.split_whitespace();
    fields.next()?; // process state
    fields.next()?.parse::<u32>().ok()
}

fn json_opt_f64(value: Option<f64>, decimals: usize) -> String {
    match value {
        Some(v) if v.is_finite() => format!("{v:.decimals$}"),
        _ => "null".to_string(),
    }
}

fn json_opt_u64(value: Option<u64>) -> String {
    value.map(|v| v.to_string()).unwrap_or_else(|| "null".to_string())
}

fn json_array_f64(values: &[f64], decimals: usize) -> String {
    let body = values
        .iter()
        .map(|v| {
            if v.is_finite() {
                format!("{v:.decimals$}")
            } else {
                "null".to_string()
            }
        })
        .collect::<Vec<_>>()
        .join(",");
    format!("[{body}]")
}
