"""Read-only inventory import and bounded health utilities for AutoBotix."""
import csv, json, re, socket, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
import db

ROOT = Path(__file__).resolve().parent
SNAPSHOT = ROOT / "audit-reports" / "cloudflare-2026-10-24"
SECRET_RE = re.compile(r"(?i)(token|password|secret|credentials?)[=:]\S+")
HEALTH_404_DOMAINS = {"wss.warnet.web.id", "wss-sharescreen.jualin.site", "api.warnet.web.id", "wizard.jualin.site"}

def sanitize(value):
    return SECRET_RE.sub(r"\1=[REDACTED]", value or "")

def import_historical_snapshot():
    db.migrate_autobotix()
    inventory = json.loads((SNAPSHOT / "cloudflare-tunnel-inventory.json").read_text())
    observed = inventory["audit_metadata"].get("observed_at") or "unknown"
    with db.get_db() as conn:
        for tunnel in inventory.get("tunnels", []):
            conn.execute("""INSERT INTO ab_tunnels(name,uuid,status,status_source,config_file,observed_at,evidence)
              VALUES(?,?,?,?,?,?,?) ON CONFLICT(name) DO UPDATE SET uuid=excluded.uuid,status=excluded.status,status_source=excluded.status_source,config_file=excluded.config_file,observed_at=excluded.observed_at,evidence=excluded.evidence""", (tunnel["name"], tunnel.get("uuid"), tunnel.get("status"), "historical_snapshot", tunnel.get("config"), observed, sanitize(tunnel.get("evidence"))))
        for service in inventory.get("services", []):
            conn.execute("""INSERT INTO ab_services(name,port,project_path,status,observed_at,source,evidence)
              VALUES(?,?,?,?,?,?,?) ON CONFLICT(name) DO UPDATE SET port=excluded.port,project_path=excluded.project_path,status=excluded.status,observed_at=excluded.observed_at,source=excluded.source,evidence=excluded.evidence""",
              (service["name"], service.get("port"), service.get("project"), service.get("status"), observed, "historical_snapshot", "Historical audit inventory"))
        with (SNAPSHOT / "domain-service-mapping.csv").open(newline="") as handle:
            for row in csv.DictReader(handle):
                upstream = "responding_health_unverified" if row["domain"] in HEALTH_404_DOMAINS else row["health_status"]
                conn.execute("""INSERT INTO ab_domains(hostname,tunnel_name,tunnel_uuid,config_file,ingress_rule,target_url,target_host,target_port,proxy_type,service_name,container_name,project_path,framework,upstream_status,public_https_status,public_https_reason,project_mapping_status,evidence,confidence,observed_at,source)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(hostname) DO UPDATE SET tunnel_name=excluded.tunnel_name,tunnel_uuid=excluded.tunnel_uuid,config_file=excluded.config_file,ingress_rule=excluded.ingress_rule,target_url=excluded.target_url,target_host=excluded.target_host,target_port=excluded.target_port,proxy_type=excluded.proxy_type,service_name=excluded.service_name,container_name=excluded.container_name,project_path=excluded.project_path,framework=excluded.framework,upstream_status=excluded.upstream_status,observed_at=excluded.observed_at,evidence=excluded.evidence,confidence=excluded.confidence,source=excluded.source""", (row["domain"],row["tunnel_name"],row["tunnel_uuid"],row["config_file"],row["ingress_rule"],row["target_url"],row["target_host"],row["target_port"] or None,row["proxy_type"],row["service_name"],row["container_name"],row["project_path"],row["framework"],upstream,"unknown","Historical public HTTPS probe returned 000: no valid HTTP response; failure reason unavailable.","mapped" if row["project_path"] else "unresolved",sanitize("historical CSV mapping"),row["mapping_confidence"],row["last_checked"] or observed,"historical_snapshot"))
                domain_id = conn.execute("SELECT id FROM ab_domains WHERE hostname=?", (row["domain"],)).fetchone()[0]
                conn.execute("DELETE FROM ab_health_checks WHERE domain_id=? AND source='historical_snapshot'", (domain_id,))
                if row["domain"] in HEALTH_404_DOMAINS: state, code, reason = "unknown", 404, "Historical /health probe returned 404; backend response does not establish an application health endpoint."
                elif upstream == "healthy": state, code, reason = "healthy", 200, "Historical local upstream probe returned 200."
                elif upstream == "unreachable": state, code, reason = "unreachable", None, "Historical target listener/connectivity probe failed."
                else: state, code, reason = "unknown", None, "Historical result is not a verified application health endpoint."
                conn.execute("INSERT INTO ab_health_checks(domain_id,layer,status,http_status,reason,checked_at,source) VALUES(?,?,?,?,?,?,?)", (domain_id,"local_upstream",state,code,reason,row["last_checked"] or observed,"historical_snapshot"))
    return observed

def allowed_target(host, port):
    return host == "127.0.0.1" and int(port) in {80,3001,5000,5173,8000,8001,8080,8088,8099,20128,49374}

def tcp_probe(host, port, timeout=2):
    if not allowed_target(host, port): return {"status":"blocked", "reason":"Target is outside the verified allow-list."}
    started=time.monotonic()
    try:
        with socket.create_connection((host, int(port)), timeout=timeout): pass
        return {"status":"reachable","duration_ms":round((time.monotonic()-started)*1000,1)}
    except OSError as exc: return {"status":"unreachable","reason":str(exc)[:160],"duration_ms":round((time.monotonic()-started)*1000,1)}
