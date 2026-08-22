from pathlib import Path
import re

import yaml


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "k8s/adguard.yaml"


CANONICAL_HOSTS = {
    "adguard-setup.e-dani.com",
    "adguard.e-dani.com",
    "admin.skirmshop.es",
    "agentgateway-mcp-stg.e-dani.com",
    "agentgateway-mcp.e-dani.com",
    "alertmanager.e-dani.com",
    "argocd.e-dani.com",
    "aurora-api.e-dani.com",
    "aurora.e-dani.com",
    "bambulab.e-dani.com",
    "brain-ingest-k8s.e-dani.com",
    "brain-k8s.e-dani.com",
    "chamber.e-dani.com",
    "claude.e-dani.com",
    "code.e-dani.com",
    "dgx-synapse-mcp.e-dani.com",
    "dgx.e-dani.com",
    "firecrawl.e-dani.com",
    "grafana.e-dani.com",
    "ha-dashboard.e-dani.com",
    "harbor.e-dani.com",
    "home-assistant.e-dani.com",
    "jarvis.e-dani.com",
    "keep-api.e-dani.com",
    "keep.e-dani.com",
    "langfuse.e-dani.com",
    "libreplay.e-dani.com",
    "litellm.e-dani.com",
    "longhorn.e-dani.com",
    "mcp-socialmedia.e-dani.com",
    "minio-s3.e-dani.com",
    "minio.e-dani.com",
    "multichamber.e-dani.com",
    "openclaw-k8s-readonly.e-dani.com",
    "openclaw-k8s-webhooks.e-dani.com",
    "openclaw-k8s.e-dani.com",
    "openclaw-synapse.e-dani.com",
    "openclaw-webhooks.e-dani.com",
    "openclaw.e-dani.com",
    "paperclip.e-dani.com",
    "picqer-mcp.e-dani.com",
    "s3.e-dani.com",
    "sauvage-bot.e-dani.com",
    "skirmbooks.e-dani.com",
    "skirmshop-s3-console.e-dani.com",
    "skirmshop-s3.e-dani.com",
    "stt-mcp.e-dani.com",
    "synapse.e-dani.com",
    "teslamate.e-dani.com",
    "uriel.e-dani.com",
    "vault.e-dani.com",
    "vm.e-dani.com",
    "whatsapp-pro.e-dani.com",
    "whatsapp.e-dani.com",
}


def manifest_documents():
    return [item for item in yaml.safe_load_all(MANIFEST.read_text()) if item]


def test_seed_contains_every_canonical_host_once_at_the_lan_vip():
    seed = next(
        item
        for item in manifest_documents()
        if item.get("kind") == "ConfigMap"
        and item["metadata"]["name"] == "adguard-seed-config"
    )
    config = yaml.safe_load(seed["data"]["AdGuardHome.yaml"])
    rewrites = config["filtering"]["rewrites"]
    by_domain = {}
    for rewrite in rewrites:
        by_domain.setdefault(rewrite["domain"], []).append(rewrite)

    for host in CANONICAL_HOSTS:
        assert by_domain[host] == [
            {"domain": host, "answer": "192.168.50.240", "enabled": True}
        ]


def test_init_container_reconciles_the_same_canonical_host_set():
    text = MANIFEST.read_text()
    block = re.search(
        r"for domain in \\\n(?P<domains>.*?)\n\s*ensure_panel_rewrite \"\$domain\"",
        text,
        flags=re.DOTALL,
    )
    assert block is not None
    tokens = {
        token.rstrip(";")
        for token in block.group("domains").replace("\\", " ").split()
        if token != ";" and token != "do"
    }
    assert tokens == CANONICAL_HOSTS


def test_init_container_removes_retired_sauvage_rewrite_from_persistent_config():
    text = MANIFEST.read_text()
    assert 'remove_panel_rewrite "openclaw-sauvage.e-dani.com"' in text
    assert "test \"$(grep -Ec" in text
