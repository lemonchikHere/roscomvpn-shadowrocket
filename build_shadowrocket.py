#!/usr/bin/env python3
"""Build a Shadowrocket config from RoscomVPN routing sources.

The upstream RoscomVPN profile is Mihomo-first and points at binary MRS
rule-providers. Shadowrocket cannot consume those directly, so this script
uses the text source lists and expands them into one importable .conf file.
"""

from __future__ import annotations

import datetime as dt
import ipaddress
import re
import sys
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT_CONF = ROOT / "roscomvpn-shadowrocket.conf"
OUT_EXPANDED_CONF = ROOT / "roscomvpn-shadowrocket-expanded.conf"
OUT_PROCESS_CONF = ROOT / "roscomvpn-shadowrocket-with-process.conf"
OUT_RULES_DIR = ROOT / "rules"

GEOSITE_BASE = "https://raw.githubusercontent.com/hydraponique/roscomvpn-geosite/master/data"
GEOIP_BASE = "https://raw.githubusercontent.com/hydraponique/roscomvpn-geoip/release/text"
CUSTOM_BASE = "https://raw.githubusercontent.com/roscomvpn/custom-category/release/mihomo"
TORRENT_CLIENTS_URL = "https://raw.githubusercontent.com/legiz-ru/mihomo-rule-sets/main/other/torrent-clients.yaml"
SHADOWROCKET_DISCORD_URL = "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Discord/Discord.list"
SHADOWROCKET_INSTAGRAM_URL = "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Instagram/Instagram.list"
SHADOWROCKET_FACEBOOK_URL = "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Facebook/Facebook.list"
ROSCOMVPN_ROUTING_URL = "https://raw.githubusercontent.com/hydraponique/roscomvpn-routing/main/MIHOMO/default.yaml"

PROXY_OPTION = "force-remote-dns"
PROXY_POLICY = "Proxy"
BLOCK_POLICY = "REJECT-DROP"
QUIC_BLOCK_RULE = "AND,((PROTOCOL,UDP),(DST-PORT,443)),REJECT-NO-DROP"
FETCH_CACHE: dict[str, str] = {}
POLICIES = {"DIRECT", "PROXY", "REJECT", "REJECT-DROP", "REJECT-NO-DROP"}
REPO_RAW_BASE = "https://raw.githubusercontent.com/lemonchikHere/roscomvpn-shadowrocket/main"
POLICIES.add(PROXY_POLICY)

TELEGRAM_IP_RANGES = (
    "91.108.4.0/22",
    "91.108.8.0/22",
    "91.108.12.0/22",
    "91.108.16.0/22",
    "91.108.20.0/22",
    "91.108.56.0/22",
    "109.239.140.0/24",
    "149.154.160.0/20",
)


@dataclass(frozen=True)
class Step:
    source_type: str
    name: str
    policy: str
    url: str | None = None
    no_resolve: bool = False
    remote_options: tuple[str, ...] = ()


