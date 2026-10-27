"""Manual-only bounded health worker. It is intentionally not auto-started."""
import argparse, time
import db
from domain_intelligence import tcp_probe

def run_once(delay=0.25):
    db.migrate_autobotix()
    for domain in db.get_autobotix_domains():
        if not domain.get("target_host") or not domain.get("target_port"): continue
        result = tcp_probe(domain["target_host"], domain["target_port"])
        with db.get_db() as conn:
            conn.execute("INSERT INTO ab_health_checks(domain_id,layer,status,reason,duration_ms,checked_at,source) VALUES(?,?,?,?,?,datetime('now'),'manual_worker')", (domain["id"], "tcp", result["status"], result.get("reason"), result.get("duration_ms")))
        time.sleep(delay)

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description='Run one read-only, allow-listed TCP health-check pass.')
    parser.add_argument('--delay', type=float, default=.25)
    args=parser.parse_args(); run_once(max(.1, args.delay))