ORDER = [
    Step("ip", "private-ips", "DIRECT", f"{GEOIP_BASE}/private.txt", no_resolve=True),
    Step("raw", "ipv6-leak-guard", BLOCK_POLICY, no_resolve=True),
    Step("raw", "quic-udp-443", "REJECT-NO-DROP"),
    Step("geosite", "private-domains", "DIRECT", f"{GEOSITE_BASE}/private"),
    Step("geosite", "google-play", PROXY_POLICY, f"{GEOSITE_BASE}/google-play", remote_options=(PROXY_OPTION,)),
    Step("geosite", "twitch-ads", PROXY_POLICY, f"{GEOSITE_BASE}/twitch-ads", remote_options=(PROXY_OPTION,)),
    Step("shadowrocket-list", "instagram", PROXY_POLICY, SHADOWROCKET_INSTAGRAM_URL, remote_options=(PROXY_OPTION,)),
    Step("shadowrocket-list", "facebook", PROXY_POLICY, SHADOWROCKET_FACEBOOK_URL, remote_options=(PROXY_OPTION,)),
    Step("geosite", "youtube", PROXY_POLICY, f"{GEOSITE_BASE}/youtube", remote_options=(PROXY_OPTION,)),
    Step("geosite", "telegram", PROXY_POLICY, f"{GEOSITE_BASE}/telegram", remote_options=(PROXY_OPTION,)),
    Step("static", "telegram-ips", PROXY_POLICY, no_resolve=True),
    Step("geosite", "github", PROXY_POLICY, f"{GEOSITE_BASE}/github", remote_options=(PROXY_OPTION,)),
    Step("shadowrocket-list", "discord-macos-addon", PROXY_POLICY, SHADOWROCKET_DISCORD_URL, remote_options=(PROXY_OPTION,)),
    Step("geosite", "category-ads", BLOCK_POLICY, f"{GEOSITE_BASE}/category-ads"),
    Step("geosite", "win-spy", BLOCK_POLICY, f"{GEOSITE_BASE}/win-spy"),
    Step("geosite", "torrent-domains", "DIRECT", f"{GEOSITE_BASE}/torrent"),
    Step("geosite", "epicgames", "DIRECT", f"{GEOSITE_BASE}/epicgames"),
    Step("geosite", "origin", "DIRECT", f"{GEOSITE_BASE}/origin"),
    Step("geosite", "riot", "DIRECT", f"{GEOSITE_BASE}/riot"),
    Step("geosite", "escapefromtarkov", "DIRECT", f"{GEOSITE_BASE}/escapefromtarkov"),
    Step("geosite", "steam", "DIRECT", f"{GEOSITE_BASE}/steam"),
    Step("geosite", "faceit", "DIRECT", f"{GEOSITE_BASE}/faceit"),
    Step("geosite", "twitch", "DIRECT", f"{GEOSITE_BASE}/twitch"),
    Step("geosite", "microsoft", "DIRECT", f"{GEOSITE_BASE}/microsoft"),
    Step("geosite", "apple", "DIRECT", f"{GEOSITE_BASE}/apple"),
    Step("geosite", "pinterest", "DIRECT", f"{GEOSITE_BASE}/pinterest"),
    Step("geosite", "category-ru", "DIRECT", f"{GEOSITE_BASE}/category-ru"),
    Step("geosite", "whitelist", "DIRECT", f"{GEOSITE_BASE}/whitelist"),
    Step("classical", "torrent-clients", "DIRECT", TORRENT_CLIENTS_URL),
    Step("classical", "games", "DIRECT", f"{CUSTOM_BASE}/games.yaml"),
    Step("classical", "ru-apps", "DIRECT", f"{CUSTOM_BASE}/ru-apps.yaml"),
    Step("ip", "direct-ips", "DIRECT", f"{GEOIP_BASE}/direct.txt"),
]

GENERAL = """[General]
bypass-system = true
skip-proxy = 127.0.0.1,localhost,*.local,10.0.0.0/8,100.64.0.0/10,172.16.0.0/12,192.168.0.0/16
bypass-tun = 10.0.0.0/8,100.64.0.0/10,127.0.0.0/8,169.254.0.0/16,172.16.0.0/12,192.0.0.0/24,192.0.2.0/24,192.88.99.0/24,192.168.0.0/16,198.18.0.0/15,198.51.100.0/24,203.0.113.0/24,224.0.0.0/3
dns-server = system,77.88.8.8,1.1.1.1,8.8.8.8
fallback-dns-server = system,1.1.1.1,8.8.8.8
ipv6 = false
prefer-ipv6 = false
private-ip-answer = true
dns-direct-fallback-proxy = true

"""


def fetch(url: str) -> str:
    if url in FETCH_CACHE:
        return FETCH_CACHE[url]
    request = urllib.request.Request(url, headers={"User-Agent": "codex-shadowrocket-builder"})
    last_error: Exception | None = None
    for attempt in range(1, 5):
        try:
            print(f"fetch {attempt}/4 {url}", file=sys.stderr)
            with urllib.request.urlopen(request, timeout=75) as response:
                text = response.read().decode("utf-8")
                FETCH_CACHE[url] = text
                return text
        except Exception as exc:
            last_error = exc
            time.sleep(min(attempt * 2, 8))
    raise RuntimeError(f"could not fetch {url}: {last_error}")


def strip_comment(line: str) -> str:
    line = line.strip()
    if not line or line.startswith("#"):
        return ""
    return re.sub(r"\s+#.*$", "", line).strip()


def with_policy(rule: str, policy: str) -> str:
    parts = [part.strip() for part in rule.split(",")]
    if len(parts) < 2:
        raise ValueError(f"Cannot attach policy to malformed rule: {rule}")
    return ",".join(parts[:2] + [policy] + parts[2:])


def attach_shadowrocket_options(rule: str, policy: str) -> str:
    if policy != PROXY_POLICY:
        return rule
    rule_type = rule.split(",", 1)[0]
    if rule_type in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "DOMAIN-WILDCARD"}:
        return f"{rule},{PROXY_OPTION}"
    return rule


def dedupe(lines: list[str], seen: set[str]) -> list[str]:
    out = []
    for line in lines:
        if line in seen:
            continue
        seen.add(line)
        out.append(line)
    return out


def parse_geosite(text: str, policy: str, skipped: list[str]) -> list[str]:
    rules = []
    for raw in text.splitlines():
        line = strip_comment(raw)
        if not line:
            continue
        if line.startswith("domain:"):
            rule = f"DOMAIN-SUFFIX,{line.split(':', 1)[1].strip()},{policy}"
        elif line.startswith("full:"):
            rule = f"DOMAIN,{line.split(':', 1)[1].strip()},{policy}"
        elif line.startswith("keyword:"):
            rule = f"DOMAIN-KEYWORD,{line.split(':', 1)[1].strip()},{policy}"
        elif line.startswith("regexp:"):
            skipped.append(line)
            continue
        else:
            rule = f"DOMAIN-SUFFIX,{line},{policy}"
        rules.append(attach_shadowrocket_options(rule, policy))
    return rules


def parse_ip(text: str, policy: str) -> list[str]:
    rules = []
    for raw in text.splitlines():
        line = strip_comment(raw)
        if not line:
            continue
        ipaddress.ip_network(line, strict=False)
        rules.append(f"IP-CIDR,{line},{policy}")
    return rules


def parse_classical(text: str, policy: str, include_process: bool) -> list[str]:
    rules = []
    for raw in text.splitlines():
        line = strip_comment(raw)
        if not line or line == "payload:":
            continue
        if line.startswith("- "):
            line = line[2:].strip()
        if not line or "," not in line:
            continue
        rule_type = line.split(",", 1)[0]
        if rule_type.startswith("PROCESS-") and not include_process:
            continue
        rules.append(attach_shadowrocket_options(with_policy(line, policy), policy))
    return rules


def parse_shadowrocket_list(text: str, policy: str) -> list[str]:
    rules = []
    for raw in text.splitlines():
        line = strip_comment(raw)
        if not line or "," not in line:
            continue
        rules.append(attach_shadowrocket_options(with_policy(line, policy), policy))
    return rules


def rules_for_step(step: Step, include_process: bool, skipped: list[str]) -> list[str]:
    if step.name == "ipv6-leak-guard":
        return [f"IP-CIDR,::/0,{BLOCK_POLICY},no-resolve"]
    if step.name == "quic-udp-443":
        return [QUIC_BLOCK_RULE]
    if step.name == "telegram-ips":
        rules = [f"IP-CIDR,{cidr},{step.policy}" for cidr in TELEGRAM_IP_RANGES]
        if step.no_resolve:
            return [f"{rule},no-resolve" for rule in rules]
        return rules
    if not step.url:
        raise ValueError(f"Step {step.name} has no URL")
    text = fetch(step.url)
    if step.source_type == "geosite":
        return parse_geosite(text, step.policy, skipped)
    if step.source_type == "ip":
        rules = parse_ip(text, step.policy)
        if step.no_resolve:
            return [f"{rule},no-resolve" for rule in rules]
        return rules
    if step.source_type == "classical":
        return parse_classical(text, step.policy, include_process)
    if step.source_type == "shadowrocket-list":
        return parse_shadowrocket_list(text, step.policy)
    raise ValueError(f"Unknown step type: {step.source_type}")


def build_config(include_process: bool) -> tuple[str, dict[str, int | str | list[str]]]:
    generated = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    skipped: list[str] = []
    seen: set[str] = set()
    lines = [
        "# RoscomVPN routing for Shadowrocket",
        "# Generated from live upstream text sources by build_shadowrocket.py",
        f"# Source profile: {ROSCOMVPN_ROUTING_URL}",
        "# Notes: generated from text sources because Shadowrocket does not import Mihomo .mrs providers directly.",
        "# Default behavior: RU/BY and known local services go DIRECT; YouTube/Telegram/GitHub/Discord go PROXY; ads/telemetry are blocked; everything else goes PROXY.",
        "",
        GENERAL.rstrip(),
        "",
        "[Rule]",
    ]

    counts: dict[str, int | str | list[str]] = {
        "generated": generated,
        "rules": 0,
        "skipped_regex": [],
        "process_rules": "included" if include_process else "omitted",
    }

    for step in ORDER:
        rules = dedupe(rules_for_step(step, include_process, skipped), seen)
        if not rules:
            continue
        lines.append("")
        lines.append(f"# {step.name} -> {step.policy}")
        lines.extend(rules)
        counts["rules"] = int(counts["rules"]) + len(rules)

    lines.append("")
    lines.append("# fallback")
    lines.append(f"FINAL,{PROXY_POLICY}")
    counts["rules"] = int(counts["rules"]) + 1
    counts["skipped_regex"] = skipped
    return "\n".join(lines) + "\n", counts


def build_ruleset_config() -> str:
    lines = [
        "# RoscomVPN routing for Shadowrocket",
        "# Lightweight RULE-SET profile generated by build_shadowrocket.py",
        f"# Source profile: {ROSCOMVPN_ROUTING_URL}",
        "# Import this URL in Shadowrocket:",
        f"# {REPO_RAW_BASE}/roscomvpn-shadowrocket.conf",
        "",
        GENERAL.rstrip(),
        "",
        "[Rule]",
    ]

    for step in ORDER:
        if step.name == "ipv6-leak-guard":
            lines.append("")
            lines.append("# ipv6-leak-guard -> REJECT-DROP")
            lines.append(f"IP-CIDR,::/0,{BLOCK_POLICY},no-resolve")
            continue
        if step.name == "quic-udp-443":
            lines.append("")
            lines.append("# quic-udp-443 -> REJECT-NO-DROP")
            lines.append(QUIC_BLOCK_RULE)
            continue

        options = ",".join(step.remote_options)
        suffix = f",{options}" if options else ""
        lines.append("")
        lines.append(f"# {step.name} -> {step.policy}")
        lines.append(f"RULE-SET,{REPO_RAW_BASE}/rules/{step.name}.list,{step.policy}{suffix}")

    lines.append("")
    lines.append("# fallback")
    lines.append(f"FINAL,{PROXY_POLICY}")
    return "\n".join(lines) + "\n"


def write_rule_files() -> int:
    OUT_RULES_DIR.mkdir(exist_ok=True)
    total = 0
    for step in ORDER:
        if step.source_type == "raw":
            continue
        skipped: list[str] = []
        rules = rules_for_step(step, include_process=True, skipped=skipped)
        rule_set = []
        for rule in rules:
            parts = rule.split(",")
            if len(parts) >= 3 and parts[2] in POLICIES:
                options = [part for part in parts[3:] if part != PROXY_OPTION]
                rule_set.append(",".join(parts[:2] + options))
            else:
                rule_set.append(rule)
        output = OUT_RULES_DIR / f"{step.name}.list"
        output.write_text("\n".join(rule_set) + "\n", encoding="utf-8")
        total += len(rule_set)
    return total


def main() -> int:
    try:
        ruleset_config = build_ruleset_config()
        expanded_config, counts = build_config(include_process=False)
        process_config, process_counts = build_config(include_process=True)
        OUT_CONF.write_text(ruleset_config, encoding="utf-8")
        OUT_EXPANDED_CONF.write_text(expanded_config, encoding="utf-8")
        OUT_PROCESS_CONF.write_text(process_config, encoding="utf-8")
        rule_file_count = write_rule_files()
    except Exception as exc:
        print(f"build failed: {exc}", file=sys.stderr)
        return 1

    print(f"wrote {OUT_CONF} (lightweight RULE-SET profile)")
    print(f"wrote {OUT_EXPANDED_CONF} ({counts['rules']} rules, process rules {counts['process_rules']})")
    print(f"wrote {OUT_PROCESS_CONF} ({process_counts['rules']} rules, process rules {process_counts['process_rules']})")
    print(f"wrote {OUT_RULES_DIR} ({rule_file_count} rule-file entries)")
    skipped = counts["skipped_regex"]
    if skipped:
        print(f"skipped {len(skipped)} geosite regexp entries unsupported by conservative Shadowrocket conversion")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
